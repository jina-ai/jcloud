from jina import DocumentArray, Executor, requests


class MyExecutor(Executor):
    def __init__(self, var_a, var_b, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.var_a = var_a
        self.var_b = var_b

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[:, 'tags'] = {'var_a': self.var_a, 'var_b': self.var_b}
