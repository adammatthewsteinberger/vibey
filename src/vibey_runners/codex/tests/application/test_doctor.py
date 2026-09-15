# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Application doctor use case."""

from __future__ import annotations

from pathlib import Path

from codexloop.application.usecases.doctor import DoctorCheck, DoctorReport, run_doctor


class _Env:
    def diagnose(self, *, cwd: Path) -> DoctorReport:
        return DoctorReport(
            checks=(DoctorCheck("codex", True, str(cwd)),),
            auth_mode="chatgpt",
            probe_strategies={"exec": True},
        )


def test_run_doctor_delegates_to_environment(tmp_path: Path) -> None:
    report = run_doctor(_Env(), cwd=tmp_path)
    assert report.all_passed
    assert report.auth_mode == "chatgpt"
    assert report.checks[0].detail == str(tmp_path)
