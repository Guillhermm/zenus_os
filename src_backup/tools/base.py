class Tool:
    name: str

    def dry_run(self, **kwargs) -> str:
        raise NotImplementedError

    def execute(self, **kwargs) -> str:
        raise NotImplementedError