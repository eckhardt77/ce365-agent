from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt
from rich import box
import json


class RichConsole:
    """Rich Console für Terminal UI"""

    def __init__(self):
        self.console = Console()

    def display_logo(self):
        """ASCII Art Logo anzeigen"""
        logo = """
╔════════════════════════════════════════╗
║                                        ║
║       🔧 TechCare Bot v0.1.0 🔧       ║
║                                        ║
║   IT-Wartungs-Assistent für            ║
║   Windows & macOS Systeme              ║
║                                        ║
╚════════════════════════════════════════╝
"""
        self.console.print(logo, style="bold cyan")
        self.console.print(
            "Workflow: [yellow]Audit → Analyse → Plan → GO REPAIR → Ausführung[/yellow]"
        )
        self.console.print()

    def display_assistant_message(self, text: str):
        """Assistant-Nachricht mit Markdown anzeigen"""
        md = Markdown(text)
        panel = Panel(
            md,
            title="🤖 TechCare",
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        self.console.print(panel)

    def display_tool_call(self, tool_name: str, tool_input: dict):
        """Tool Call anzeigen"""
        input_json = json.dumps(tool_input, indent=2)
        syntax = Syntax(input_json, "json", theme="monokai", line_numbers=False)

        self.console.print()
        self.console.print(f"[bold yellow]🔧 Tool:[/bold yellow] {tool_name}")
        self.console.print("[bold yellow]📥 Input:[/bold yellow]")
        self.console.print(syntax)

    def display_tool_result(self, tool_name: str, result: str, success: bool = True):
        """Tool Result anzeigen"""
        status = "✓" if success else "✗"
        color = "green" if success else "red"

        self.console.print(
            f"[bold {color}]{status} Result:[/bold {color}]",
        )
        self.console.print(Panel(result, border_style=color, box=box.ROUNDED))
        self.console.print()

    def display_error(self, error: str):
        """Fehler anzeigen"""
        self.console.print(
            Panel(
                error,
                title="❌ Error",
                border_style="red",
                box=box.ROUNDED,
            )
        )

    def display_info(self, message: str):
        """Info-Nachricht anzeigen"""
        self.console.print(f"[cyan]ℹ️  {message}[/cyan]")

    def display_warning(self, message: str):
        """Warnung anzeigen"""
        self.console.print(f"[yellow]⚠️  {message}[/yellow]")

    def display_success(self, message: str):
        """Erfolgs-Nachricht anzeigen"""
        self.console.print(f"[green]✓ {message}[/green]")

    def get_input(self) -> str:
        """User Input holen"""
        self.console.print()
        return Prompt.ask("[bold green]You[/bold green]").strip()

    def display_separator(self):
        """Separator-Linie anzeigen"""
        self.console.print("─" * 80, style="dim")

    def clear(self):
        """Console clearen"""
        self.console.clear()

    def display_known_solution(self, case_data: dict, similarity: float):
        """
        Bekannte Lösung anzeigen

        Args:
            case_data: Dict mit Problem, Root Cause, Lösung, etc.
            similarity: Ähnlichkeits-Score (0.0-1.0)
        """
        similarity_pct = similarity * 100

        content = f"""
🎯 **BEKANNTES PROBLEM ERKANNT!**

**Ähnlichkeit:** {similarity_pct:.0f}%

**Problem:** {case_data.get('problem_description', 'N/A')[:200]}

**Root Cause:** {case_data.get('root_cause', 'N/A')}

**Bewährte Lösung:**
{case_data.get('solution_plan', 'N/A')[:500]}

**Statistik:**
✓ Bereits {case_data.get('reuse_count', 0)} Mal erfolgreich angewendet
✓ Erfolgsquote: {case_data.get('success_rate', 0) * 100:.0f}%

---

**Möchtest du diese Lösung verwenden?**

**1.** Ja, bewährte Lösung verwenden (schneller, ~2-5 Min)
**2.** Nein, vollständigen Audit durchführen (gründlicher, ~10 Min)

Bitte antworte mit **"1"** oder **"2"**.
"""

        panel = Panel(
            Markdown(content),
            title="💡 Smart Learning",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2)
        )

        self.console.print(panel)

    def display_learning_stats(self, stats: dict):
        """Learning-Statistiken anzeigen"""
        content = f"""
📊 **LEARNING SYSTEM STATISTIK**

**Gespeicherte Fälle:** {stats.get('total_cases', 0)}
**Erfolgreiche Lösungen:** {stats.get('successful_cases', 0)}
**Wiederverwendungen:** {stats.get('total_reuses', 0)}
**Durchschnittliche Erfolgsquote:** {stats.get('avg_success_rate', 0) * 100:.0f}%

**OS-Verteilung:**
"""

        for os_type, count in stats.get('os_distribution', {}).items():
            content += f"  • {os_type}: {count} Fälle\n"

        if stats.get('top_solutions'):
            content += "\n**🏆 Top 5 Lösungen:**\n"
            for i, solution in enumerate(stats['top_solutions'], 1):
                content += f"{i}. {solution['problem']}...\n"
                content += f"   ({solution['reuse_count']}x, {solution['success_rate']*100:.0f}%)\n"

        panel = Panel(
            Markdown(content),
            title="📊 Learning Statistics",
            border_style="cyan",
            box=box.ROUNDED
        )

        self.console.print(panel)
