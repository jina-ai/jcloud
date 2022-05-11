from jina import Document, DocumentArray, Executor, requests


class MyExecutor(Executor):
    @requests
    def get_shard_id(self, docs: DocumentArray, **kwargs):
        return DocumentArray([Document(text=str(self.runtime_args.shard_id))])
