"""FalkorDB connection and Cypher execution helpers."""
import contextvars
import os
import re
from functools import lru_cache

from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

# Each tenant is an isolated garden graph (graph = rooted:<tenant>). A ContextVar ensures each
# Streamlit script run uses the graph for its own user.
_tenant = contextvars.ContextVar("rooted_tenant", default="")


def slug_tenant(name: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "", (name or "").strip().lower())


def use_tenant(name: str) -> None:
    _tenant.set(slug_tenant(name))


def list_gardens() -> list[str]:
    """Return existing gardens: '' is the default (rooted); others are rooted:<name>."""
    base = os.getenv("FALKORDB_GRAPH", "rooted")
    gardens = [""]
    try:
        names = _client().list_graphs()
    except Exception:
        names = []
    for name in names:
        name = name.decode() if isinstance(name, bytes) else str(name)
        if name.startswith(base + ":"):
            gardens.append(name[len(base) + 1:])
    return sorted(set(gardens), key=lambda g: (g != "", g))


def current_tenant() -> str:
    return _tenant.get()


def graph_name() -> str:
    base = os.getenv("FALKORDB_GRAPH", "rooted")
    tenant = _tenant.get()
    return f"{base}:{tenant}" if tenant else base


@lru_cache(maxsize=1)
def _client() -> FalkorDB:
    return FalkorDB(
        host=os.getenv("FALKORDB_HOST", "localhost"),
        port=int(os.getenv("FALKORDB_PORT", "6379")),
        username=os.getenv("FALKORDB_USERNAME") or None,
        password=os.getenv("FALKORDB_PASSWORD") or None,
    )


def get_graph():
    return _client().select_graph(graph_name())


def is_available() -> bool:
    try:
        get_graph().query("RETURN 1")
        return True
    except Exception:
        return False


def _convert(value):
    """Converte Node/Edge do FalkorDB em dicts simples."""
    if hasattr(value, "properties") and hasattr(value, "labels"):  # Node
        data = dict(value.properties)
        data["_labels"] = list(value.labels)
        return data
    if hasattr(value, "properties") and hasattr(value, "relation"):  # Edge
        data = dict(value.properties)
        data["_relation"] = value.relation
        return data
    if isinstance(value, list):
        return [_convert(v) for v in value]
    return value


def run(query: str, params: dict | None = None) -> list[dict]:
    """Read through ro_query, the read-only path used by all non-writing operations."""
    result = get_graph().ro_query(query, params or {})
    header = [h[1] if isinstance(h, (list, tuple)) else h for h in result.header]
    return [dict(zip(header, (_convert(v) for v in row))) for row in result.result_set]


def execute(query: str, params: dict | None = None) -> None:
    get_graph().query(query, params or {})


def reset_graph() -> None:
    try:
        get_graph().delete()
    except Exception:
        pass
