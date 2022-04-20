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
<a href="https://slack.jina.ai"><img src="https://img.shields.io/badge/Slack-2.7k%2B-blueviolet?logo=slack&amp;logoColor=white&style=flat-square"></a>
</p>

☁️ **To the cloud!** - Smoothly deploy a local project as a cloud service. Radically easy, no brainfuck.

🎯 **Cut to the chase** - One CLI with five commands to manage the lifecycle of your Jina projects.

🎟️ **Early free access** - Sneak peek at our stealthy cloud hosting platform. Built on latest cloud-native tech stack, we now host your Jina project and offer computational and storage resources, for free!


## Install

```bash
pip install jcloud
jc -h
```

In case `jc` is already used by another command/tool, please use `jcloud` instead. 

## Get Started

### Login

```bash
jc login
```

You can use Google/Github account to register and login. Without login, you can do nothing.

### Deploy a Jina Project

In Jina's idiom, a project is a [Flow](https://docs.jina.ai/fundamentals/flow/), which represents an end-to-end task such as indexing, searching, recommending. In the sequel, we will use "project" and "Flow" interchangeably.

A Flow can have two types of file structure:
- **A folder**: just like a regular Python project, you can have sub-folders of Executor implementations; and a `flow.yml` on the top-level to connect all Executors together. You can create an example project folder via `jc new`. This is often used in **prototyping**.
- **A single YAML file**: a self-contained YAML file, consisting of all configs at the Flow-level and [Executor](https://docs.jina.ai/fundamentals/executor/)-level. Note that, all Executors' `uses: ` must follow `uses: jinahub+docker://MyExecutor` (from [Jina Hub](https://hub.jina.ai)) or `uses: docker://your_dockerhub_org/MyExecutor` (from Docker Hub) to avoid any local file dependency. This is often used in **production**.


#### Deploy a Flow from a folder

```bash
jc new ./hello
jc deploy ./hello
```

#### Deploy a Flow from a single YAML


```bash
jc deploy toy.yml
```


The simplest `toy.yml` looks like the following:

```yaml
jtype: Flow
executors: {}
```

A slightly complicated example, e.g. DALLE-mini (generating image from text prompt) looks like the following:

```yaml
jtype: Flow
with:
  protocol: http
executors:
  - name: dalle_mini
    uses: jinahub+docker://DalleMini
```

Flow is succefully deployed when you see:

<p align="center">
<a href="https://jcloud.jina.ai"><img src="https://github.com/jina-ai/jcloud/blob/main/.github/README-img/deploy.png?raw=true" width="50%"></a>
</p>

You will get a Flow ID, say `84b8b495df`. This ID is required to manage, view logs and remove the Flow.

As this Flow is deployed with default gRPC gateway (feel free changing it to http or websocket), you can use `jina.Client` to access it:

```python
from jina import Client, Document

c = Client(host='grpcs://84b8b495df.wolf.jina.ai')
print(c.post('/', Document(text='hello')))
```



### View logs

To watch the logs in realtime.

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

### Verbose logs

To make the output more verbose, you can add `--loglevel DEBUG` *before* each CLI subcommand, e.g.

```bash
jc --loglevel DEBUG deploy toy.yml
```

gives you more comprehensive output.

## FAQ

- **Why does it take a while on every operation of `jcloud`?**
  
    Because the event listener at Jina Cloud is serveless by design, which means it spawns an instance on-demand to process your requests from `jcloud`. Note that operation such as `deploy`, `remove` in `jcloud` is not high-frequent. Hence, having a serveless listener is much more cost-efficient than an always-on listener. The downside is slower operations, nevertheless this does not affect the deployed service. Your deployed service is **always on**.
- **How long do you persist my service?**

    Until you manually `remove` it, we will persist your service as long as possible.
- **Is everything free?**

    Yes! We just need your feedback - use `jc survey` to help us understand your needs.
- **How powerful is Jina Cloud?**
  
    Right now it is just `m5.2xlarge`. We are implementing auto-scaling of hosts on the server side. Also, it would be nice if you contact us [on Slack](https://slack.jina.ai) or via `jc survey` to help us understand your needs.
- **How do I send request to a HTTP server?**

  First, you need to set the Flow protocol to `http`. Then make sure you are sending to `/post` endpoint, e.g.
  
  ```bash
  curl -X POST https://6893976a58.wolf.jina.ai/post -H 'Content-Type: application/json' -d '{"data":[{"text": "hello, world!"}], "execEndpoint":"/"}'
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
