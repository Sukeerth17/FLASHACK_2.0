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
        if not HAS_GRAPHICS: return None
        records = []
        base_time = pd.Timestamp("2026-05-18 00:00:00")
        for task in self.task_summaries:
            start_tick = float(task["start"] if task["start"] is not None else 0.0)
            end_tick = float(task["end"] if task["end"] is not None else start_tick + task["duration"])
            start_time = base_time + pd.Timedelta(minutes=start_tick)
            end_time = base_time + pd.Timedelta(minutes=end_tick)
            records.append({
                "Task": task["id"], "Label": task["name"], "Start": start_time,
                "Finish": end_time, "Service": task["service"] or "Unassigned",
                "Priority": task["priority"], "Duration": task["duration"], "Wait Time": task["wait_time"]
            })
        df = pd.DataFrame(records)
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Service")
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(tickformat="%M", title_text="Simulation Ticks")
        try: fig.write_html(output_path)
        except Exception: pass
        return fig

    def generate_matplotlib_chart(self, output_path: str = "gantt_chart.png") -> Optional[object]:
        if not HAS_GRAPHICS: return None
        fig, ax = plt.subplots(figsize=(10, 6))
        service_colors = {}
        colors_palette = ["#457b9d", "#e63946", "#f4a261", "#2a9d8f", "#9b5de5"]
        y_labels = []
        for idx, task in enumerate(self.task_summaries):
            start = float(task["start"] if task["start"] is not None else 0.0)
            dur = float(task["duration"])
            srv = task["service"] or "Unassigned"
            if srv not in service_colors: service_colors[srv] = colors_palette[len(service_colors) % len(colors_palette)]
            ax.barh(idx, dur, left=start, align='center', color=service_colors[srv])
            y_labels.append(task["id"])
        ax.set_yticks(range(len(self.task_summaries)))
        ax.set_yticklabels(y_labels)
        ax.invert_yaxis()
        plt.tight_layout()
        try: plt.savefig(output_path, dpi=300)
        except Exception: pass
        return fig

    def render_ascii_timeline(self):
        """Prints the schedule timeline, falling back to basic ASCII if Rich is missing."""
        max_tick = 0.0
        for task in self.task_summaries:
            end = float(task["end"] if task["end"] is not None else 0.0)
            max_tick = max(max_tick, end)
        scale_ticks = max(max_tick, 10.0)

        try:
            from rich.console import Console
            from rich.table import Table
            from rich import box
            HAS_RICH = True
            console = Console()
        except ImportError:
            HAS_RICH = False

        if HAS_RICH:
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
                
                width = 30
                block_start = int((start / scale_ticks) * width) if scale_ticks > 0 else 0
                block_len = max(int((dur / scale_ticks) * width) if scale_ticks > 0 else 1, 1)
                
                blocks = [" "] * width
                for i in range(block_start, min(block_start + block_len, width)): blocks[i] = "█"
                
                pri = task.get("priority", "MEDIUM")
                color = "green" if pri == "LOW" else "red" if pri == "CRITICAL" else "yellow"
                table.add_row(
                    f"[bold {color}]{task['id']}[/bold {color}]",
                    f"{start:4.1f} - {end:4.1f}",
                    f"[magenta][{''.join(blocks)}][/magenta]",
                    srv
                )
            console.print(table)
            print("\n")
        else:
            # Fallback basic ASCII
            print("\n" + "="*65)
            print("          PACKETPATH ASCII SIMULATION SCHEDULE")
            print("="*65)
            print(f"{'Task ID':<25} | Timeline (0 to {scale_ticks:.1f} ticks)")
            print("-" * 65)
            for task in self.task_summaries:
                start = float(task["start"] if task["start"] is not None else 0.0)
                dur = float(task["duration"])
                width = 40
                block_start = int((start / scale_ticks) * width) if scale_ticks > 0 else 0
                block_len = max(int((dur / scale_ticks) * width) if scale_ticks > 0 else 1, 1)
                blocks = [" "] * width
                for i in range(block_start, min(block_start + block_len, width)): blocks[i] = "█"
                print(f"{task['id']:<25} | [{''.join(blocks)}]")
            print("=" * 65 + "\n")
