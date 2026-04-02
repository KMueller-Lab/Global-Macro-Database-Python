from pathlib import Path
import sys
import importlib

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(REPO_ROOT))

gmd_module = importlib.import_module("global_macro_data.gmd")


class _LocalResponse:
    def __init__(self, content: bytes):
        self.content = content
        self.text = content.decode("utf-8", errors="replace")

    def raise_for_status(self) -> None:
        return None


def _clear_all_caches():
    for cache_fn in (
        gmd_module._versions_df,
        gmd_module._varlist_df,
        gmd_module._source_list_df,
        gmd_module._bib_df,
        gmd_module._country_df,
    ):
        if hasattr(cache_fn, "cache_clear"):
            cache_fn.cache_clear()


def _resolve_data_root():
    """Find the best available data root for tests.

    Priority:
    1. Bundled fixtures in tests/fixtures/ (always available, self-contained)
    2. Sibling Stata repo checkout (richer data, optional)
    """
    if (FIXTURES_DIR / "helpers").exists() and (FIXTURES_DIR / "final").exists():
        return FIXTURES_DIR

    for candidate in [
        REPO_ROOT.parent / "Global-Macro-Database-Stata-main",
        REPO_ROOT.parent / "Global-Macro-Database-Stata",
    ]:
        if (candidate / "data" / "helpers").exists():
            return candidate / "data"

    return None


@pytest.fixture(autouse=True)
def local_data_backend(monkeypatch):
    """Route all GMD fetches to local files for deterministic tests."""
    data_root = _resolve_data_root()
    if data_root is None:
        pytest.skip("No test data available (neither fixtures/ nor sibling Stata repo)")

    def _map_path(relative_path: str) -> Path:
        rel = relative_path.replace("\\", "/")
        if rel.startswith("helpers/"):
            return data_root / rel
        if rel.startswith("distribute/"):
            filename = rel.split("/", 1)[1]
            return data_root / "final" / filename
        if rel.startswith("clean/combined/"):
            filename = rel.split("/", 2)[2]
            return data_root / "clean" / filename
        raise RuntimeError(f"Unhandled resource path in test backend: {relative_path}")

    def _fetch_local(relative_path: str):
        target = _map_path(relative_path)
        if not target.exists():
            raise RuntimeError(f"Local test resource not found: {target}")
        return _LocalResponse(target.read_bytes())

    monkeypatch.setattr(gmd_module, "_fetch_first", _fetch_local)
    monkeypatch.setattr(gmd_module, "_fetch_primary", _fetch_local)
    monkeypatch.setattr(gmd_module, "_fetch_secondary", _fetch_local)

    _clear_all_caches()
    yield
    _clear_all_caches()
