from jina import DocumentArray, Executor, requests


class MyExecutor1(Executor):
    def __init__(self, init_var, **kwargs):
        super().__init__(**kwargs)
        self.init_var = init_var

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        for d in docs:
            d.tags.update({'MyExecutor1': self.init_var})
