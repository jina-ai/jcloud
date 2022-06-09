<p align="center">
<br>
<br>
<br>
<img src="https://github.com/jina-ai/jcloud/blob/main/.github/README-img/logo.svg?raw=true" alt="JCloud logo: the command line interface that simplifies deploying and managing Jina projects on Jina Cloud" width="80px">
<br>
<br>
<br>
<b>Simplify deploying and managing Jina projects on Jina Cloud</b>
</p>

<p align=center>
<a href="https://pypi.org/project/jcloud/"><img alt="PyPI" src="https://img.shields.io/pypi/v/jcloud?label=PyPI&logo=pypi&logoColor=white&style=flat-square"></a>
<a href="https://slack.jina.ai"><img src="https://img.shields.io/badge/Slack-2.8k-blueviolet?logo=slack&amp;logoColor=white&style=flat-square"></a>
</p>

☁️ **To the cloud!** - Smoothly deploy a local project as a cloud service. Radically easy, no nasty surprises.

🎯 **Cut to the chase** - One CLI with five commands to manage the lifecycle of your Jina projects.

🎟️ **Early free access** - Sneak peek at our stealthy cloud hosting platform. Built on latest cloud-native tech stack, we now host your Jina project and offer computational and storage resources, for free!

## Install

```bash
pip install jcloud
jc -h
```

In case `jc` is already occupied by another tool, please use `jcloud` instead. If your pip install doesn't register bash commands for you, you can run `python -m jcloud -h`.

## Get Started

### Login

```bash
jc login
```

You can use a Google/GitHub account to register and login. Without logging in, you can't do anything.

### Deploy a Jina Project

In Jina's idiom, a project is a [Flow](https://docs.jina.ai/fundamentals/flow/), which represents an end-to-end task such as indexing, searching or recommending. In this README, we will use "project" and "Flow" interchangeably.

A Flow can have two types of file structure:

#### A single YAML file

