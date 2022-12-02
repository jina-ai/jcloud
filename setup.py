import sys
from os import path

from setuptools import find_packages, setup

if sys.version_info < (3, 7, 0):
    raise OSError(f'Requires Python >=3.7, but yours is {sys.version}')

try:
    pkg_name = 'jcloud'
    libinfo_py = path.join(pkg_name, '__init__.py')
    libinfo_content = open(libinfo_py, 'r', encoding='utf8').readlines()
    version_line = [l.strip() for l in libinfo_content if l.startswith('__version__')][
        0
    ]
    exec(version_line)  # gives __version__
except FileNotFoundError:
    __version__ = '0.0.0'

try:
    with open('README.md', encoding='utf8') as fp:
        _long_description = fp.read()
except FileNotFoundError:
    _long_description = ''

setup(
    name=pkg_name,
    packages=find_packages(),
    version=__version__,
    include_package_data=True,
    description='Simplify deploying and managing Jina projects on Jina Cloud',
    author='Jina AI',
    author_email='hello@jina.ai',
    license='Apache 2.0',
    url='https://github.com/jina-ai/jcloud',
    download_url='https://github.com/jina-ai/jcloud/tags',
    long_description=_long_description,
    long_description_content_type='text/markdown',
    zip_safe=False,
    setup_requires=['setuptools>=18.0', 'wheel'],
    install_requires=[
        'rich>=12.0.0',
        'aiohttp>=3.8.0',
        'jina-hubble-sdk>=0.26.10',
        'packaging',
        'pyyaml',
        'python-dotenv',
        'python-dateutil',
    ],
    extras_require={
        'test': [
            'pytest',
            'pytest-asyncio',
            'pytest-timeout',
            'pytest-mock',
            'pytest-cov',
            'pytest-repeat',
            'pytest-reraise',
            'pytest-env',
            'mock',
            'pytest-custom_exit_code',
            'black==22.3.0',
            'jina>=3.7.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'jcloud=jcloud.__main__:main',
            'jc=jcloud.__main__:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Unix Shell',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'Topic :: Multimedia :: Video',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    project_urls={
        'Documentation': 'https://jcloud.jina.ai',
        'Source': 'https://github.com/jina-ai/jcloud/',
        'Tracker': 'https://github.com/jina-ai/jcloud/issues',
    },
    keywords='jcloud neural-search serverless deployment devops mlops',
)
