from .job_controller import JobController


class AController:
    _abc: list
    _name: str

    def __init__(
        self,
        val: int,
        other,
        name: str = "default",
        *,
        urls: dict[str, dict] = None,
        job_controller: JobController
    ):
        self._urls = urls
        self._name = name
        self.value = val
        self._job_controller = job_controller
