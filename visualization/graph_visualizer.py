import os
from typing import Dict, List, Tuple, Optional
from shared.constants import Priority

# Try loading networkx and matplotlib for graphical plots
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    HAS_GRAPHICS = True
except ImportError:
    HAS_GRAPHICS = False

class GraphVisualizer:
    def __init__(self, adj_list: Dict[str, List[str]], nodes: Dict[str, dict]):
        self.adj_list = adj_list
        self.nodes = nodes

    def plot_graph_graphical(self, critical_path: Optional[List[str]] = None, output_path: str = "dependency_graph.png") -> Optional[object]:
        """
        Creates a high-quality visualization of the dependency DAG using Matplotlib.
        Nodes are colored by priority; edges on the critical path are highlighted.
        Returns:
            Matplotlib Figure object or None.
        """
        if not HAS_GRAPHICS:
            return None

        # Build NetworkX Directed Graph
        G = nx.DiGraph()
        
        # Add nodes with metadata
        for node_id, node in self.nodes.items():
            G.add_node(
                node_id, 
                name=node["name"],
                priority=node.get("priority", "MEDIUM"),
                duration=node.get("duration", 1)
            )

        # Add edges
        for u, successors in self.adj_list.items():
            for v in successors:
                G.add_edge(u, v)

        # Set up node colors based on priority
        color_map = {
            "LOW": "#a8dadc",       # Soft teal
            "MEDIUM": "#457b9d",    # Soft blue
            "HIGH": "#f4a261",      # Muted orange
            "CRITICAL": "#e63946"  # Vibrant red
        }
        
        node_colors = []
        node_labels = {}
        for n in G.nodes():
            pri = G.nodes[n]["priority"]
            node_colors.append(color_map.get(pri, "#cccccc"))
            
            dur = G.nodes[n]["duration"]
            node_labels[n] = f"{n}\n({dur} ticks)"

        # Highlight critical path edges
        edge_colors = []
        edge_widths = []
        critical_edges = set()
        if critical_path:
            for i in range(len(critical_path) - 1):
                critical_edges.add((critical_path[i], critical_path[i+1]))

        for u, v in G.edges():
            if (u, v) in critical_edges:
                edge_colors.append("#e63946")  # Critical path is highlighted red
                edge_widths.append(3.0)
            else:
                edge_colors.append("#2b2d42")  # Normal path is dark grey
                edge_widths.append(1.2)

        # Set up figure
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.patch.set_facecolor('#f8f9fa')
        ax.set_facecolor('#f8f9fa')

        # Graph layout (spring or planar/shell depending on graph structure)
        try:
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot') # prefers graphviz
        except Exception:
            pos = nx.spring_layout(G, seed=42, k=1.5)  # fallback layout

        # Draw network components
        nx.draw_networkx_nodes(
            G, pos, 
            node_color=node_colors, 
            node_size=1600, 
            edgecolors="#2b2d42", 
            linewidths=1.5,
            ax=ax
        )
        
        nx.draw_networkx_edges(
            G, pos, 
            edge_color=edge_colors, 
            width=edge_widths,
            arrowsize=20, 
            arrowstyle="->",
            connectionstyle="arc3,rad=0.15",
            ax=ax
        )
        
        nx.draw_networkx_labels(
            G, pos, 
            labels=node_labels, 
            font_size=8, 
            font_weight="bold",
            font_color="#2b2d42",
            ax=ax
        )

        plt.title("Task Dependency Graph (DAG) & Critical Path Highlight", fontsize=14, fontweight="bold", pad=20)
        plt.tight_layout()
        
        # Save file
        try:
            plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
        except Exception:
            pass

        return fig

    def plot_graph_text(self, critical_path: Optional[List[str]] = None):
        """
        Prints a text-based ASCII structure of the DAG to the standard output.
        """
        print("\n" + "=" * 50)
        print("         TEXT-BASED GRAPH DEPENDENCY VIEW")
        print("=" * 50)
        
        # Calculate in-degree to find sources
        in_degrees = {node: 0 for node in self.adj_list}
        for u, successors in self.adj_list.items():
            for v in successors:
                in_degrees[v] = in_degrees.get(v, 0) + 1

        sources = [node for node, deg in in_degrees.items() if deg == 0]
        
        def print_node_recursive(node_id: str, prefix: str = "", is_last: bool = True):
            node = self.nodes[node_id]
            dur = node.get("duration", 1)
            pri = node.get("priority", "MEDIUM")
            crit_marker = " *CRITICAL PATH*" if critical_path and node_id in critical_path else ""
            
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{node_id} ({dur}t, Priority: {pri}){crit_marker}")
            
            successors = self.adj_list.get(node_id, [])
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            for idx, succ in enumerate(successors):
                last_succ = (idx == len(successors) - 1)
                print_node_recursive(succ, new_prefix, last_succ)

        for idx, src in enumerate(sources):
            last_src = (idx == len(sources) - 1)
            print_node_recursive(src, "", last_src)
            
        print("=" * 50 + "\n")
