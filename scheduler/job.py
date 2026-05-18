from dataclasses import dataclass, field
from typing import List, Optional
from shared.constants import TaskState, Priority
import threading

@dataclass
class Task:
    id: str
    name: str
    service_type: str
    duration: int
    original_priority: Priority
    dependencies: List[str] = field(default_factory=list)
    
    # Dynamic execution states
    state: TaskState = TaskState.PENDING
    current_priority: Priority = None
    remaining_time: int = 0
    assigned_service_id: Optional[str] = None
    
    # Timing and scheduling metrics
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    wait_time: float = 0.0
    ticks_since_priority_boost: int = 0

    # Threading primitives for preemptive OS scheduling
    _pause_event: threading.Event = field(default_factory=threading.Event)
    _completion_event: threading.Event = field(default_factory=threading.Event)
    
    def __post_init__(self):
        if self.current_priority is None:
            self.current_priority = self.original_priority
        self.remaining_time = self.duration
        self._pause_event.set() # Initially not paused

    def reset(self):
        self.state = TaskState.PENDING
        self.current_priority = self.original_priority
        self.remaining_time = self.duration
        self.assigned_service_id = None
        self.start_time = None
        self.end_time = None
        self.wait_time = 0.0
        self.ticks_since_priority_boost = 0
        self._pause_event.set()
        self._completion_event.clear()

    def start(self, time_now: float, service_id: str):
        if self.start_time is None:
            self.start_time = time_now
        self.state = TaskState.RUNNING
        self.assigned_service_id = service_id
        self._pause_event.set() # Resume if paused

    def preempt(self):
        """Pause the task thread (Context Switch)"""
        self.state = TaskState.READY
        self.assigned_service_id = None
        self._pause_event.clear()

    def is_completed(self) -> bool:
        return self.state == TaskState.COMPLETED
