from datetime import datetime

from examples.subpackage.apis import Vehicle
from typedpy import create_pyi
from examples.controllers.job_controller import JobController


class ScheduledController(JobController):
    def __init__(self, *args, d: datetime, job_controller: JobController, vehicle: Vehicle, **kw):
        self.d=d
        super().__init__(*args, **kw)

    def is_it_time(self, *, a=1) -> bool:
        return False


if __name__ == "__main__":
    create_pyi(__file__, locals())

