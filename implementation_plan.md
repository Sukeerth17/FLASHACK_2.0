# PacketPath: Network Service Boot Sequencer & Adaptive Bandwidth Scheduler
**Implementation & Analysis Plan**

## 1. Project Architecture Overview

PacketPath is designed to solve two major network infrastructure problems: cascading boot failures due to incorrect service initialization orders (DAA), and bandwidth congestion caused by competing network tasks (OS).

The system is structured into three primary layers:
1. **Dependency Graph Engine (DAA Layer):** Handles graph building, DFS-based topological sorting, cycle detection, and failure propagation.
2. **Adaptive Scheduler Engine (OS Layer):** Manages multithreaded task execution, preemptive scheduling, aging, and time-of-day policies.
3. **Visualization Layer (Frontend):** A Streamlit dashboard for real-time Gantt charts, boot logs, queue monitoring, and dependency graphs.

---

## 2. DAA Modules: Analysis & Solution Strategy

### A1. Service Dependency Graph
- **Representation:** An Adjacency List `Dict[str, List[str]]` mapping each service to its dependent services (successors).
- **Scale:** Must comfortably support 15+ services (e.g., DNS, Proxy, Firewall, VPN, Database, Monitor).

### A2. DFS-Based Topological Sort
- **Current vs. New:** Instead of Kahn’s Algorithm, we will implement a pure **Recursive DFS**.
- **How to Solve:**
  1. Initialize a `visited` set and a `stack` list.
  2. For every unvisited node, trigger the recursive `dfs_visit()` function.
  3. Inside `dfs_visit()`, mark the node as visited, recursively call `dfs_visit()` on all its unvisited successors.
  4. Once all successors are processed, append the node to `stack`.
  5. The final boot order is the `stack` reversed.
- **Complexity:** $O(V + E)$ Time, $O(V)$ Space.

### A3. Cycle Detection
- **How to Solve:** Implement a 3-color DFS approach.
  - `WHITE` (Unvisited): Initial state.
  - `GRAY` (Visiting): Node is currently in the recursion stack.
  - `BLACK` (Completed): Node and all its descendants have been fully explored.
- If the DFS traversal encounters a `GRAY` node, a cycle is detected. The recursion path provides the exact circular sequence.

### A4. Critical Service Failure Propagation
- **How to Solve:** 
  1. Maintain a state mapping for all nodes (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `SKIPPED`).
  2. During the boot sequence, if a service randomly or deliberately fails, mark it `FAILED`.
  3. Execute a localized BFS/DFS starting from the `FAILED` node to mark all reachable downstream descendants as `SKIPPED`.

---

## 3. OS Modules: Analysis & Solution Strategy

### B1. Multithreaded Job Simulation
- **How to Solve:** Use Python's `threading` and `queue` modules. 
- Instead of a simple loop (tick-based), each network task (Backup, OS Update) will be spawned as a concurrent `Thread`. 
- A central **Dispatcher/Scheduler Thread** will manage CPU/Bandwidth allocations by using `threading.Event` or `threading.Condition` primitives to pause/resume worker threads.

### B2. Preemptive Priority Scheduling & Context Switching
- **How to Solve:** 
  1. The Ready Queue is implemented as a Priority Queue (heapq).
  2. When a high-priority task arrives, the Dispatcher checks the currently running tasks.
  3. If all slots are full and a running task has lower priority, the Dispatcher signals the lower-priority thread to pause (context switch).
  4. The preempted task's state is saved, and the high-priority task's thread is signaled to start/resume. Logs will capture the exact timestamps of these switches.

### B3 & B4. Starvation Demonstration and Aging Algorithm
- **Starvation:** A scenario where continuous high-priority tasks (e.g., Video Streams) prevent low-priority tasks (e.g., Backups) from ever acquiring bandwidth.
- **Aging Solution:**
  1. A background thread (or the Dispatcher) periodically checks the wait time of all tasks in the Ready Queue.
  2. Every $X$ seconds (aging factor), the priority integer of waiting tasks is increased.
  3. The Priority Queue is re-sorted. Eventually, the starved task outranks new tasks and gets executed.

### B5. Time-of-Day Scheduling
- **How to Solve:** 
  1. Introduce a global `SimulationClock` with states like `PEAK_HOURS` and `NIGHT_HOURS`.
  2. The Scheduler consults this clock when evaluating priorities.
  3. **Peak Hours:** Base priorities of "User Traffic" / "DNS" are inflated.
  4. **Night Hours:** Base priorities of "Backups" / "Data Sync" are inflated.
  5. The queue re-evaluates task rankings immediately upon a Time-of-Day phase shift.

---

## 4. Frontend Architecture (Streamlit)

- **Dependency Graph:** Rendered using `networkx` and `plotly` or `matplotlib` for interactive node inspection. FAILED/SKIPPED nodes will be color-coded red/gray.
- **Boot Logs:** A dynamic `st.empty()` or text box that appends multithreaded log output (timestamps + context switch events).
- **Scheduler Timeline (Gantt):** Use `plotly.express.timeline` to display thread start, pause (preemption), resume, and completion times.
- **Queue Monitor:** Live metric cards showing counts of Ready, Running, and Waiting queues.

---

## 5. Git Strategy
To ensure a zero-merge conflict environment:
- `main`: Production-ready code only.
- `dev`: Integration branch.
- Feature branches (`feature/sequencer`, `feature/scheduler`, `feature/ui`) mapped exactly to the directory structure. Developers only modify files inside their assigned domain.
- Strictly pull `dev` before creating PRs or pushing.