A self-contained YAML file, consisting of all configs at the [Flow](https://docs.jina.ai/fundamentals/flow/)-level and [Executor](https://docs.jina.ai/fundamentals/executor/)-level.

> All Executors' `uses` must follow the format `jinahub+docker://MyExecutor` (from [Jina Hub](https://hub.jina.ai)) to avoid any local file dependencies.

e.g.-

```yaml
# flow.yml
jtype: Flow
executors:
  - name: sentencizer
    uses: jinahub+docker://Sentencizer
```

To deploy,

```bash
jc deploy flow.yml
```

#### Local projects

Just like a regular Python project, you can have sub-folders of Executor implementations; and a `flow.yml` on the top-level to connect all Executors together.

You can create an example local project using `jc new`. The default structure looks like:

```
.
├── .env
├── executor1
│   ├── config.yml
│   ├── executor.py
│   └── requirements.txt
└── flow.yml
```

where,

- `executor1` directory has all Executor related code/config. You can read the best practices for [file structures](https://docs.jina.ai/fundamentals/executor/repository-structure/). Multiple such Executor directories can be created.
- `flow.yml` Your Flow YAML.
- `.env` All environment variables used during deployment.

To deploy,

```bash
jc deploy ./hello
```

---

The Flow is successfully deployed when you see:

<p align="center">
<img src=".github/README-img/deploy.png" width="50%">
</p>

You will get a Flow ID, say `173503c192`. This ID is required to manage, view logs and remove the Flow.

As this Flow is deployed with default gRPC gateway (feel free to change it to `http` or `websocket`), you can use `jina.Client` to access it:

```python
from jina import Client, Document

c = Client(host='https://173503c192.wolf.jina.ai')
print(c.post('/', Document(text='hello')))
```

#### Environment variables

##### Local project

- You can include your environment variables in the `.env` file in the local project and JCloud will take care of managing them.
- You can optionally pass a `custom.env`.
  ```bash
  jc deploy ./hello --env-file ./hello/custom.env
  ```

##### Local yaml

```bash
jc deploy flow.yml --env-file flow.env
```

### View logs

To watch the logs in realtime:

```bash
jc logs 173503c192
```

You can also stream logs for a particular Executor by passing its name:

```bash
jc logs 173503c192 --executor sentencizer
```

### Remove Flow(s)

You can either remove a single Flow, multiple selected Flows or even all Flows by passing different kind of identifiers.

To remove a single Flow:

```bash
jc remove 173503c192
```

To remove multiple selected Flows:

```bash
jc remove 173503c192 887f6313e5 ddb8a2c4ef
```

To remove all Flows:

```bash
jc remove all
```

By default, removing multiple selected / all Flows would be in interactive mode where confirmation will be sent prior to
the deletion, to make it non-interactive to better suit your use case, set below environment variable before running the command:

```bash
export JCLOUD_NO_INTERACTIVE=1
```

### Get the status of a Flow

```bash
jc status 173503c192
```

<p align="center">
<img src=".github/README-img/status.png" width="50%">
</p>

### List Flows on the cloud

```bash
jc list
```

You can see the ALIVE Flows deployed by you.

<p align="center">
<img src=".github/README-img/list.png" width="50%">
</p>

You can also filter your Flows by passing a status:

```
jc list --status FAILED
```

<p align="center">
<img src=".github/README-img/list_failed.png" width="50%">
</p>

Or see all the flows:

```
jc list --status ALL
```

<p align="center">
<img src=".github/README-img/list_all.png" width="50%">
</p>

### Advanced deployments

#### Fine-grained `resources` request

By default, `jcloud` allocates `100M` of RAM to each Executor. There might be cases where your Executor requires more memory. For example, DALLE-mini (generating image from text prompt) would need more than 100M to load the model. You can request higher memory for your Executor using `resources` arg while deploying the Flow (max 16G allowed per Executor).

```yaml
jtype: Flow
executors:
  - name: dalle_mini
    uses: jinahub+docker://DalleMini
    jcloud:
      resources:
        memory: 8G
```

#### `spot` vs `on-demand` capacity

For cost optimization, `jcloud` tries to deploy all Executors on `spot` capacity. These are ideal for stateless Executors, which can withstand interruptions & restarts. It is recommended to use `on-demand` capacity for stateful Executors (e.g.- indexers) though.

```yaml
jtype: Flow
executors:
  - name: custom
    uses: jinahub+docker://CustomExecutor
    jcloud:
      capacity: on-demand
```

#### Deploy `External Executors`

You can also expose the Executors only by setting `expose_gateway` to `false`. Read more about [External Executors.](https://docs.jina.ai/how-to/external-executor/)

```yaml
jtype: Flow
jcloud:
  expose_gateway: false
executors:
  - name: custom
    uses: jinahub+docker://CustomExecutor
```

<p align="center">
<img src=".github/README-img/external-executor.png" width="50%">
</p>

Similarly, you can also deploy & expose multiple External Executors.

```yaml
jtype: Flow
jcloud:
  expose_gateway: false
executors:
  - name: custom1
    uses: jinahub+docker://CustomExecutor1
  - name: custom2
    uses: jinahub+docker://CustomExecutor2
```

<p align="center">
<img src=".github/README-img/external-executors-multiple.png" width="50%">
</p>

#### Deploy with specific `jina` version

When deploying Flow to `jcloud`, the default `jina` version would be used. If for any reason you'd like your Flow to be built with a specific `jina` version, you can do so by using `version` arg while deploying the Flow.

```yaml
jtype: Flow
jcloud:
  version: 3.4.11
executors:
  - name: custom
    uses: jinahub+docker://CustomExecutor
```

## FAQ

- **Why does it take a while on every operation of `jcloud`?**

  Because the event listener at Jina Cloud is serverless by design, which means it spawns an instance on-demand to process your requests from `jcloud`. Note that operations such as `deploy`, `remove` in `jcloud` are not high-frequency. Hence, having a serverless listener is much more cost-efficient than an always-on listener. The downside is slower operations, nevertheless this does not affect the deployed service. Your deployed service is **always on**.

- **How long do you persist my service?**

  Until you manually `remove` it, we will persist your service as long as possible.

- **Is everything free?**

  Yes! We just need your feedback - use `jc survey` to help us understand your needs.

- **How powerful is Jina Cloud?**

  Jina Cloud scales according to your need. You can demand for the resources your Flow requires. If there's anything particular you'd be looking for, you can contact us [on Slack](https://slack.jina.ai) or let us know via `jc survey`.

- **How can I enable verbose logs with `jcloud`?**

  To make the output more verbose, you can add `--loglevel DEBUG` _before_ each CLI subcommand, e.g.

  ```bash
  jc --loglevel DEBUG deploy toy.yml
  ```

<!-- start support-pitch -->

## Support

- Check out the [Learning Bootcamp](https://learn.jina.ai) to get started with DocArray.
- Join our [Slack community](https://slack.jina.ai) and chat with other community members about ideas.
- Join our [Engineering All Hands](https://youtube.com/playlist?list=PL3UBBWOUVhFYRUa_gpYYKBqEAkO4sxmne) meet-up to discuss your use case and learn Jina's new features.
  - **When?** The second Tuesday of every month
  - **Where?**
    Zoom ([see our public events calendar](https://calendar.google.com/calendar/embed?src=c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com&ctz=Europe%2FBerlin)/[.ical](https://calendar.google.com/calendar/ical/c_1t5ogfp2d45v8fit981j08mcm4%40group.calendar.google.com/public/basic.ics))
    and [live stream on YouTube](https://youtube.com/c/jina-ai)
- Subscribe to the latest video tutorials on our [YouTube channel](https://youtube.com/c/jina-ai)

## Join Us

JCloud is backed by [Jina AI](https://jina.ai) and licensed under [Apache-2.0](./LICENSE). [We are actively hiring](https://jobs.jina.ai) AI engineers, solution engineers to build the next neural search ecosystem in open-source.

<!-- end support-pitch -->
