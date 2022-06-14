import os
import re
import string
import warnings

from types import SimpleNamespace
from typing import Dict, Any, Union, Dict, Optional


class EnvironmentVariables:
    def __init__(self, envs: Dict):
        self._env_keys_added: Dict = envs

    def __enter__(self):
        for key, val in self._env_keys_added.items():
            os.environ[key] = str(val)

    def __exit__(self, *args, **kwargs):
        for key in self._env_keys_added.keys():
            os.unsetenv(key)


# Code below was directly ported over from JAML class (jaml/__init__.py) in jina.
# We need to utiltiy of expand_dict during the normalization process.

context_regex_str = r'\${{\s[a-zA-Z0-9_]*\s}}'
context_var_regex = re.compile(
    context_regex_str
)  # matches expressions of form '${{ var }}'

context_dot_regex_str = (
    r'\${{\sCONTEXT\.[a-zA-Z0-9_]*\s}}|\${{\scontext\.[a-zA-Z0-9_]*\s}}'
)
context_dot_regex = re.compile(
    context_dot_regex_str
)  # matches expressions of form '${{ ENV.var }}' or '${{ env.var }}'

new_env_regex_str = r'\${{\sENV\.[a-zA-Z0-9_]*\s}}|\${{\senv\.[a-zA-Z0-9_]*\s}}'
new_env_var_regex = re.compile(
    new_env_regex_str
)  # matches expressions of form '${{ ENV.var }}' or '${{ env.var }}'

env_var_deprecated_regex_str = r'\$[a-zA-Z0-9_]*'
env_var_deprecated_regex = re.compile(
    r'\$[a-zA-Z0-9_]*'
)  # matches expressions of form '$var'

env_var_regex_str = env_var_deprecated_regex_str + '|' + new_env_regex_str
env_var_regex = re.compile(env_var_regex_str)  # matches either of the above

yaml_ref_regex = re.compile(
    r'\${{([\w\[\].]+)}}'
)  # matches expressions of form '${{root.name[0].var}}'


def parse_arg(v: str) -> Optional[Union[bool, int, str, list, float]]:
    """
    Parse the arguments from string to `Union[bool, int, str, list, float]`.
    :param v: The string of arguments
    :return: The parsed arguments list.
    """
    m = re.match(r'^[\'"](.*)[\'"]$', v)
    if m:
        return m.group(1)

    if v.startswith('[') and v.endswith(']'):
        # function args must be immutable tuples not list
        tmp = v.replace('[', '').replace(']', '').strip().split(',')
        if len(tmp) > 0:
            return [parse_arg(vv.strip()) for vv in tmp]
        else:
            return []
    try:
        v = int(v)  # parse int parameter
    except ValueError:
        try:
            v = float(v)  # parse float parameter
        except ValueError:
            if len(v) == 0:
                # ignore it when the parameter is empty
                v = None
            elif v.lower() == 'true':  # parse boolean parameter
                v = True
            elif v.lower() == 'false':
                v = False
    return v


class ContextVarTemplate(string.Template):
    delimiter = '$$'  # variables that should be substituted with values from the context are internally denoted with '$$'


