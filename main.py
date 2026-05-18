import os
import json
import argparse
from shared.constants import Priority
from sequencer.graph_builder import GraphBuilder
from sequencer.cycle_detector import CycleDetector
from sequencer.topo_sort import TopologicalSorter
from sequencer.critical_handler import CriticalPathHandler
from scheduler.job import Task
from scheduler.priority_scheduler import PriorityScheduler
from visualization.logger import PacketPathLogger
from visualization.graph_visualizer import GraphVisualizer
from visualization.gantt_chart import GanttChartGenerator

def run_pipeline(use_aging: bool = True):
    PacketPathLogger.banner("NETWORK BOOT SEQUENCER & ADAPTIVE SCHEDULER")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    services_path = os.path.join(base_dir, "config", "services.json")
    jobs_path = os.path.join(base_dir, "config", "jobs.json")

    with open(services_path, "r") as f:
        services_data = json.load(f)
    with open(jobs_path, "r") as f:
        jobs_data = json.load(f)

    all_tasks_data = services_data + jobs_data

    # 1. Build graph & DFS validate
    builder = GraphBuilder()
    adj_list, nodes = builder.build_graph(all_tasks_data)
    in_degrees = builder.get_in_degrees()

    PacketPathLogger.info("Verifying circular dependencies via DFS 3-Coloring...")
    detector = CycleDetector(adj_list)
    if detector.has_cycle():
        cycle_path = detector.get_cycle_path()
        PacketPathLogger.error(f"FATAL: Cycle detected: {' -> '.join(cycle_path)}")
        return

    PacketPathLogger.success("Network sequence is a valid DAG!")

    # Topological sorting (DFS)
    sorter = TopologicalSorter(adj_list, in_degrees)
    topo_order = sorter.sort()
    PacketPathLogger.success(f"DFS Boot Sequence: {', '.join(topo_order)}")

    critical_handler = CriticalPathHandler(adj_list, nodes, topo_order)
    critical_path, critical_duration = critical_handler.find_critical_path()
    PacketPathLogger.success(f"Critical Path: {' -> '.join(critical_path)}")

    # Plot dependency DAG text
    viz = GraphVisualizer(adj_list, nodes)
    viz.plot_graph_text(critical_path)

    # 2. Simulate Multithreaded OS Scheduler
    PacketPathLogger.info("Starting Dispatcher Thread Scheduler Simulation...")
    tasks = []
    for job in all_tasks_data:
        tasks.append(
            Task(
                id=job["id"],
                name=job["name"],
                service_type=job.get("type", job.get("service_type")),
                duration=job.get("duration", 1),
                original_priority=Priority[job.get("priority", "MEDIUM")],
                dependencies=job.get("dependencies", [])
            )
        )

    scheduler = PriorityScheduler(services_data, tasks, use_aging=use_aging)
    history = scheduler.run_simulation()
    
    PacketPathLogger.banner("DISPATCHER THREAD LOGS")
    for log in scheduler.context_switch_logs:
        print(log)
    
    metrics = scheduler.metrics_collector.get_summary()

    # 3. Print Gantt Timeline
    gantt = GanttChartGenerator(metrics["task_summaries"])
    gantt.render_ascii_timeline()

    # 4. Summary
    PacketPathLogger.banner("METRICS SUMMARY")
    PacketPathLogger.info(f"Total Makespan               : {metrics['makespan']} ticks")
    PacketPathLogger.info(f"Context Switches (Preempted) : {len([x for x in scheduler.context_switch_logs if 'PREEMPTED' in x])}")
    PacketPathLogger.info(f"Avg Wait Time                : {metrics['avg_wait_time']} ticks")
    
    PacketPathLogger.success("Network and Scheduling Pipeline executed successfully!\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PacketPath Sequencer CLI")
    parser.add_argument("--no-aging", action="store_true", help="Disable starvation aging policy")
    args = parser.parse_args()
    
    run_pipeline(use_aging=not args.no_aging)
