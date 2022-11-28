from jina import Executor, requests, DocumentArray


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[:, 'text'] = 'hello, world!'
