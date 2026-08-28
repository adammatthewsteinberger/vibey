# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import pytest

from vibey.domain.command_guard import (
    CommandSecurityPolicy,
    DestructiveCommandBlocked,
    scan_command,
)


def test_command_guard_detects_git_destructive() -> None:
    policy = CommandSecurityPolicy()

    # Blocked git commands
    blocked = [
        "git reset --hard",
        "git reset --hard HEAD~1",
        "git push --force",
        "git push origin main -f",
        "git push --force-with-lease origin main",
        "git branch -D main",
        "git branch -D master",
    ]
    for cmd in blocked:
        match = scan_command(cmd)
        assert match is not None, f"Expected {cmd} to be blocked"
        with pytest.raises(DestructiveCommandBlocked):
            policy.check_command(cmd)


def test_command_guard_detects_filesystem_destructive() -> None:
    policy = CommandSecurityPolicy()

    blocked = [
        "rm -rf /",
        "rm -fr /",
        "rm -rf /*",
        "rm -rf ~",
        "rm -rf ~/",
        "rm -rf *",
        "mkfs.ext4 /dev/sda",
        "dd if=/dev/zero of=/dev/sda",
        "chmod -R 777 /",
    ]
    for cmd in blocked:
        match = scan_command(cmd)
        assert match is not None, f"Expected {cmd} to be blocked"
        with pytest.raises(DestructiveCommandBlocked):
            policy.check_command(cmd)


def test_command_guard_detects_system_and_sql_destructive() -> None:
    policy = CommandSecurityPolicy()

    blocked = [
        "reboot",
        "shutdown -h now",
        "poweroff",
        ":(){ :|:& };:",
        "DROP DATABASE production;",
        "DROP TABLE users CASCADE;",
    ]
    for cmd in blocked:
        match = scan_command(cmd)
        assert match is not None, f"Expected {cmd} to be blocked"
        with pytest.raises(DestructiveCommandBlocked):
            policy.check_command(cmd)


def test_command_guard_allows_safe_commands() -> None:
    policy = CommandSecurityPolicy()

    safe = [
        "git status",
        "git diff",
        "git commit -m 'feat: test'",
        "git checkout -b feature/test",
        "pytest",
        "uv run pytest tests",
        "rm file.txt",
        "rm -f temp.log",
        "SELECT * FROM users;",
        "cargo build --release",
        "npm test",
    ]
    for cmd in safe:
        assert scan_command(cmd) is None
        policy.check_command(cmd)
        assert policy.is_allowed(cmd) is True
