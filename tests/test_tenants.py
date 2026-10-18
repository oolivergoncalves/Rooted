"""Track 2: memory separated by user or tenant (one isolated graph per garden)."""
from agents import care_agent
from graph import db, queries, seed
from services import session_service


def test_tenants_have_isolated_memory():
    try:
        db.use_tenant("garden_a")
        db.reset_graph()
        seed.ensure_base(sample_plants=True)
        s = session_service.start_session()
        care_agent.register_care("plant_monstera", s["id"], "Watered")
        assert queries.latest_care("plant_monstera") is not None

        db.use_tenant("garden_b")  # Other garden: no data from garden A should appear.
        db.reset_graph()
        seed.ensure_base()
        assert queries.latest_care("plant_monstera") is None
        assert queries.list_sessions() == []

        db.use_tenant("garden_a")  # Garden A retains its own data.
        assert queries.latest_care("plant_monstera") is not None
        assert len(queries.list_sessions()) == 1
    finally:
        for tenant in ("garden_a", "garden_b"):
            db.use_tenant(tenant)
            db.reset_graph()
        db.use_tenant("")


def test_new_garden_starts_without_plants():
    try:
        db.use_tenant("garden_c")
        db.reset_graph()
        seed.ensure_base()
        assert queries.list_plants() == []
        assert queries.base_ready()
    finally:
        db.use_tenant("garden_c")
        db.reset_graph()
        db.use_tenant("")
