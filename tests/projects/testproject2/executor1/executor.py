from jina import DocumentArray, Executor, requests


class MyExecutor1(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text = 'hello, world from executor1'
        docs[1].text = 'goodbye, world from executor1'
