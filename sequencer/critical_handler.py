from typing import Dict, List, Tuple, Optional, Set
from shared.constants import TaskState

class CriticalPathHandler:
    def __init__(self, adj_list: Dict[str, List[str]], nodes: Dict[str, dict], topo_order: List[str]):
        self.adj_list = adj_list
        self.nodes = nodes
        self.topo_order = topo_order

    def find_critical_path(self) -> Tuple[List[str], int]:
        """
        Calculates the longest path in terms of execution duration in the DAG using Dynamic Programming.
        """
        if not self.topo_order:
            return [], 0

        dist: Dict[str, int] = {}
        parent: Dict[str, Optional[str]] = {}

        for node_id in self.topo_order:
            duration = self.nodes[node_id].get("duration", 1)
            dist[node_id] = duration
            parent[node_id] = None

        for u in self.topo_order:
            for v in self.adj_list.get(u, []):
                v_duration = self.nodes[v].get("duration", 1)
                if dist[u] + v_duration > dist[v]:
                    dist[v] = dist[u] + v_duration
                    parent[v] = u

        if not dist:
            return [], 0

        end_node = max(dist, key=lambda k: dist[k])
        max_duration = dist[end_node]

        path = []
        curr: Optional[str] = end_node
        while curr is not None:
            path.append(curr)
            curr = parent[curr]

        path.reverse()
        return path, max_duration

    def propagate_failure(self, failed_node: str, node_states: Dict[str, TaskState]) -> List[str]:
        """
        Executes a localized BFS starting from the FAILED node to mark all reachable 
        downstream descendants as SKIPPED. Returns list of skipped nodes.
        """
        if failed_node not in self.nodes:
            return []
            
        skipped_nodes = []
        queue = [failed_node]
        visited = set([failed_node])
        
        node_states[failed_node] = TaskState.FAILED
        
        while queue:
            current = queue.pop(0)
            
            for neighbor in self.adj_list.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    if node_states.get(neighbor) != TaskState.SKIPPED:
                        node_states[neighbor] = TaskState.SKIPPED
                        skipped_nodes.append(neighbor)
                        
        return skipped_nodes
