"""Aggregated plant views for the interface."""
from pathlib import Path

from graph import queries
from services.utils import new_id, now_iso, slugify

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def attention_reason(obs) -> str:
    """Reflect only what the user reported; this is not a diagnosis."""
    if not obs:
        return ""
    if obs.get("leaf_status") == "some_yellow":
        return "Leaves showing yellow"
    if obs.get("leaf_status") == "fallen":
        return "Leaves have fallen"
    if obs.get("pests_visible") == "yes":
        return "Pests visible"
    return ""


def plant_summary(plant: dict) -> dict:
    pid = plant["id"]
    obs = queries.current_observation(pid)
    return {
        "plant": plant,
        "last_care": queries.latest_care(pid),
        "last_watering": queries.latest_care(pid, "watered"),
        "last_obs": obs,
        "tasks": queries.pending_tasks(pid),
        "location": queries.get_plant_location(pid),
        "alert": attention_reason(obs),
    }


def all_summaries() -> list[dict]:
    return [plant_summary(p) for p in queries.list_plants()]


def add_plant(name: str, species: str = "", location_id: str = "", photo: str = "") -> dict:
    base = f"plant_{slugify(name)}"
    plant_id, i = base, 2
    while queries.get_plant(plant_id):
        plant_id, i = f"{base}_{i}", i + 1
    queries.create_plant(plant_id, name.strip(), species.strip(), now_iso(), photo=photo)
    if location_id:
        loc = next((l for l in queries.list_locations() if l["id"] == location_id), None)
        if loc:
            queries.set_plant_location(plant_id, loc["id"], loc["name"], loc.get("light", ""))
    return queries.get_plant(plant_id)


def delete_plant(plant_id: str) -> None:
    plant = queries.get_plant(plant_id)
    if not plant:
        return
    queries.delete_plant(plant_id)

    photo = plant.get("photo", "")
    if photo.startswith("uploads/"):
        path = (ASSETS / photo).resolve()
        try:
            path.relative_to((ASSETS / "uploads").resolve())
        except ValueError:
            return
        if not any(other.get("photo") == photo for other in queries.list_plants()):
            try:
                path.unlink()
            except OSError:
                pass
