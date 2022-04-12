# JCloud


JCloud is the command line interface that simplifies deploying and managing Jina projects on Jina Cloud.

> Jina Cloud is the the cloud infrastructure provided by Jina AI. It hosts your Jina project, provides computational and storage resources. Jina Cloud is now in early beta, you can apply the access token here for free.


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

You can use Github/Google account to login.

### Deploy a Flow

```bash
jc deploy toy.yml
```

The simplest `toy.yml` looks like the following:

```yaml
jtype: Flow
executors: {}
```

Flow is succefully deployed when you see:

<p align="center">
<a href="https://jcloud.jina.ai"><img src="https://github.com/jina-ai/jcloud/blob/main/.github/README-img/deploy.svg?raw=true" width="40%"></a>
</p>

You will get an Flow ID, say `84b8b495df`. This ID is required to manage, view logs and remove the Flow.

Since this Flow is deployed with default gRPC gateway, you can use `jina.Client` to access it

```python
from jina import Client, Document

c = Client(host='grpcs://84b8b495df.wolf.jina.ai')
print(c.post('/', Document(text='hello')))
```



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


