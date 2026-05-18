# 🕸️ PacketPath: Network Boot Sequencer & Adaptive Bandwidth Scheduler

PacketPath is an enterprise-grade network simulation framework designed to solve two core infrastructure problems:
1. **Cascading Boot Failures:** Prevents cyclic initialization issues using **DAA** (Design and Analysis of Algorithms) graph models.
2. **Bandwidth Congestion:** Manages competing network task threads using an **OS** (Operating Systems) preemptive priority scheduler.

---

## 🚀 Key Features

### DAA Layer (Dependency Engine)
*   **DFS 3-Color Cycle Detection:** Identifies circular dependencies preventing server boot-ups.
*   **Recursive DFS Topological Sort:** Generates the exact deterministic order in which network services must boot.
*   **Failure Propagation:** Uses localized BFS to traverse downstream nodes, safely marking dependent services as `SKIPPED` when a parent `FAILED`.

### OS Layer (Scheduler Engine)
*   **True Multithreading:** Each network job runs concurrently in its own Python `Thread`.
*   **Dispatcher Preemption:** A central OS manager actively context-switches threads using `threading.Event` primitives to yield CPU/bandwidth to critical traffic.
*   **Starvation Prevention (Aging):** Dynamically increases priority tiers of ignored jobs over time.
*   **Time-of-Day Policies:** Automatically boosts "User Traffic" during `PEAK_HOURS` and "System Backups" during `NIGHT_HOURS`.

---

## 📂 Hackathon Architecture & Team Domains

This project is strictly partitioned to prevent Git merge conflicts for a 3-member team:

*   `sequencer/` **(DAA Engineer):** Graph building, DFS sorting, and cycle handlers.
*   `scheduler/` **(OS Engineer):** Multithreaded jobs, aging, context switches, and dispatching.
*   `ui/` & `visualization/` **(Full-Stack/UI):** Streamlit dashboard, Plotly Gantt charts, queue metrics.

---

## 🛠️ Setup Instructions

### 1. Install Dependencies
Requires Python 3.9+. Install the core packages:
```bash
pip install -r requirements.txt
```

### 2. Run the Command Line Simulator
Execute the full OS pipeline to see real-time multithreaded context-switch dispatch logs:
```bash
python main.py
```
*(Disable starvation-prevention using `python main.py --no-aging`)*

### 3. Launch the Interactive Web Dashboard
Run the following command to start the beautiful, responsive Streamlit dashboard:
```bash
streamlit run ui/dashboard.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser to view the Live Queue Monitor, DFS DAG Maps, and the OS Gantt Thread Timelines!

### 4. Run the Automated Tests
Verify that all logical sequencing, cycles, and priority queue orders work flawlessly by running:
```bash
pytest -v
```
