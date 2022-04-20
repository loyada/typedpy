from typedpy import create_pyi


class JobController:
    def __init__(self, urls: dict[str, dict]):
        self.urls =urls

    def execute(self, job_id:str):
        pass


if __name__ == "__main__":
    create_pyi(__file__, locals())
