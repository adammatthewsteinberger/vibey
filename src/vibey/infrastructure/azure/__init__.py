# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Azure infrastructure adapters and verification clients (Milestone 10)."""

from vibey.infrastructure.azure.adapter import AzureCliAdapter, InMemoryAzureClientAdapter
from vibey.infrastructure.azure.iac import IacValidator

__all__ = ["AzureCliAdapter", "IacValidator", "InMemoryAzureClientAdapter"]
