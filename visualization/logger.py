from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

class PacketPathLogger:
    @staticmethod
    def log(message: str, level: str = "INFO", color: Optional[str] = None):
        """Prints a styled and colored log line, falling back gracefully if Rich is not installed."""
        if HAS_RICH:
            if color == "green" or level == "SUCCESS":
                style = "bold green"
            elif color == "blue" or level == "INFO":
                style = "bold blue"
            elif color == "cyan" or level == "DEBUG":
                style = "bold cyan"
            elif color == "yellow" or level == "WARNING":
                style = "bold yellow"
            elif color == "red" or level == "ERROR":
                style = "bold red"
            elif color == "magenta" or level == "HEADER":
                style = "bold magenta"
            else:
                style = "white"

            prefix = f"[{level}]"
            console.print(f"[{style}]{prefix:<10}[/{style}] {message}")
        else:
            print(f"[{level:<10}] {message}")

    @staticmethod
    def success(message: str):
        PacketPathLogger.log(message, "SUCCESS", "green")

    @staticmethod
    def info(message: str):
        PacketPathLogger.log(message, "INFO", "blue")

    @staticmethod
    def warning(message: str):
        PacketPathLogger.log(message, "WARNING", "yellow")

    @staticmethod
    def error(message: str):
        PacketPathLogger.log(message, "ERROR", "red")

    @staticmethod
    def debug(message: str):
        PacketPathLogger.log(message, "DEBUG", "cyan")

    @staticmethod
    def banner(title: str):
        """Prints a beautiful block banner, falling back gracefully if Rich is not installed."""
        if HAS_RICH:
            console.print(Panel(Text(title, justify="center", style="bold magenta"), border_style="magenta", padding=(1, 2)))
        else:
            print(f"\n{'='*60}\n{title.center(60)}\n{'='*60}\n")
