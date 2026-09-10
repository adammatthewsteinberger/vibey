# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Every application-layer Protocol lives in `application/interfaces/`.

The convention is only worth having if it cannot quietly erode: a Protocol
declared inline in whatever module first needed it is exactly how a codebase
ends up with four different `ProjectStore`s. These tests are the enforcement.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Protocol, get_type_hints

import claudeloop.application as application_pkg
from claudeloop.application import interfaces, ports


def _is_protocol(obj: object) -> bool:
    return (
        inspect.isclass(obj)
        and issubclass(obj, Protocol)  # type: ignore[arg-type]
        and getattr(obj, "_is_protocol", False)
    )


def _iter_application_modules() -> list[str]:
    return [
        name
        for _, name, _ in pkgutil.walk_packages(
            application_pkg.__path__, prefix=f"{application_pkg.__name__}."
        )
    ]


def test_every_application_protocol_is_declared_in_interfaces() -> None:
    offenders: list[str] = []
    for module_name in _iter_application_modules():
        if module_name.startswith(f"{interfaces.__name__}") or module_name.endswith(".ports"):
            continue
        module = importlib.import_module(module_name)
        for attr_name, obj in vars(module).items():
            if not _is_protocol(obj):
                continue
            # Only flag declarations, not imports of an interface.
            if obj.__module__ == module_name:
                offenders.append(f"{module_name}.{attr_name}")
    assert offenders == [], (
        f"Protocols must be declared in application/interfaces/, not inline. Move: {offenders}"
    )


def test_interfaces_exports_every_protocol_it_declares() -> None:
    declared: set[str] = set()
    for _, module_name, _ in pkgutil.walk_packages(
        interfaces.__path__, prefix=f"{interfaces.__name__}."
    ):
        module = importlib.import_module(module_name)
        declared |= {
            name
            for name, obj in vars(module).items()
            if _is_protocol(obj) and obj.__module__ == module_name
        }
    assert declared <= set(interfaces.__all__)
    assert set(interfaces.__all__) == declared


def test_ports_shim_still_exports_the_same_names() -> None:
    """The move must not break `from claudeloop.application.ports import X`."""
    assert set(ports.__all__) == set(interfaces.__all__)
    for name in interfaces.__all__:
        assert getattr(ports, name) is getattr(interfaces, name)


def test_every_interface_is_runtime_checkable() -> None:
    """`isinstance(fake, Port)` is how the fake suite proves a double really
    satisfies the seam it stands in for, so every Protocol must support it."""
    not_checkable = [
        name
        for name in interfaces.__all__
        if not getattr(getattr(interfaces, name), "_is_runtime_protocol", False)
    ]
    assert not_checkable == []


def test_interface_annotations_all_resolve() -> None:
    """A Protocol whose annotations cannot be resolved is not usable as a type;
    `from __future__ import annotations` makes that easy to miss."""
    for name in interfaces.__all__:
        proto = getattr(interfaces, name)
        for method_name, method in vars(proto).items():
            if method_name.startswith("_") or not callable(method):
                continue
            get_type_hints(method)
