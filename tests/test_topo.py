import pytest
from sequencer.graph_builder import GraphBuilder
from sequencer.cycle_detector import CycleDetector
from sequencer.topo_sort import TopologicalSorter
from sequencer.critical_handler import CriticalPathHandler
from shared.constants import TaskState

def test_graph_building_and_topo_sort():
    # Setup simple job structures
    jobs = [
        {"id": "A", "name": "Task A", "duration": 3, "dependencies": []},
        {"id": "B", "name": "Task B", "duration": 2, "dependencies": ["A"]},
        {"id": "C", "name": "Task C", "duration": 4, "dependencies": ["A"]},
        {"id": "D", "name": "Task D", "duration": 1, "dependencies": ["B", "C"]}
    ]
    
    builder = GraphBuilder()
    adj_list, nodes = builder.build_graph(jobs)
    
    # Assert nodes and structures
    assert "A" in nodes
    assert len(adj_list["A"]) == 2  # A has children B and C
    assert "D" in adj_list["B"]
    
    # Check cycle detection
    detector = CycleDetector(adj_list)
    assert not detector.has_cycle()
    
    # Check topo sort (DFS)
    sorter = TopologicalSorter(adj_list)
    order = sorter.sort()
    # A must boot before B and C. B and C must boot before D.
    assert order.index("A") < order.index("B")
    assert order.index("A") < order.index("C")
    assert order.index("B") < order.index("D")
    assert order.index("C") < order.index("D")

def test_cycle_detection():
    # Setup cyclic structures
    cyclic_jobs = [
        {"id": "A", "name": "Task A", "duration": 3, "dependencies": ["C"]},
        {"id": "B", "name": "Task B", "duration": 2, "dependencies": ["A"]},
        {"id": "C", "name": "Task C", "duration": 4, "dependencies": ["B"]}
    ]
    
    builder = GraphBuilder()
    adj_list, nodes = builder.build_graph(cyclic_jobs)
    
    detector = CycleDetector(adj_list)
    assert detector.has_cycle()
    
    cycle_path = detector.get_cycle_path()
    assert "A" in cycle_path
    assert "B" in cycle_path
    assert "C" in cycle_path

def test_failure_propagation():
    jobs = [
        {"id": "A", "name": "Task A", "dependencies": []},
        {"id": "B", "name": "Task B", "dependencies": ["A"]},
        {"id": "C", "name": "Task C", "dependencies": ["B"]}
    ]
    
    builder = GraphBuilder()
    adj_list, nodes = builder.build_graph(jobs)
    sorter = TopologicalSorter(adj_list)
    order = sorter.sort()
    
    critical_handler = CriticalPathHandler(adj_list, nodes, order)
    
    # Simulate A Fails
    states = {
        "A": TaskState.READY,
        "B": TaskState.PENDING,
        "C": TaskState.PENDING
    }
    
    skipped = critical_handler.propagate_failure("A", states)
    assert "B" in skipped
    assert "C" in skipped
    assert states["A"] == TaskState.FAILED
    assert states["B"] == TaskState.SKIPPED
    assert states["C"] == TaskState.SKIPPED
