<p align="center">
<br>
<br>
<br>
<img src=https://github.com/jina-ai/jcloud/blob/main/docs/_static/logo-light.svg?raw=true" alt="JCloud logo: the command line interface that simplifies deploying and managing Jina projects on Jina Cloud" width="80px">
<br>
<br>
<br>
<b>Simplify deploying and managing Jina projects on Jina Cloud</b>
</p>

<p align=center>
<a href="https://pypi.org/project/jcloud/"><img alt="PyPI" src="https://img.shields.io/pypi/v/jcloud?label=PyPI&logo=pypi&logoColor=white&style=flat-square"></a>
<a href="https://slack.jina.ai"><img src="https://img.shields.io/badge/Slack-2.7k%2B-blueviolet?logo=slack&amp;logoColor=white&style=flat-square"></a>
</p>

☁️ **To the cloud!** - Smoothly deploy a local project as a cloud service. Radically easy, no brainfuck.

🎯 **Cut to the chase** - One CLI with five commands to manage the lifecycle of your Jina projects.

🎟️ **Early free access** - Sneak peek at our steathy cloud hosting platform. Built on latest cloud-native tech stack to host your Jina project and offer computational and storage resources. And it is free for now!


## Install

```bash
pip install jcloud
jc -h
```

## Get Started

### Login

```bash
jc login
```

You can use Google/Github account to register and login. Without login, you can do nothing.

### Deploy a Jina Flow

In Jina's idiom, a Flow is a project. A Flow represents an end-to-end task such as indexing, searching, recommending, etc. In the sequel, we will use "project" and "Flow" interchangeably. 

#### Deploy a single YAML Flow

A Jina Flow can be as simple as a single YAML file, representing a Flow with all configs and executors in it. The simplest `toy.yml` looks like the following:

```yaml
jtype: Flow
executors: {}
```

To make a single-YAML Flow in practice, it requires all Executors to be specified with `uses: jinahub+docker://MyExecutor` or `uses: docker://your_dockerhub_org/MyExecutor`. No more file dependency. The YAML itself is self-contained.


To deploy it:

```bash
jc deploy toy.yml
```


Flow is succefully deployed when you see:

<p align="center">
<a href="https://jcloud.jina.ai"><img src="https://github.com/jina-ai/jcloud/blob/main/.github/README-img/deploy.png?raw=true" width="50%"></a>
</p>

You will get an Flow ID, say `84b8b495df`. This ID is required to manage, view logs and remove the Flow.

As this Flow is deployed with default gRPC gateway, you can use `jina.Client` to access it:

```python
from jina import Client, Document

c = Client(host='grpcs://84b8b495df.wolf.jina.ai')
print(c.post('/', Document(text='hello')))
```

#### Deploy a Flow from a folder

You can also deploy a Jina Flow from a local folder:

```bash
jc deploy /my/folder
```

Note that `/my/folder` must contain a `flow.yml` that represents the Flow. Besides, it can contain sub-folders of Executor implementations. You can create an example project folder via `jc new`.


### View logs

```bash
jc logs 84b8b495df
```

### Remove a Flow

```bash
jc remove 84b8b495df
```

### Get the status of a Flow

```bash
jc status 84b8b495df
```

<p align="center">
<a href="https://jcloud.jina.ai"><img src="https://github.com/jina-ai/jcloud/blob/main/.github/README-img/status.png?raw=true" width="50%"></a>
</p>


### List all Flows on the cloud

```bash
jc list
```

You can only see the Flows deployed by you.

<p align="center">
<a href="https://jcloud.jina.ai"><img src="https://github.com/jina-ai/jcloud/blob/main/.github/README-img/list.png?raw=true" width="50%"></a>
</p>


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
