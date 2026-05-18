from typing import Dict, List, Set

class TopologicalSorter:
    def __init__(self, adj_list: Dict[str, List[str]], in_degrees: Dict[str, int] = None):
        self.adj_list = adj_list
        self.nodes = list(adj_list.keys())

    def sort(self) -> List[str]:
        """
        Performs a Recursive DFS to obtain a topological order.
        Time Complexity: O(V + E)
        Space Complexity: O(V)
        Raises:
            ValueError: If there is a circular dependency in the graph.
        """
        visited: Set[str] = set()
        visiting: Set[str] = set()
        stack: List[str] = []

        # Sort nodes for deterministic sorting
        self.nodes.sort()

        def dfs(node: str):
            if node in visiting:
                raise ValueError(f"Graph contains a cycle involving node '{node}'")
            if node in visited:
                return

            visiting.add(node)

            # Process all successors
            successors = sorted(self.adj_list.get(node, []))
            for neighbor in successors:
                dfs(neighbor)

            visiting.remove(node)
            visited.add(node)
            stack.append(node)

        for n in self.nodes:
            if n not in visited:
                dfs(n)

        # In adj_list, edges are Dependency -> Task.
        # DFS pushes Task first, then Dependency. Reversing gives correct boot order.
        stack.reverse()
        return stack
