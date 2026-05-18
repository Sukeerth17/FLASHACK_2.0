import os
import sys
# Ensure the root 'packetpath' directory is in the Python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from shared.constants import Priority, TaskState, TimeOfDay
from sequencer.graph_builder import GraphBuilder
from sequencer.cycle_detector import CycleDetector
from sequencer.topo_sort import TopologicalSorter
from sequencer.critical_handler import CriticalPathHandler
from scheduler.job import Task
from scheduler.priority_scheduler import PriorityScheduler
from visualization.graph_visualizer import GraphVisualizer
from visualization.gantt_chart import GanttChartGenerator

# Page config and premium styling
st.set_page_config(
    page_title="PacketPath Control Dashboard",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply premium visual stylesheet
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        letter-spacing: -0.5px;
    }

    /* Stunning gradient background for main container */
    .stApp {
        background: radial-gradient(circle at top left, #121528, #0B0C15 50%, #08080C 100%);
        color: #e2e8f0;
    }

    /* Glassmorphism for Metrics */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px -10px rgba(100, 150, 255, 0.15);
        border-color: rgba(100, 150, 255, 0.3);
    }

    /* Metric Label Styling */
    div[data-testid="metric-container"] > div:first-child {
        color: #94a3b8 !important;
        font-size: 0.95rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Metric Value Styling */
    div[data-testid="metric-container"] > div:nth-child(2) {
        font-size: 2.2rem;
        font-weight: 800;
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(90deg, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        gap: 15px;
        padding-top: 15px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        color: #94a3b8;
        transition: all 0.2s ease;
        border: 1px solid transparent;
        border-bottom: none;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.08);
        color: #ffffff;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(99, 102, 241, 0.15) !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
        border-bottom: none !important;
        color: #818cf8 !important;
        font-weight: 600;
    }
    
    /* Headers */
    h1 {
        background: linear-gradient(120deg, #60a5fa, #c084fc, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(10, 11, 20, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Text area */
    .stTextArea textarea {
        background: rgba(0,0,0,0.3) !important;
        color: #4ade80 !important;
        font-family: monospace !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to load default configuration files
def load_json_file(file_path: str) -> list:
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

# App header
st.title("🕸️ PacketPath: Network Boot Sequencer & OS Scheduler")
st.write("DAA Topological Dependency Engine & OS Adaptive Multithreaded Preemptive Scheduler.")
st.markdown("---")

# Absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
SERVICES_PATH = os.path.join(BASE_DIR, "config", "services.json")
JOBS_PATH = os.path.join(BASE_DIR, "config", "jobs.json")

# Sidebar configurations
st.sidebar.header("🎛️ OS Scheduler Parameters")

# Load configuration items
services_data = load_json_file(SERVICES_PATH)
jobs_data = load_json_file(JOBS_PATH)

# Settings toggles
use_aging = st.sidebar.toggle("Enable Starvation Aging Algorithm", value=True)
aging_threshold = st.sidebar.slider("Aging Threshold (ticks)", min_value=1, max_value=30, value=5, disabled=not use_aging)
time_of_day = st.sidebar.selectbox("Time of Day Policy", [TimeOfDay.PEAK_HOURS.value, TimeOfDay.NIGHT_HOURS.value])

st.sidebar.markdown("---")
st.sidebar.subheader("🚨 Failure Simulation (DAA)")
simulate_failure = st.sidebar.selectbox("Simulate Critical Boot Failure on Node:", ["None"] + [s["id"] for s in services_data])

# Allow manual edits to configurations directly in the sidebar
st.sidebar.markdown("---")
show_config_editor = st.sidebar.checkbox("Show JSON Editors")

if show_config_editor:
    st.subheader("Edit Services Configuration")
    services_str = st.text_area("services.json content", value=json.dumps(services_data, indent=2), height=150)
    
    st.subheader("Edit Jobs Configuration")
    jobs_str = st.text_area("jobs.json content", value=json.dumps(jobs_data, indent=2), height=250)
    
    try:
        services_data = json.loads(services_str)
        jobs_data = json.loads(jobs_str)
        st.success("JSON configurations loaded from editor successfully!")
    except Exception as e:
        st.error(f"Error parsing JSON text: {e}")

# Combine both services (boot sequence) and jobs (bandwidth tasks) for the simulation
# In a real scenario, boot finishes first, then jobs run. But here we'll map both to the DAG or treat jobs independently.
all_tasks_data = services_data + jobs_data

# Build graph sequencer state
builder = GraphBuilder()
try:
    adj_list, nodes = builder.build_graph(all_tasks_data)
    in_degrees = builder.get_in_degrees()
    
    # 1. Circular dependency checks (DFS)
    detector = CycleDetector(adj_list)
    has_cycles = detector.has_cycle()
    
    if has_cycles:
        st.error("🚨 CRITICAL: Circular Dependency Detected in Graph (DFS Gray Node)!")
        st.write("Cycle path found: " + " -> ".join(detector.get_cycle_path()))
    else:
        # 2. Topological sort (DFS)
        sorter = TopologicalSorter(adj_list, in_degrees)
        topo_order = sorter.sort()
        
        # 3. Critical Path and Failure Propagation
        critical_handler = CriticalPathHandler(adj_list, nodes, topo_order)
        critical_path, critical_duration = critical_handler.find_critical_path()
        
        # Convert task configurations to live models
        tasks = []
        for j in all_tasks_data:
            tasks.append(
                Task(
                    id=j["id"],
                    name=j["name"],
                    service_type=j.get("type", j.get("service_type")),
                    duration=j.get("duration", 1),
                    original_priority=Priority[j.get("priority", "MEDIUM")],
                    dependencies=j.get("dependencies", [])
                )
            )
            
        # Instantiate scheduler simulation
        scheduler = PriorityScheduler(services_data, tasks, use_aging=use_aging)
        scheduler.time_policy.time_of_day = TimeOfDay(time_of_day)
        scheduler.aging_policy.aging_threshold = aging_threshold
        
        # Apply manual failure if requested
        if simulate_failure != "None":
            # Just marking it failed isn't enough, we need to let the failure propagation handle it dynamically or before start
            # The Dispatcher logic already handles SKIPPED if parent is FAILED or SKIPPED
            scheduler.tasks[simulate_failure].state = TaskState.FAILED
        
        # Run entire simulation to compile metrics
        with st.spinner("Running Multithreaded Job Simulation..."):
            simulation_history = scheduler.run_simulation()
            metrics = scheduler.metrics_collector.get_summary()
        
        # Grid layout for summary stats
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Makespan", f"{metrics['makespan']} ticks")
        with col2:
            st.metric("Avg Wait Time", f"{metrics['avg_wait_time']} ticks")
        with col3:
            st.metric("Avg Turnaround", f"{metrics['avg_turnaround_time']} ticks")
        with col4:
            st.metric("Context Switches", f"{len([x for x in scheduler.context_switch_logs if 'PREEMPTED' in x])}")
        with col5:
            st.metric("Throughput Rate", f"{metrics['throughput']} tasks/t")

        tab_graph, tab_gantt, tab_queue, tab_logs, tab_dfs = st.tabs([
            "📊 Network Dependency Graph (DAA)",
            "📅 OS Context Switch Gantt",
            "🖥️ Resource & Queue Monitor",
            "📜 Preemption & Boot Logs",
            "🔀 DFS Boot Sequence"
        ])
        
        with tab_graph:
            col_graph_left, col_graph_right = st.columns([2, 1])
            with col_graph_left:
                st.subheader("DFS Topological DAG")
                viz = GraphVisualizer(adj_list, nodes)
                temp_graph_path = "st_graph.png"
                fig = viz.plot_graph_graphical(critical_path, temp_graph_path)
                if fig:
                    st.image(temp_graph_path, use_column_width=True)
            
            with col_graph_right:
                st.subheader("Critical Bottleneck Path")
                st.info(f"Total Critical Path duration: **{critical_duration} ticks**")
                for idx, node_id in enumerate(critical_path):
                    st.markdown(f"**Step {idx+1}:** `{node_id}`")
                        

                
        with tab_gantt:
            st.subheader("Thread Execution Timeline (OS Gantt)")
            gantt = GanttChartGenerator(metrics["task_summaries"])
            df_gantt = pd.DataFrame(metrics["task_summaries"])
            if not df_gantt.empty:
                df_gantt["start_tick"] = df_gantt["start"]
                df_gantt["duration_ticks"] = df_gantt["duration"]
                
                fig_gantt = px.bar(
                    df_gantt,
                    x="duration_ticks",
                    y="id",
                    base="start_tick",
                    color="priority",
                    orientation="h",
                    title="OS Context Switch & Run Timeline",
                    labels={"id": "Thread Task", "duration_ticks": "Execution Time"}
                )
                fig_gantt.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#cbd5e1"
                )
                fig_gantt.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_gantt, use_container_width=True)

        with tab_queue:
            st.subheader("Live Queue Phase Viewer")
            total_ticks = len(simulation_history)
            if total_ticks > 0:
                selected_tick = st.slider("Scrub Timeline Tick", min_value=0, max_value=total_ticks - 1, value=total_ticks//2)
                tick_data = simulation_history[selected_tick]
                
                # Count queues
                q_ready = [t for t, d in tick_data['tasks'].items() if d['state'] == 'READY']
                q_run = [t for t, d in tick_data['tasks'].items() if d['state'] == 'RUNNING']
                q_wait = [t for t, d in tick_data['tasks'].items() if d['state'] == 'PENDING']
                
                col_q1, col_q2, col_q3 = st.columns(3)
                col_q1.metric("Ready Queue (Waiting CPU)", len(q_ready))
                col_q2.metric("Running Queue (Executing)", len(q_run))
                col_q3.metric("Pending Queue (Blocked)", len(q_wait))
                
                st.write("**Tasks in Ready Queue:**", q_ready)
                
                st.subheader("Bandwidth Capacity Used")
                srv_cols = st.columns(len(tick_data["services"]))
                for idx, (srv_id, srv_status) in enumerate(tick_data["services"].items()):
                    if idx < len(srv_cols):
                        with srv_cols[idx]:
                            st.metric(
                                label=f"🖥️ {srv_id}",
                                value=f"{srv_status['utilization']:.0f}% Util",
                                delta=f"Active: {len(srv_status['running'])} threads"
                            )

        with tab_logs:
            st.subheader("Central Dispatcher Thread Logs")
            st.markdown("Displays exact timestamped context switches, preemptions, starvation aging upgrades, and boot failures.")
            log_text = ""
            for log in scheduler.context_switch_logs:
                log_text += log + "\n"
            st.text_area("Live Output Console", log_text, height=400)

        with tab_dfs:
            st.subheader("Depth-First Search Topological Order")
            st.markdown("The computed deterministic boot sequence to prevent all circular dependencies:")
            
            html_content = '<div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center; padding: 20px 0;">'
            
            for idx, task in enumerate(topo_order):
                is_critical = task in critical_path
                bg_color = "linear-gradient(135deg, #ef4444, #b91c1c)" if is_critical else "rgba(255, 255, 255, 0.05)"
                border = "1px solid rgba(239, 68, 68, 0.5)" if is_critical else "1px solid rgba(255, 255, 255, 0.1)"
                font_weight = "800" if is_critical else "600"
                
                html_content += f'''
                <div style="
                    background: {bg_color};
                    border: {border};
                    padding: 10px 16px;
                    border-radius: 8px;
                    color: white;
                    font-family: 'Outfit', sans-serif;
                    font-weight: {font_weight};
                    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                ">
                    <span style="opacity: 0.6; font-size: 0.8em; margin-right: 6px;">{idx+1}</span>
                    {task}
                </div>
                '''
                
                if idx < len(topo_order) - 1:
                    html_content += '<div style="color: #64748b; font-weight: bold; font-size: 1.2em;">➔</div>'
                    
            html_content += '</div>'
            st.markdown(html_content, unsafe_allow_html=True)
            
            st.info("💡 **Note:** Nodes highlighted in **red** belong to the Critical Path and dictate the absolute minimum Makespan of the network.")

except Exception as e:
    st.error(f"Failed to compile scheduling pipeline: {e}")
    st.exception(e)
