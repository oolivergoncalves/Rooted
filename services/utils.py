"""Shared helpers for IDs, dates, and formatting."""
import re
import uuid
from datetime import datetime


def now_iso() -> str:
    return datetime.now().isoformat(timespec="microseconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "x"


def parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def fmt_date(ts: str) -> str:
    return parse(ts).strftime("%b %d, %Y")


def fmt_short(ts: str) -> str:
    return parse(ts).strftime("%b %d")


def fmt_datetime(ts: str) -> str:
    return parse(ts).strftime("%b %d, %Y • %I:%M %p")


def session_label(number) -> str:
    if number is None or number == "":
        return "—"
    return f"Session {int(number):02d}"
