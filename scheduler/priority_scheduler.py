import time
import threading
from typing import Dict, List, Optional
from shared.constants import TaskState, Priority, TimeOfDay
from scheduler.job import Task
from scheduler.aging import AgingPolicy
from scheduler.metrics import MetricsCollector
from scheduler.time_policy import SimulationTimePolicy
from visualization.logger import PacketPathLogger

class ServiceInstance:
    def __init__(self, id: str, name: str, service_type: str, capacity: int, cost_per_tick: float):
        self.id = id
        self.name = name
        self.type = service_type
        self.total_capacity = capacity
        self.current_usage = 0
        self.cost_per_tick = cost_per_tick
        self.running_tasks: List[Task] = []
        self.lock = threading.Lock()

    @property
    def available_capacity(self) -> int:
        return self.total_capacity - self.current_usage

    def allocate(self, task: Task) -> bool:
        with self.lock:
            if self.available_capacity > 0:
                self.running_tasks.append(task)
                self.current_usage += 1
                return True
            return False

    def release(self, task: Task) -> bool:
        with self.lock:
            if task in self.running_tasks:
                self.running_tasks.remove(task)
                self.current_usage -= 1
                return True
            return False

class PriorityScheduler:
    def __init__(self, services_data: List[dict], tasks: List[Task], use_aging: bool = True):
        self.services = {
            srv["id"]: ServiceInstance(srv["id"], srv["name"], srv["type"], srv["capacity"], srv["cost_per_tick"])
            for srv in services_data
        }
        self.tasks: Dict[str, Task] = {task.id: task for task in tasks}
        self.use_aging = use_aging
        self.aging_policy = AgingPolicy()
        self.metrics_collector = MetricsCollector()
        self.time_policy = SimulationTimePolicy("realtime", 100.0) 
        
        self.history: List[dict] = []
        self.context_switch_logs: List[str] = []
        self.start_time = 0.0

    def apply_time_of_day_policy(self, task: Task):
        """Dynamic Priority Adjustment based on Time of Day"""
        if self.time_policy.time_of_day == TimeOfDay.PEAK_HOURS:
            if "DNS" in task.name or "Video" in task.name:
                task.current_priority = Priority.CRITICAL
            elif "Backup" in task.name:
                task.current_priority = Priority.LOW
        else: # NIGHT_HOURS
            if "Backup" in task.name or "Sync" in task.name:
                task.current_priority = Priority.CRITICAL
            elif "Video" in task.name:
                task.current_priority = Priority.LOW

    def _task_worker(self, task: Task):
        """Thread worker for each network job. Blocks when preempted."""
        while task.remaining_time > 0:
            task._pause_event.wait() # Block if preempted
            if task.state == TaskState.RUNNING:
                time.sleep(self.time_policy.tick_delay_ms / 1000.0)
                task.remaining_time -= 1
                
        # Thread completion
        if task.state != TaskState.SKIPPED:
            task.state = TaskState.COMPLETED
            # End time relative to current_tick approx
            task.end_time = time.time() - self.start_time
            task._completion_event.set()

    def run_simulation(self, simulate_failure_node: str = None) -> List[dict]:
        self.history = []
        self.context_switch_logs = []
        self.start_time = time.time()
        
        # Setup and apply time of day to ready tasks
        for task in self.tasks.values():
            task.reset()
            if simulate_failure_node and task.id == simulate_failure_node:
                task.state = TaskState.FAILED
            elif not task.dependencies:
                task.state = TaskState.READY
                self.apply_time_of_day_policy(task)

        # Start task threads in paused state
        threads = []
        for task in self.tasks.values():
            task._pause_event.clear()
            t = threading.Thread(target=self._task_worker, args=(task,))
            t.daemon = True
            t.start()
            threads.append(t)

        current_tick = 0
        while not all(task.state in (TaskState.COMPLETED, TaskState.SKIPPED, TaskState.FAILED) for task in self.tasks.values()):
            # 1. Release completed/skipped tasks
            for service in self.services.values():
                completed = [t for t in service.running_tasks if t.is_completed() or t.state == TaskState.SKIPPED]
                for t in completed:
                    service.release(t)
                    self.context_switch_logs.append(f"[{current_tick}] 🟢 COMPLETED: {t.id} released bandwidth from {service.name}")

            # 2. Dependency resolution and Failure Propagation checks
            for task in self.tasks.values():
                if task.state == TaskState.PENDING:
                    deps_met = True
                    for dep in task.dependencies:
                        if self.tasks[dep].state == TaskState.SKIPPED or self.tasks[dep].state == TaskState.FAILED:
                            task.state = TaskState.SKIPPED
                            self.context_switch_logs.append(f"[{current_tick}] ❌ SKIPPED: {task.id} (Dependency {dep} failed/skipped)")
                            deps_met = False
                            break
                        elif self.tasks[dep].state != TaskState.COMPLETED:
                            deps_met = False
                            break
                            
                    if deps_met and task.state != TaskState.SKIPPED:
                        task.state = TaskState.READY
                        self.apply_time_of_day_policy(task)

            # 3. Aging
            if self.use_aging:
                for task in self.tasks.values():
                    if task.state == TaskState.READY:
                        task.wait_time += 1
                        task.ticks_since_priority_boost += 1
                        if self.aging_policy.apply(task):
                            self.context_switch_logs.append(f"[{current_tick}] ⚡ AGING BOOST: {task.id} upgraded to {task.current_priority.name}")

            # 4. Schedule and Preempt (Context Switching)
            ready_tasks = [t for t in self.tasks.values() if t.state == TaskState.READY]
            # Highest priority first, longest wait time tie-breaker
            ready_tasks.sort(key=lambda t: (-int(t.current_priority), -t.wait_time))

            for task in ready_tasks:
                eligible_services = [s for s in self.services.values() if s.type == task.service_type]
                
                # If no specific service matches and it's bandwidth, assume any gateway
                if not eligible_services and task.service_type == "BANDWIDTH":
                    eligible_services = [s for s in self.services.values() if s.type in ("EDGE", "CORE")]

                if eligible_services:
                    srv = max(eligible_services, key=lambda s: s.available_capacity)
                    if srv.available_capacity > 0:
                        srv.allocate(task)
                        task.start(current_tick, srv.id)
                        self.context_switch_logs.append(f"[{current_tick}] ▶️ SCHEDULED: {task.id} (Priority: {task.current_priority.name}) on {srv.name}")
                    else:
                        lowest_running = min(srv.running_tasks, key=lambda t: int(t.current_priority), default=None)
                        if lowest_running and int(lowest_running.current_priority) < int(task.current_priority):
                            # Preempt operation
                            srv.release(lowest_running)
                            lowest_running.preempt() # Clears event lock pausing the thread
                            self.context_switch_logs.append(f"[{current_tick}] ⏸️ PREEMPTED: {lowest_running.id} by {task.id} (Context Switch)")
                            
                            # Allocate operation
                            srv.allocate(task)
                            task.start(current_tick, srv.id) # Sets event lock unpausing the thread
                            self.context_switch_logs.append(f"[{current_tick}] ▶️ SCHEDULED: {task.id} took over {srv.name}")

            # Snapshot capture
            snapshot = {
                "tick": current_tick,
                "tasks": {
                    tid: {
                        "state": t.state.value,
                        "priority": t.current_priority.name,
                        "remaining": t.remaining_time,
                        "service": t.assigned_service_id,
                        "wait_time": t.wait_time
                    }
                    for tid, t in self.tasks.items()
                },
                "services": {
                    sid: {
                        "running": [t.id for t in s.running_tasks],
                        "utilization": (s.current_usage / s.total_capacity) * 100
                    }
                    for sid, s in self.services.items()
                }
            }
            self.history.append(snapshot)
            current_tick += 1
            
            time.sleep(self.time_policy.tick_delay_ms / 1000.0)
            
            if current_tick > 1000:
                break 

        # Cleanup threads
        for task in self.tasks.values():
            if not task.is_completed() and task.state != TaskState.SKIPPED:
                 task._pause_event.set()
                 task._completion_event.set()

        self.metrics_collector.calculate_metrics(list(self.tasks.values()), self.services, current_tick)
        return self.history
