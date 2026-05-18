from scheduler.job import Task
from shared.constants import DEFAULT_AGING_THRESHOLD, DEFAULT_AGING_STEP, Priority

class AgingPolicy:
    def __init__(self, aging_threshold: int = DEFAULT_AGING_THRESHOLD, aging_step: int = DEFAULT_AGING_STEP):
        self.aging_threshold = aging_threshold
        self.aging_step = aging_step

    def apply(self, task: Task) -> bool:
        """
        Calculates if a task's priority should be boosted based on waiting duration.
        If it meets the aging threshold, it upgrades the priority and returns True.
        """
        # The priority boost condition is evaluated.
        # If the task has spent enough ticks waiting without a boost, increase it.
        if task.ticks_since_priority_boost >= self.aging_threshold:
            if task.current_priority < Priority.CRITICAL:
                old = task.current_priority
                # Increment the priority level by the aging step
                new_val = min(int(task.current_priority) + self.aging_step, int(Priority.CRITICAL))
                task.current_priority = Priority(new_val)
                task.ticks_since_priority_boost = 0
                return task.current_priority != old
        return False
