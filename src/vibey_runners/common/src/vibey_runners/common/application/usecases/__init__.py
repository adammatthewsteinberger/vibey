# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use-case orchestrations genuinely shared across the runner family.

Most usecases modules stay local to each runner: their function bodies
construct or accept runner-specific concrete domain types (a runner's own
``AutonomousRunner``, ``RunResult``, ``WorkPlan``, or command dataclasses)
directly, and genuinely sharing them would mean inventing new
dependency-injection seams (factories, structural runner protocols) that
do not exist anywhere in this family today -- that is a design change, not
an extraction. Only orchestration that is already pure with respect to
runner-specific types lives here.
"""

from __future__ import annotations

from vibey_runners.common.application.usecases.completion import with_done_marker_instruction

__all__ = ["with_done_marker_instruction"]