def expand_dict(
    d: Dict,
    context: Optional[Union[Dict, SimpleNamespace]] = None,
    resolve_cycle_ref=True,
    resolve_passes: int = 3,
) -> Dict[str, Any]:
    """
    Expand variables from YAML file.
    :param d: yaml file loaded as python dict
    :param context: context replacement variables in a dict, the value of the dict is the replacement.
    :param resolve_cycle_ref: resolve internal reference if True.
    :param resolve_passes: number of rounds to resolve internal reference.
    :return: expanded dict.
    """

    expand_map = SimpleNamespace()
    env_map = SimpleNamespace()

    def _scan(sub_d, p):
        if isinstance(sub_d, dict):
            for k, v in sub_d.items():
                if isinstance(v, dict):
                    p.__dict__[k] = SimpleNamespace()
                    _scan(v, p.__dict__[k])
                elif isinstance(v, list):
                    p.__dict__[k] = list()
                    _scan(v, p.__dict__[k])
                else:
                    p.__dict__[k] = v
        elif isinstance(sub_d, list):
            for idx, v in enumerate(sub_d):
                if isinstance(v, dict):
                    p.append(SimpleNamespace())
                    _scan(v, p[idx])
                elif isinstance(v, list):
                    p.append(list())
                    _scan(v, p[idx])
                else:
                    p.append(v)

    def _replace(sub_d, p, resolve_ref=False):

        if isinstance(sub_d, dict):
            for k, v in sub_d.items():
                if isinstance(v, (dict, list)):
                    _replace(v, p.__dict__[k], resolve_ref)
                else:
                    if isinstance(v, str):
                        if resolve_ref and yaml_ref_regex.findall(v):
                            sub_d[k] = _resolve_yaml_reference(v, p)
                        else:
                            sub_d[k] = _sub(v)
        elif isinstance(sub_d, list):
            for idx, v in enumerate(sub_d):
                if isinstance(v, (dict, list)):
                    _replace(v, p[idx], resolve_ref)
                else:
                    if isinstance(v, str):
                        if resolve_ref and yaml_ref_regex.findall(v):
                            sub_d[idx] = _resolve_yaml_reference(v, p)
                        else:
                            sub_d[idx] = _sub(v)

    def _var_to_substitutable(v, exp=context_var_regex):
        def repl_fn(matchobj):
            return '$$' + matchobj.group(0)[4:-3]

        return re.sub(exp, repl_fn, v)

    def _to_env_var_synatx(v):
        v = _var_to_substitutable(v, new_env_var_regex)

        def repl_fn(matchobj):
            match_str = matchobj.group(0)
            match_str = match_str.replace('ENV.', '')
            match_str = match_str.replace('env.', '')
            return match_str[1:]

        return re.sub(r'\$\$[a-zA-Z0-9_.]*', repl_fn, v)

    def _to_normal_context_var(v):
        def repl_fn(matchobj):
            match_str = matchobj.group(0)
            match_str = match_str.replace('CONTEXT.', '')
            match_str = match_str.replace('context.', '')
            return match_str

        return re.sub(context_dot_regex, repl_fn, v)

    def _sub(v):

        # substitute template with actual value either from context or env variable
        # v could contain template of the form
        #
        # 1)    ${{ var }},${{ context.var }},${{ CONTEXT.var }} when need to be parsed with the context dict
        # or
        # 2 )   ${{ ENV.var }},${{ env.var }},$var ( deprecated) when need to be parsed with env
        #
        #
        # internally env var (1) and context var (2) are treated differently, both of them are cast to a unique and
        # normalize template format and then are parsed
        # 1) context variables placeholder are cast to $$var then we use the ContextVarTemplate to parse the context
        # variables
        # 2) env variables placeholder are cast to $var then we leverage the os.path.expandvars to replace by
        # environment variables.

        if env_var_deprecated_regex.findall(v) and not env_var_regex.findall(
            v
        ):  # catch expressions of form '$var'
            warnings.warn(
                'Specifying environment variables via the syntax `$var` is deprecated.'
                'Use `${{ ENV.var }}` instead.',
                category=DeprecationWarning,
            )
        if new_env_var_regex.findall(v):  # handle expressions of form '${{ ENV.var}}',
            v = _to_env_var_synatx(v)
        if context_dot_regex.findall(v):
            v = _to_normal_context_var(v)
        if context_var_regex.findall(v):  # handle expressions of form '${{ var }}'
            v = _var_to_substitutable(v)
            if context:
                v = ContextVarTemplate(v).safe_substitute(
                    context
                )  # use vars provided in context
        v = os.path.expandvars(
            v
        )  # gets env var and parses to python objects if neededd
        return parse_arg(v)

    def _resolve_yaml_reference(v, p):

        org_v = v
        # internal references are of the form ${{path}} where path is a yaml path like root.executors[0].name

        def repl_fn(matchobj):
            match_str = matchobj.group(0)
            match_str_origin = match_str

            match_str = re.sub(
                yaml_ref_regex, '{\\1}', match_str
            )  # from ${{var}} to {var} to leverage python formatter

            try:
                # "root" context is now the global namespace
                # "this" context is now the current node namespace
                match_str = match_str.format(root=expand_map, this=p, ENV=env_map)
            except AttributeError as ex:
                raise AttributeError(
                    'variable replacement is failed, please check your YAML file.'
                ) from ex
            except KeyError:
                return match_str_origin

            return match_str

        v = re.sub(yaml_ref_regex, repl_fn, v)

        return parse_arg(v)

    _scan(d, expand_map)
    _scan(dict(os.environ), env_map)

    # first do var replacement
    _replace(d, expand_map)

    # do `resolve_passes` rounds of scan-replace to resolve internal references
    for _ in range(resolve_passes):
        # rebuild expand_map
        expand_map = SimpleNamespace()
        _scan(d, expand_map)

        # resolve internal reference
        if resolve_cycle_ref:
            _replace(d, expand_map, resolve_ref=True)

    return d
