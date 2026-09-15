# Development guide

Start from `develop`, make a focused topic branch, and preserve the dependency-free
runtime. Configuration and decision logic should be testable without GitHub or network
access. Mock subprocess boundaries, not domain decisions. Add new managed behavior to the
template, renderer, dogfood copy, and contract tests together. See `CONTRIBUTING.md`.
