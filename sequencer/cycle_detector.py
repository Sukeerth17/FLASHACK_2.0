from typing import Dict, List, Optional, Set

class CycleDetector:
    def __init__(self, adj_list: Dict[str, List[str]]):
        self.adj_list = adj_list
        # Colors: 0 = White (unvisited), 1 = Gray (visiting), 2 = Black (visited)
        self.colors: Dict[str, int] = {node: 0 for node in adj_list}
        self.parent: Dict[str, Optional[str]] = {node: None for node in adj_list}
        self.cycle_path: List[str] = []

    def has_cycle(self) -> bool:
        """
        Runs the color-based DFS to detect cycles.
        Returns:
            True if a cycle exists, False otherwise.
        """
        self.colors = {node: 0 for node in self.adj_list}
        self.parent = {node: None for node in self.adj_list}
        self.cycle_path = []

        for node in self.adj_list:
            if self.colors[node] == 0:
                if self._dfs_visit(node):
                    return True
        return False

    def _dfs_visit(self, u: str) -> bool:
        self.colors[u] = 1  # Gray (currently visiting)

        for v in self.adj_list.get(u, []):
            if self.colors[v] == 1:
                # Cycle found! Reconstruct cycle path
                self.cycle_path = [v]
                curr = u
                while curr != v and curr is not None:
                    self.cycle_path.append(curr)
                    curr = self.parent[curr]
                self.cycle_path.append(v)
                self.cycle_path.reverse()
                return True
            elif self.colors[v] == 0:
                self.parent[v] = u
                if self._dfs_visit(v):
                    return True

        self.colors[u] = 2  # Black (finished visiting)
        return False

    def get_cycle_path(self) -> List[str]:
        """Returns the node path forming the cycle if one was detected."""
        return self.cycle_path
