"""Tests use a dedicated graph (rooted_test) and require FalkorDB to be running.
Tests marked with @pytest.mark.nodb do not access the database."""
import os

os.environ["FALKORDB_GRAPH"] = "rooted_test"

import pytest  # noqa: E402

from graph import db, seed  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_graph(request):
    if request.node.get_closest_marker("nodb"):
        yield
        return
    if not db.is_available():
        pytest.skip("FalkorDB is not running (docker compose up -d)")
    db.reset_graph()
    seed.ensure_base()
    yield
    db.reset_graph()
