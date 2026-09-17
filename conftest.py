"""Marks the project root for pytest so tests can import pawpal_system directly.

Without this file, bare `pytest` fails with ModuleNotFoundError because only
the tests/ directory lands on sys.path. Its presence at the root puts the root
on sys.path too, so both `pytest` and `python -m pytest` work.
"""
