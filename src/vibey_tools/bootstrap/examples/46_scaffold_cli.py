"""Example 46 — scaffold CLI (Terraform / Bicep / Helm / GitOps / CI / policy templates)."""

from __future__ import annotations

import subprocess
import sys

from vibey_bootstrap.contrib.scaffold import list_templates, main, scaffold


def demo_python_api() -> None:
    names = list_templates()
    print(f"{len(names)} templates available")
    for name in sorted(names)[:5]:
        print(f"  - {name}")
    print("  ...")


def demo_cli() -> None:
    code = main(["list"])
    print(f"vibey-bootstrap list exit code: {code}")


if __name__ == "__main__":
    demo_python_api()
    demo_cli()
    # Or from shell after `pip install vibey-bootstrap`:
    #   vibey-bootstrap list
    #   vibey-bootstrap scaffold helm/worker/Chart.yaml.template ./out --var app_name=my-worker
    if len(sys.argv) > 1 and sys.argv[1] == "--subprocess":
        subprocess.run(
            [sys.executable, "-m", "vibey_bootstrap.contrib.scaffold", "list"], check=False
        )
