from datetime import datetime

from typedpy import create_pyi
from examples.controllers.job_controller import JobController


class ScheduledController(JobController):
    def __init__(self, *args, d: datetime, **kw):
        self.d=d
        super().__init__(*args, **kw)

    def is_it_time(self) -> bool:
        return False


if __name__ == "__main__":
    create_pyi(__file__, locals())

