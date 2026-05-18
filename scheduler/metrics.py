from typing import List, Dict, Any
from scheduler.job import Task

class MetricsCollector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.makespan: int = 0
        self.avg_wait_time: float = 0.0
        self.avg_turnaround_time: float = 0.0
        self.total_cost: float = 0.0
        self.service_utilization: Dict[str, float] = {}
        self.throughput: float = 0.0
        self.task_summaries: List[Dict[str, Any]] = []

    def calculate_metrics(self, tasks: List[Task], services: Dict[str, Any], total_ticks: int):
        """
        Processes completed simulation logs to generate key-performance metrics.
        """
        self.reset()
        self.makespan = total_ticks

        if not tasks:
            return

        total_wait = 0
        total_turnaround = 0
        self.total_cost = 0.0
        self.task_summaries = []

        for task in tasks:
            # Turnaround time = End Time - Time it arrived (assumed tick 0 in this simplified cluster)
            turnaround = (task.end_time or total_ticks)
            total_turnaround += turnaround
            total_wait += task.wait_time
            
            # Find the service it ran on to compute operational cost
            srv_cost = 0.0
            if task.assigned_service_id and task.assigned_service_id in services:
                srv = services[task.assigned_service_id]
                srv_cost = task.duration * srv.cost_per_tick
                self.total_cost += srv_cost

            self.task_summaries.append({
                "id": task.id,
                "name": task.name,
                "service": task.assigned_service_id,
                "priority": task.original_priority.name,
                "duration": task.duration,
                "start": task.start_time,
                "end": task.end_time,
                "wait_time": task.wait_time,
                "turnaround_time": turnaround,
                "cost": srv_cost
            })

        self.avg_wait_time = total_wait / len(tasks)
        self.avg_turnaround_time = total_turnaround / len(tasks)
        self.throughput = len(tasks) / total_ticks if total_ticks > 0 else 0.0

        # Calculate average utilization per service based on active time slices
        for srv_id, srv in services.items():
            # If the service capacity was used, we calculate utilization.
            # In our simulation snapshot we track this per tick.
            # However, we can also compute it statically from the completed task start/end times.
            total_slots_ticks = srv.total_capacity * total_ticks
            if total_slots_ticks == 0:
                self.service_utilization[srv_id] = 0.0
                continue
                
            active_slots_ticks = 0
            for task in tasks:
                if task.assigned_service_id == srv_id and task.start_time is not None:
                    end_tick = task.end_time if task.end_time is not None else total_ticks
                    active_slots_ticks += (end_tick - task.start_time)
            
            self.service_utilization[srv_id] = min((active_slots_ticks / total_slots_ticks) * 100, 100.0)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "makespan": self.makespan,
            "avg_wait_time": round(self.avg_wait_time, 2),
            "avg_turnaround_time": round(self.avg_turnaround_time, 2),
            "total_cost": round(self.total_cost, 2),
            "throughput": round(self.throughput, 3),
            "service_utilization": {sid: round(val, 2) for sid, val in self.service_utilization.items()},
            "task_summaries": self.task_summaries
        }
