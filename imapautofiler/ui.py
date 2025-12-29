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

import sys
from typing import Optional

try:
    from rich.console import Console
    from rich.progress import (
        Progress,
        TaskID,
        BarColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
        MofNCompleteColumn,
    )

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ProgressTracker:
    """Tracks progress for mailbox processing with fallback for environments without rich."""

    def __init__(self, interactive: bool = False, quiet: bool = False) -> None:
        self.interactive = interactive and RICH_AVAILABLE
        self.quiet = quiet
        self._console: Optional["Console"] = None
        self._progress: Optional["Progress"] = None
        self._overall_task: Optional["TaskID"] = None
        self._mailbox_task: Optional["TaskID"] = None

        if self.interactive:
            self._console = Console()
            self._progress = Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=self._console,
            )

    def start(self) -> None:
        """Start the progress tracking."""
        if self._progress:
            self._progress.start()

    def stop(self) -> None:
        """Stop the progress tracking."""
        if self._progress:
            self._progress.stop()

    def start_overall(self, total_mailboxes: int) -> None:
        """Start tracking overall mailbox progress."""
        if self._progress:
            self._overall_task = self._progress.add_task(
                "Processing mailboxes", total=total_mailboxes
            )

    def start_mailbox(self, mailbox_name: str, total_messages: int) -> None:
        """Start tracking current mailbox progress."""
        if self._progress and self._overall_task is not None:
            self._progress.update(
                self._overall_task, description=f"Processing mailbox: {mailbox_name}"
            )

        if self._progress:
            self._mailbox_task = self._progress.add_task(
                f"Messages in {mailbox_name}", total=total_messages
            )
        elif not self.quiet:
            print(f"Processing mailbox: {mailbox_name} ({total_messages} messages)")

    def update_message(self, advance: int = 1) -> None:
        """Update progress for processed messages."""
        if self._progress and self._mailbox_task is not None:
            self._progress.update(self._mailbox_task, advance=advance)

    def finish_mailbox(self) -> None:
        """Finish current mailbox and update overall progress."""
        if self._progress:
            if self._mailbox_task is not None:
                self._progress.remove_task(self._mailbox_task)
                self._mailbox_task = None
            if self._overall_task is not None:
                self._progress.update(self._overall_task, advance=1)

    def print(self, message: str) -> None:
        """Print a message, handling rich console if available."""
        if self._console:
            self._console.print(message)
        else:
            print(message)

    def __enter__(self) -> "ProgressTracker":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def is_interactive_terminal() -> bool:
    """Check if we're running in an interactive terminal."""
    return sys.stdout.isatty() and RICH_AVAILABLE
