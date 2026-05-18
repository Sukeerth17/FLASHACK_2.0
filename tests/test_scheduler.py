import pytest
import time
from shared.constants import Priority, TaskState, TimeOfDay
from scheduler.job import Task
from scheduler.priority_scheduler import PriorityScheduler

def test_time_of_day_policy():
    services = [{"id": "srv", "name": "S", "type": "BANDWIDTH", "capacity": 1, "cost_per_tick": 1.0}]
    
    task_dns = Task(id="T1", name="DNS Request", service_type="BANDWIDTH", duration=1, original_priority=Priority.MEDIUM)
    task_bkp = Task(id="T2", name="Database Backup", service_type="BANDWIDTH", duration=1, original_priority=Priority.MEDIUM)
    
    scheduler = PriorityScheduler(services, [task_dns, task_bkp], use_aging=False)
    
    # Peak Hours: DNS -> CRITICAL, Backup -> LOW
    scheduler.time_policy.time_of_day = TimeOfDay.PEAK_HOURS
    scheduler.apply_time_of_day_policy(task_dns)
    scheduler.apply_time_of_day_policy(task_bkp)
    assert task_dns.current_priority == Priority.CRITICAL
    assert task_bkp.current_priority == Priority.LOW
    
    # Night Hours: DNS -> default, Backup -> CRITICAL
    scheduler.time_policy.time_of_day = TimeOfDay.NIGHT_HOURS
    scheduler.apply_time_of_day_policy(task_bkp)
    assert task_bkp.current_priority == Priority.CRITICAL

def test_aging_preemption():
    task = Task(id="T_starve", name="Starve", service_type="BANDWIDTH", duration=5, original_priority=Priority.LOW)
    task.state = TaskState.READY
    
    task.wait_time = 0
    task.ticks_since_priority_boost = 0
    
    from scheduler.aging import AgingPolicy
    policy = AgingPolicy(aging_threshold=3, aging_step=1)
    
    # Tick 1 & 2
    task.ticks_since_priority_boost += 1
    assert not policy.apply(task)
    
    task.ticks_since_priority_boost += 1
    assert not policy.apply(task)
    
    # Tick 3 -> Boosts to MEDIUM
    task.ticks_since_priority_boost += 1
    assert policy.apply(task)
    assert task.current_priority == Priority.MEDIUM
