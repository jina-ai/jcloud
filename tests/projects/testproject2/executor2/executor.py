from jina import DocumentArray, Executor, requests


class MyExecutor2(Executor):
    def __init__(self, init_var, **kwargs):
        super().__init__(**kwargs)
        self.init_var = init_var

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text = 'hello, world from executor2'
        docs[0].tags = {'init_var': self.init_var}
        docs[1].text = 'goodbye, world from executor2'
        docs[0].tags = {'init_var': self.init_var}
