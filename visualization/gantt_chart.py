import os
from typing import List, Dict, Any, Optional

try:
    import pandas as pd
    import plotly.express as px
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_GRAPHICS = True
except ImportError:
    HAS_GRAPHICS = False

class GanttChartGenerator:
    def __init__(self, task_summaries: List[Dict[str, Any]]):
        self.task_summaries = task_summaries

    def generate_plotly_chart(self, output_path: str = "gantt_chart.html") -> Optional[object]:
        """
        Creates an interactive, beautiful HTML-based Gantt chart using Plotly.
        """
        if not HAS_GRAPHICS:
            return None

        # Build records with mock dates (since Plotly timeline requires datetime fields)
        records = []
        base_time = pd.Timestamp("2026-05-18 00:00:00")
        
        for task in self.task_summaries:
            start_tick = float(task["start"] if task["start"] is not None else 0.0)
            end_tick = float(task["end"] if task["end"] is not None else start_tick + task["duration"])
            
            # Map tick values to minute offsets
            start_time = base_time + pd.Timedelta(minutes=start_tick)
            end_time = base_time + pd.Timedelta(minutes=end_tick)

            records.append({
                "Task": task["id"],
                "Label": task["name"],
                "Start": start_time,
                "Finish": end_time,
                "Service": task["service"] or "Unassigned",
                "Priority": task["priority"],
                "Duration": task["duration"],
                "Wait Time": task["wait_time"]
            })

        df = pd.DataFrame(records)
        
        # Draw Plotly timeline
        fig = px.timeline(
            df, 
            x_start="Start", 
            x_end="Finish", 
            y="Task", 
            color="Service",
            title="PacketPath Schedule Timeline (Gantt Chart)",
            hover_data=["Label", "Priority", "Duration", "Wait Time"]
        )
        
        # Configure aesthetics
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            plot_bgcolor="#f8f9fa",
            paper_bgcolor="#f8f9fa",
            title_font=dict(size=18, family="Arial", color="#2b2d42"),
            xaxis_title="Time Scale (Simulation Ticks)",
            yaxis_title="Tasks"
        )
        
        # Make the x-axis display custom tick values (0, 1, 2...) instead of standard datetimes
        fig.update_xaxes(
            tickformat="%M",  # displays only minutes
            title_text="Simulation Ticks (minutes)"
        )
        
        try:
            fig.write_html(output_path)
        except Exception:
            pass

        return fig

    def generate_matplotlib_chart(self, output_path: str = "gantt_chart.png") -> Optional[object]:
        """
        Creates a high-resolution static Gantt chart image.
        """
        if not HAS_GRAPHICS:
            return None

        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#f8f9fa')
        ax.set_facecolor('#f8f9fa')

        # Create distinct color palettes for service nodes
        service_colors = {}
        colors_palette = ["#457b9d", "#e63946", "#f4a261", "#2a9d8f", "#9b5de5"]
        
        y_labels = []
        for idx, task in enumerate(self.task_summaries):
            start = float(task["start"] if task["start"] is not None else 0.0)
            dur = float(task["duration"])
            srv = task["service"] or "Unassigned"
            
            if srv not in service_colors:
                color_idx = len(service_colors) % len(colors_palette)
                service_colors[srv] = colors_palette[color_idx]
                
            color = service_colors[srv]
            ax.barh(idx, dur, left=start, align='center', color=color, edgecolor='#2b2d42', height=0.6, alpha=0.9)
            
            # Text display inside/outside the bars
            ax.text(start + (dur / 2), idx, f"{dur:.1f}t", ha='center', va='center', color='white', fontweight='bold', fontsize=8)
            
            y_labels.append(task["id"])

        ax.set_yticks(range(len(self.task_summaries)))
        ax.set_yticklabels(y_labels, fontsize=9, fontweight='bold', color='#2b2d42')
        ax.invert_yaxis()  # top-down task flow

        # Grid lines and formatting
        ax.grid(axis='x', linestyle='--', alpha=0.5, color='#ccc')
        ax.set_xlabel('Simulation Ticks', fontsize=11, fontweight='bold', color='#2b2d42', labelpad=10)
        ax.set_title('Schedule Timeline Execution (Gantt Chart)', fontsize=14, fontweight='bold', color='#2b2d42', pad=15)
        
        # Legend construction
        legend_patches = [
            mpatches.Patch(color=color, label=srv)
            for srv, color in service_colors.items()
        ]
        ax.legend(handles=legend_patches, title="Service Allocations", loc="best")
        
        plt.tight_layout()
        try:
            plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
        except Exception:
            pass

        return fig

    def render_ascii_timeline(self):
        """
        Prints an eye-catching character-based ASCII visual representation of the schedule timeline.
        Upgraded to use Rich Library tables.
        """
        from rich.console import Console
        from rich.table import Table
        from rich import box

        console = Console()
        
        max_tick = 0.0
        for task in self.task_summaries:
            end = float(task["end"] if task["end"] is not None else 0.0)
            max_tick = max(max_tick, end)
        
        # Ensure scale makes sense
        scale_ticks = max(max_tick, 10.0)
        
        table = Table(title="PACKETPATH SIMULATION SCHEDULE", box=box.ROUNDED, header_style="bold cyan", expand=True)
        table.add_column("Task ID", width=25)
        table.add_column("Interval", width=15, justify="center")
        table.add_column(f"Timeline (0 to {scale_ticks:.1f} ticks)", width=35)
        table.add_column("Service", width=25)

        for task in self.task_summaries:
            start = float(task["start"] if task["start"] is not None else 0.0)
            end = float(task["end"] if task["end"] is not None else start + float(task["duration"]))
            dur = float(task["duration"])
            srv = str(task["service"] or "None")
            
            # Map task times to discrete block indexes
            width = 30
            block_start = int((start / scale_ticks) * width) if scale_ticks > 0 else 0
            block_len = int((dur / scale_ticks) * width) if scale_ticks > 0 else 1
            block_len = max(block_len, 1)  # ensure at least one block is displayed
            
            blocks = [" "] * width
            for i in range(block_start, min(block_start + block_len, width)):
                blocks[i] = "█"
                
            timeline_str = "".join(blocks)
            time_interval = f"{start:4.1f} - {end:4.1f}"
            
            # Color coding based on priority string
            pri = task.get("priority", "MEDIUM")
            if pri == "LOW":
                color = "green"
            elif pri == "CRITICAL":
                color = "red"
            else:
                color = "yellow"
            
            table.add_row(
                f"[bold {color}]{task['id']}[/bold {color}]",
                time_interval,
                f"[magenta][{timeline_str}][/magenta]",
                srv
            )
            
        console.print(table)
        print("\n")
