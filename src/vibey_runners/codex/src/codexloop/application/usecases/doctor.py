# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Use case: pre-flight doctor checks before a long unattended run."""

from __future__ import annotations

from pathlib import Path

from codexloop.application.interfaces.doctor import (
    DoctorCheck,
    DoctorEnvironment,
    DoctorReport,
)


def run_doctor(env: DoctorEnvironment, *, cwd: Path) -> DoctorReport:
    return env.diagnose(cwd=cwd)


__all__ = ["DoctorCheck", "DoctorEnvironment", "DoctorReport", "run_doctor"]
