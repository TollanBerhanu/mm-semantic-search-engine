from sched import scheduler
from time import time, sleep

class MMScheduler:

    def __init__(self) -> None:
        self.mm_scheduler = scheduler(time, sleep)


    def register_schedule(self, seconds, scheduler_function, *args) -> None:
        self.mm_scheduler.enter(
            seconds,
            1, 
            scheduler_function,
            args
        )

        self.mm_scheduler.run()

    def has_schedule(self) -> bool:
        return not self.mm_scheduler.empty()
    
    def cancel_all_schedules(self) -> None:
        if self.has_schedule():
            # Cancel each event in the scheduler queue
            for event in self.mm_scheduler.queue:
                self.mm_scheduler.cancel(event)
    