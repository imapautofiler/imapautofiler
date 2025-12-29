#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""User interface components for interactive mode."""

import logging
import signal
import sys
import time
import types
from typing import Any, Callable

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text

RICH_AVAILABLE = True


# Color scheme for consistent theming
class Colors:
    """Color scheme constants for the UI."""

    PANEL_TITLE = "bold blue"
    PANEL_BORDER = "blue"
    PROGRESS_TEXT = "green"
    METRIC_LABEL = "red"
    ERROR_VALUE = "red"
    INTERRUPT_TEXT = "bold red"
    # All other text uses default terminal color for adaptability


class ProgressTracker:
    """Tracks progress for mailbox processing with fallback for environments without rich."""

    def __init__(self, interactive: bool = False, quiet: bool = False) -> None:
        self.interactive = interactive
        self.quiet = quiet
        self._console: Console | None = None
        self._progress: Progress | None = None
        self._live: Live | None = None
        self._layout: Layout | None = None
        self._overall_task: TaskID | None = None
        self._mailbox_task: TaskID | None = None

        # Statistics tracking
        self._stats = {
            "total_messages": 0,
            "seen": 0,
            "processed": 0,
            "moved": 0,
            "deleted": 0,
            "flagged": 0,
            "errors": 0,
            "total_mailboxes_overall": 0,
            "completed_mailboxes": 0,
        }
        self._current_subject: str = ""
        self._current_from: str = ""
        self._current_to: str = ""
        self._current_mailbox: str = ""
        self._start_time: float | None = None
        self._interrupted: bool = False
        self._original_sigint_handler: (Callable[[int, Any], Any] | int) | None = None

        # Recent actions tracking (most recent first)
        self._recent_actions: list[str] = []
        self._max_actions = (
            self._calculate_max_actions()
        )  # Dynamic based on terminal height

        if self.interactive:
            self._console = Console()
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=self._console,
                expand=True,
            )

            # Create the progress tasks upfront
            self._overall_task = self._progress.add_task(
                f"[{Colors.PROGRESS_TEXT}]Initializing...", total=1
            )
            self._mailbox_task = self._progress.add_task("📁 Waiting...", total=1)

            # Create layout for multi-component display
            self._layout = Layout()
            self._layout.split_column(
                Layout(name="progress", size=4),
                Layout(name="stats", size=11),
                Layout(name="current", size=5),
                Layout(name="actions"),  # Dynamic size - takes remaining space
            )

    def _calculate_max_actions(self) -> int:
        """Calculate maximum actions to display based on terminal height."""
        try:
            console = Console()
            terminal_height = console.size.height
            # Reserve space for: progress (4) + stats (11) + current (5) + borders/padding (~5) = 25
            # Use remaining space for actions, with minimum of 5 and maximum of 20
            available_height = terminal_height - 25
            return max(5, min(20, available_height))
        except Exception:
            return 10  # Fallback if size detection fails

    def _handle_interrupt(self, signum: int, frame: types.FrameType | None) -> None:
        """Handle Ctrl+C interruption gracefully."""
        self._interrupted = True
        if self.interactive and self._console:
            self._console.print(
                f"\n\n⚠️  [{Colors.INTERRUPT_TEXT}]Interrupt received[/]. Processing will stop after current message...\n"
            )

    def start(self) -> None:
        """Start the progress tracking."""
        self._start_time = time.time()

        # Set up interrupt handler for graceful shutdown
        if self.interactive:
            self._original_sigint_handler = signal.signal(
                signal.SIGINT, self._handle_interrupt
            )

        if self._progress and self._layout:
            # Wrap progress in a panel with border
            progress_panel = Panel(
                self._progress,
                title=f"[{Colors.PANEL_TITLE}]Progress",
                border_style=Colors.PANEL_BORDER,
            )
            self._layout["progress"].update(progress_panel)
            self._update_layout()

            # Wrap the entire layout in a main panel
            main_panel = Panel(
                self._layout,
                title=f"[{Colors.PANEL_TITLE}]imapautofiler",
                border_style=Colors.PANEL_BORDER,
                padding=(0, 0),
                # height=19,
            )

            self._live = Live(main_panel, console=self._console, refresh_per_second=4)
            self._live.start()

    def stop(self) -> None:
        """Stop the progress tracking."""
        # Restore original signal handler
        if self._original_sigint_handler is not None:
            signal.signal(signal.SIGINT, self._original_sigint_handler)

        if self._live:
            self._live.stop()
        if self._progress:
            self._progress.stop()

        # Show final summary when interactive mode ends
        if self.interactive and self._console:
            self._show_final_summary()

    def _show_final_summary(self) -> None:
        """Display final processing summary after interactive mode ends."""
        if not self._console:
            return

        self._console.print("\n")

        # Show different title based on completion status
        if self._interrupted:
            self._console.print(
                f"[{Colors.INTERRUPT_TEXT}]Processing Interrupted[/] ⚠️\n"
            )
        else:
            self._console.print(f"[{Colors.PANEL_TITLE}]Processing Complete[/] 🎉\n")

        # Create summary table
        title = "Final Summary" if not self._interrupted else "Progress Summary"
        summary_table = Table(title=title, box=None, show_header=False)
        summary_table.add_column("Metric", style=Colors.METRIC_LABEL, width=15)
        summary_table.add_column("Count", justify="right", width=10)

        # Show timing information
        if self._start_time is not None:
            elapsed = time.time() - self._start_time
            if elapsed >= 60:
                time_str = f"{elapsed / 60:.1f}m"
            else:
                time_str = f"{elapsed:.1f}s"
            summary_table.add_row("Runtime:", time_str)

        # Show mailbox completion
        if "total_mailboxes_overall" in self._stats:
            completed = self._stats.get("completed_mailboxes", 0)
            total = self._stats["total_mailboxes_overall"]
            if self._interrupted and completed < total:
                summary_table.add_row(
                    "Mailboxes:", f"[{Colors.INTERRUPT_TEXT}]{completed}/{total}[/]"
                )
            else:
                summary_table.add_row("Mailboxes:", f"{completed}/{total}")

        # Show message statistics
        summary_table.add_row("Messages:", str(self._stats["total_messages"]))
        summary_table.add_row("Seen:", str(self._stats["seen"]))
        summary_table.add_row("Processed:", str(self._stats["processed"]))

        if self._stats["moved"] > 0:
            summary_table.add_row("Moved:", str(self._stats["moved"]))
        if self._stats["deleted"] > 0:
            summary_table.add_row("Deleted:", str(self._stats["deleted"]))
        if self._stats["flagged"] > 0:
            summary_table.add_row("Flagged:", str(self._stats["flagged"]))

        # Show errors prominently if any
        if self._stats["errors"] > 0:
            summary_table.add_row(
                "Errors:", f"[{Colors.ERROR_VALUE}]{self._stats['errors']}[/]"
            )

        self._console.print(summary_table)

        # Show additional context for interruptions
        if self._interrupted:
            self._console.print(
                "\n[dim]💡 Run again to continue processing remaining mailboxes[/]"
            )

        self._console.print()

    def _create_stats_panel(self) -> Panel:
        """Create the statistics table wrapped in a panel."""
        table = Table(box=None, show_header=True)
        table.add_column("Metric", style=Colors.METRIC_LABEL, width=12)
        table.add_column("Count", justify="right", width=8)
        table.add_column("Progress", justify="right", width=12)

        # Show overall mailbox progress if available
        if "total_mailboxes_overall" in self._stats:
            completed = self._stats.get("completed_mailboxes", 0)
            total = self._stats["total_mailboxes_overall"]
            progress_text = f"{completed}/{total}"
            table.add_row("Mailboxes", str(completed), progress_text)

        # Add statistics rows with minimal color coding
        table.add_row("Messages", str(self._stats["total_messages"]), "")
        table.add_row("Seen", str(self._stats["seen"]), "")
        table.add_row("Processed", str(self._stats["processed"]), "")
        table.add_row("Moved", str(self._stats["moved"]), "")
        table.add_row("Deleted", str(self._stats["deleted"]), "")
        table.add_row("Flagged", str(self._stats["flagged"]), "")
        if self._stats["errors"] > 0:
            table.add_row(
                "Errors", f"[{Colors.ERROR_VALUE}]{self._stats['errors']}", ""
            )
        else:
            table.add_row("Errors", str(self._stats["errors"]), "")

        return Panel(
            table,
            title=f"[{Colors.PANEL_TITLE}]Statistics",
            border_style=Colors.PANEL_BORDER,
        )

    def _create_current_panel(self) -> Panel:
        """Create the current processing panel."""
        if self._current_subject:
            # Create multi-line content showing subject, from, and to
            lines = []

            # Subject line
            subject = (
                self._current_subject[:60] + "..."
                if len(self._current_subject) > 60
                else self._current_subject
            )
            lines.append(f"📧 {subject}")

            # From line
            from_addr = (
                self._current_from[:50] + "..."
                if len(self._current_from) > 50
                else self._current_from
            )
            if from_addr:
                lines.append(f"👤 From: {from_addr}")

            # To line
            to_addr = (
                self._current_to[:50] + "..."
                if len(self._current_to) > 50
                else self._current_to
            )
            if to_addr:
                lines.append(f"📮 To: {to_addr}")

            content = Text("\n".join(lines))
        else:
            content = Text("⏳ Waiting...")

        return Panel(
            content,
            title=f"[{Colors.PANEL_TITLE}]Current: {self._current_mailbox}",
            border_style=Colors.PANEL_BORDER,
        )

    def _create_actions_panel(self) -> Panel:
        """Create the recent actions panel."""
        if not self._recent_actions:
            content = Text("⏳ No actions taken yet...", style="dim")
        else:
            lines = []
            for i, action in enumerate(self._recent_actions):
                # Add timestamp-style prefix and action
                icon = (
                    "✓" if i == 0 else "•"
                )  # Recent action gets checkmark, others get bullets
                style = "green" if i == 0 else ""  # Highlight most recent
                # Truncate very long action messages to fit panel width
                truncated_action = action[:80] + "..." if len(action) > 80 else action
                lines.append(Text(f"{icon} {truncated_action}", style=style))

            # Combine all lines
            content = Text()
            for i, line in enumerate(lines):
                if i > 0:
                    content.append("\n")
                content.append_text(line)

        return Panel(
            content,
            title=f"[{Colors.PANEL_TITLE}]Recent Actions",
            border_style=Colors.PANEL_BORDER,
        )

    def _update_layout(self) -> None:
        """Update the layout with current data."""
        if self._layout:
            self._layout["stats"].update(self._create_stats_panel())
            self._layout["current"].update(self._create_current_panel())
            self._layout["actions"].update(self._create_actions_panel())

    def start_overall(self, total_mailboxes: int) -> None:
        """Start tracking overall mailbox progress."""
        self._stats["total_mailboxes"] = 0  # Reset for accurate counting
        self._stats["total_mailboxes_overall"] = total_mailboxes
        self._stats["completed_mailboxes"] = 0

        if self._progress and self._overall_task is not None:
            self._progress.update(
                self._overall_task,
                description=f"[{Colors.PROGRESS_TEXT}]Processing mailboxes",
                total=total_mailboxes,
                completed=0,
            )

        self._update_layout()

    def start_mailbox(self, mailbox_name: str, total_messages: int) -> None:
        """Start tracking current mailbox progress."""
        self._current_mailbox = mailbox_name
        self._stats["total_messages"] += total_messages

        if self._progress:
            # Update the overall task description to show current mailbox
            completed_mb = self._stats.get("completed_mailboxes", 0)
            total_mb = self._stats.get("total_mailboxes_overall", 0)
            if self._overall_task is not None:
                self._progress.update(
                    self._overall_task,
                    description=f"[{Colors.PROGRESS_TEXT}]Mailbox {completed_mb + 1}/{total_mb}: {mailbox_name}",
                )

            # Update the pre-created mailbox messages progress task
            if self._mailbox_task is not None:
                self._progress.update(
                    self._mailbox_task,
                    description=f"[{Colors.PROGRESS_TEXT}]📁 Messages in {mailbox_name}",
                    total=total_messages,
                    completed=0,
                )
        elif not self.quiet:
            print(f"Processing mailbox: {mailbox_name} ({total_messages} messages)")

        self._update_layout()

    def update_message(
        self,
        advance: int = 1,
        subject: str = "",
        action: str = "",
        from_addr: str = "",
        to_addr: str = "",
        action_message: str = "",
    ) -> None:
        """Update progress for processed messages."""
        if subject:
            self._current_subject = subject
        if from_addr:
            self._current_from = from_addr
        if to_addr:
            self._current_to = to_addr

        # Always increment seen count when advancing (regardless of action)
        if advance > 0:
            self._stats["seen"] += advance

        # Add action message to recent actions list
        if action_message:
            self._recent_actions.insert(0, action_message)  # Add to front (most recent)
            # Keep only the most recent actions
            self._recent_actions = self._recent_actions[: self._max_actions]

        if action:
            # Update statistics based on action
            if action == "move":
                self._stats["moved"] += advance
            elif action == "delete":
                self._stats["deleted"] += advance
            elif action == "flag":
                self._stats["flagged"] += advance
            elif action == "error":
                self._stats["errors"] += advance

            self._stats["processed"] += advance

        if self._progress and self._mailbox_task is not None:
            self._progress.update(self._mailbox_task, advance=advance)

        self._update_layout()

    def finish_mailbox(self) -> None:
        """Finish current mailbox and update overall progress."""
        # Update overall mailbox completion count
        if "completed_mailboxes" in self._stats:
            self._stats["completed_mailboxes"] += 1

        if self._progress and self._overall_task is not None:
            self._progress.update(self._overall_task, advance=1)

        self._current_subject = ""
        self._current_from = ""
        self._current_to = ""
        self._update_layout()

    def is_interrupted(self) -> bool:
        """Check if processing has been interrupted by user."""
        return self._interrupted

    def print(self, message: str) -> None:
        """Print a message, handling rich console if available."""
        if self._console and self._live:
            # Print to the live display
            self._console.print(message)
        elif self._console:
            self._console.print(message)
        else:
            print(message)

    def __enter__(self) -> "ProgressTracker":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self.stop()


