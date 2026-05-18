from enum import Enum, IntEnum

class TaskState(Enum):
    PENDING = "PENDING"      # Waiting for dependencies to complete
    READY = "READY"          # All dependencies met, in the ready queue
    RUNNING = "RUNNING"      # Currently executing on a service resource
    COMPLETED = "COMPLETED"  # Successfully executed
    FAILED = "FAILED"        # Failed during execution
    SKIPPED = "SKIPPED"      # Skipped due to critical dependency failure

class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TimeOfDay(Enum):
    PEAK_HOURS = "PEAK_HOURS"
    NIGHT_HOURS = "NIGHT_HOURS"

# Map priority values to names and vice-versa
PRIORITY_COLORS = {
    Priority.LOW: "green",
    Priority.MEDIUM: "blue",
    Priority.HIGH: "yellow",
    Priority.CRITICAL: "red"
}

# Scheduler Configuration Defaults
DEFAULT_AGING_THRESHOLD = 5  # Seconds after which priority increases
DEFAULT_AGING_STEP = 1       # Amount to increase priority by during aging
MAX_PRIORITY_LEVEL = Priority.CRITICAL
