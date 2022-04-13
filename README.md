# JCloud


JCloud is the command line interface that simplifies deploying and managing Jina projects on **Jina Cloud**.

> **Jina Cloud** is the cloud infrastructure provided by Jina AI. It hosts your Jina project, offers computational and storage resources. Jina Cloud is now in early beta, you can apply the access token here for free.


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

### Deploy a Jina Project

A Jina project is a Jina Flow, representing an end-to-end task such as indexing, searching, recommending, etc. In the sequel, we will use "project" and "Flow" interchangeably. 

#### Deploy a single YAML project

A Jina project can be as simple as a single YAML file, representing a Flow with all configs and executors in it. The simplest `toy.yml` looks like the following:

```yaml
jtype: Flow
executors: {}
```

To make a single-YAML project in practice, it requires all Executors to be specified with `uses: jinahub+docker://MyExecutor` or `uses: docker://your_dockerhub_org/MyExecutor`. No more file dependency. The YAML itself is self-contained.


To deploy it:

```bash
jc deploy toy.yml
```


Flow is succefully deployed when you see:

<p align="center">
<a href="https://jcloud.jina.ai"><img src="https://github.com/jina-ai/jcloud/blob/main/.github/README-img/deploy.svg?raw=true" width="40%"></a>
</p>

You will get an Flow ID, say `84b8b495df`. This ID is required to manage, view logs and remove the Flow.

As this Flow is deployed with default gRPC gateway, you can use `jina.Client` to access it:

```python
from jina import Client, Document

c = Client(host='grpcs://84b8b495df.wolf.jina.ai')
print(c.post('/', Document(text='hello')))
```

#### Deploy a project from a folder

You can also deploy a Jina project from a local folder:

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
<a href="https://jcloud.jina.ai"><img src="https://github.com/jina-ai/jcloud/blob/main/.github/README-img/status.svg?raw=true" width="50%"></a>
</p>


### List all Flows on the cloud

```bash
jc list
```

You can only see the Flows deployed by you.


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
