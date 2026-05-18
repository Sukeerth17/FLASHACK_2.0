import json
from typing import Dict, List, Set, Tuple

class GraphBuilder:
    def __init__(self):
        # adj_list: task_id -> list of successor task_ids (children)
        self.adj_list: Dict[str, List[str]] = {}
        # rev_adj_list: task_id -> list of predecessor task_ids (parents)
        self.rev_adj_list: Dict[str, List[str]] = {}
        self.nodes: Dict[str, dict] = {}

    def build_graph(self, jobs_data: List[dict]) -> Tuple[Dict[str, List[str]], Dict[str, dict]]:
        """
        Builds dependency graph representations from raw JSON list.
        Returns:
            - adj_list: task_id -> list of child/dependent task_ids
            - nodes: task_id -> task config dict
        """
        self.nodes = {job["id"]: job for job in jobs_data}
        self.adj_list = {job_id: [] for job_id in self.nodes}
        self.rev_adj_list = {job_id: [] for job_id in self.nodes}

        for job_id, job in self.nodes.items():
            dependencies = job.get("dependencies", [])
            for dep in dependencies:
                if dep not in self.nodes:
                    raise ValueError(
                        f"Task '{job_id}' depends on missing task '{dep}'."
                    )
                # dep must execute before job_id.
                # So dep -> job_id in dependency graph
                self.adj_list[dep].append(job_id)
                self.rev_adj_list[job_id].append(dep)

        return self.adj_list, self.nodes

    def get_predecessors(self, node_id: str) -> List[str]:
        return self.rev_adj_list.get(node_id, [])

    def get_successors(self, node_id: str) -> List[str]:
        return self.adj_list.get(node_id, [])

    def get_in_degrees(self) -> Dict[str, int]:
        return {node_id: len(parents) for node_id, parents in self.rev_adj_list.items()}
