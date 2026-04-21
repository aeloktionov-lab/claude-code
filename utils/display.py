from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box

console = Console()


def print_banner(company: str) -> None:
    console.print(Panel(
        f"[bold cyan]{company}[/bold cyan] [white]— Система оркестрации ИИ-агентов[/white]\n"
        "[dim]Поиск заказов · Обработка заявок · Оптимизация · КП · Удержание клиентов[/dim]",
        border_style="cyan",
        expand=False,
    ))


def print_agent_header(name: str) -> None:
    console.print()
    console.print(Rule(f"[bold yellow]Агент: {name}[/bold yellow]", style="yellow"))


def print_agent_result(data: dict) -> None:
    if not data:
        return
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("Ключ", style="green", no_wrap=True)
    table.add_column("Значение", style="white")
    for k, v in data.items():
        if isinstance(v, list):
            v = "\n".join(f"• {i}" for i in v)
        elif isinstance(v, dict):
            v = "\n".join(f"{dk}: {dv}" for dk, dv in v.items())
        table.add_row(str(k), str(v))
    console.print(table)


def print_section(title: str, content: str) -> None:
    console.print(Panel(content, title=f"[bold]{title}[/bold]", border_style="blue"))


def print_success(msg: str) -> None:
    console.print(f"\n[bold green]✓ {msg}[/bold green]")


def print_error(msg: str) -> None:
    console.print(f"\n[bold red]✗ {msg}[/bold red]")


def print_info(msg: str) -> None:
    console.print(f"[dim]{msg}[/dim]")
