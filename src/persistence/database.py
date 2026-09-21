import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "fancyProjects" / "projects.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    workflow_type TEXT NOT NULL DEFAULT 'continuous'
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    position INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    hours_predicted INTEGER NOT NULL,
    hours_completed INTEGER NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    position INTEGER NOT NULL
);
"""


def resolve_db_path(db_path=None):
    if db_path is not None:
        return Path(db_path)
    override = os.environ.get("FANCY_PROJECTS_DB")
    if override:
        return Path(override)
    return DEFAULT_DB_PATH


def connect(db_path=None):
    path = resolve_db_path(db_path)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    conn.executescript(SCHEMA)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(projects)")}
    if "workflow_type" not in columns:
        conn.execute("ALTER TABLE projects ADD COLUMN workflow_type TEXT NOT NULL DEFAULT 'continuous'")
    conn.commit()