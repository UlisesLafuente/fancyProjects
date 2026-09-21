import sqlite3
from contextlib import closing

from persistence.database import connect, init_db

from projects.Page import Page
from projects.Project import Project
from projects.Task import Task


class ProjectRepository:
    def __init__(self, db_path=None):
        self.db_path = db_path

    def _new_connection(self):
        conn = connect(self.db_path)
        init_db(conn)
        return conn

    def save_project(self, project):
        with closing(self._new_connection()) as conn:
            with conn:
                if project.id is None:
                    cursor = conn.execute(
                        "INSERT INTO projects (name) VALUES (?)",
                        (project.projectName,),
                    )
                    project.id = cursor.lastrowid
                else:
                    conn.execute(
                        "UPDATE projects SET name = ? WHERE id = ?",
                        (project.projectName, project.id),
                    )

                conn.execute("DELETE FROM pages WHERE project_id = ?", (project.id,))

                for position, page in enumerate(project.pages):
                    cursor = conn.execute(
                        "INSERT INTO pages (project_id, position) VALUES (?, ?)",
                        (project.id, position),
                    )
                    page.id = cursor.lastrowid
                    for task_position, task in enumerate(page.getTasks()):
                        cursor = conn.execute(
                            "INSERT INTO tasks (page_id, name, hours_predicted, hours_completed, completed, position)"
                            " VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                page.id,
                                task.getTaskName(),
                                task.getHoursPredicted(),
                                task.getHoursCompleted(),
                                int(task.getCompletedTask()),
                                task_position,
                            ),
                        )
                        task.id = cursor.lastrowid

    def load_project(self, project_id):
        with closing(self._new_connection()) as conn:
            project_row = conn.execute(
                "SELECT id, name FROM projects WHERE id = ?",
                (project_id,),
            ).fetchone()
            if project_row is None:
                return None

            page_rows = conn.execute(
                "SELECT id, position FROM pages WHERE project_id = ? ORDER BY position",
                (project_id,),
            ).fetchall()

            pages = []
            for page in page_rows:
                task_rows = conn.execute(
                    "SELECT id, name, hours_predicted, hours_completed, completed"
                    " FROM tasks WHERE page_id = ? ORDER BY position",
                    (page["id"],),
                ).fetchall()
                tasks = [
                    self._build_task(row) for row in task_rows
                ]
                pages.append(Page(tasks, id=page["id"]))

            return Project(project_row["name"], pages, id=project_row["id"])

    def list_projects(self):
        with closing(self._new_connection()) as conn:
            rows = conn.execute(
                "SELECT id, name FROM projects ORDER BY id"
            ).fetchall()
            return [Project(row["name"], [], id=row["id"]) for row in rows]

    def delete_project(self, project_id):
        with closing(self._new_connection()) as conn:
            with conn:
                conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))

    @staticmethod
    def _build_task(row):
        task = Task(row["name"], row["hours_predicted"], id=row["id"])
        task.updateTask(
            row["name"],
            row["hours_predicted"],
            row["hours_completed"],
            bool(row["completed"]),
        )
        return task