class RichWarningHandler(logging.Handler):
    """Custom logging handler that sends warnings to rich console."""

    def __init__(self, progress_tracker: "ProgressTracker") -> None:
        super().__init__(level=logging.WARNING)
        self.progress_tracker = progress_tracker

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.WARNING:
            msg = self.format(record)
            if record.levelno >= logging.ERROR:
                self.progress_tracker.print(f"[bold red]Error:[/] {msg}")
            else:
                self.progress_tracker.print(f"[bold yellow]Warning:[/] {msg}")


class NullProgressTracker:
    """No-op progress tracker for when progress display is disabled."""

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def start_overall(self, total_mailboxes: int) -> None:
        pass

    def start_mailbox(self, mailbox_name: str, total_messages: int) -> None:
        pass

    def update_message(
        self,
        advance: int = 1,
        subject: str = "",
        action: str = "",
        from_addr: str = "",
        to_addr: str = "",
        action_message: str = "",
    ) -> None:
        pass

    def finish_mailbox(self) -> None:
        pass

    def is_interrupted(self) -> bool:
        """Check if processing has been interrupted by user."""
        return False

    def print(self, message: str) -> None:
        print(message)

    def __enter__(self) -> "NullProgressTracker":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        self.stop()


def is_interactive_terminal() -> bool:
    """Check if we're running in an interactive terminal with full capabilities."""
    # Check if stdout is a TTY (not redirected)
    if not sys.stdout.isatty():
        return False

    # Check for common non-interactive environments
    import os

    ci_environments = {
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_URL",
        "BUILDKITE",
    }
    if any(env in os.environ for env in ci_environments):
        return False

    # Check terminal capabilities
    term = os.environ.get("TERM", "").lower()
    if term in ("dumb", "unknown", "") or "emacs" in term:
        return False

    return True


def should_use_progress(
    interactive_requested: bool = False,
    no_interactive_requested: bool = False,
    verbose: bool = False,
    debug: bool = False,
) -> bool:
    """Determine if progress display should be enabled based on environment and options."""
    # Explicit user preferences override everything
    if no_interactive_requested:
        return False
    if interactive_requested:
        return True

    # Auto-detection: enable if we have good terminal support
    # but disable for verbose/debug modes where log output is important
    if verbose or debug:
        return False

    return is_interactive_terminal()
