from __future__ import annotations

pytest_plugins = [
    "tests.fixtures.db",
    "tests.fixtures.app",
    "tests.fixtures.llm",
    "tests.fixtures.corpus",
]
