import time
from typing import Dict, Any
from shared.constants import TimeOfDay

class SimulationTimePolicy:
    def __init__(self, mode: str = "instant", tick_delay_ms: float = 100.0):
        self.mode = mode
        self.tick_delay_ms = tick_delay_ms
        self.time_of_day = TimeOfDay.PEAK_HOURS

    def pace(self):
        if self.mode == "realtime" and self.tick_delay_ms > 0:
            time.sleep(self.tick_delay_ms / 1000.0)

    def set_speed(self, speed_label: str):
        if speed_label == "slow":
            self.mode = "realtime"
            self.tick_delay_ms = 1000.0
        elif speed_label == "medium":
            self.mode = "realtime"
            self.tick_delay_ms = 500.0
        elif speed_label == "fast":
            self.mode = "realtime"
            self.tick_delay_ms = 100.0
        else:
            self.mode = "instant"
            self.tick_delay_ms = 0.0

    def toggle_time_of_day(self) -> TimeOfDay:
        if self.time_of_day == TimeOfDay.PEAK_HOURS:
            self.time_of_day = TimeOfDay.NIGHT_HOURS
        else:
            self.time_of_day = TimeOfDay.PEAK_HOURS
        return self.time_of_day

    def get_info(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "delay_ms": self.tick_delay_ms,
            "time_of_day": self.time_of_day.value
        }
