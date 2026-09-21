import json
from pathlib import Path

from projects.Page import Page
from projects.Project import Project
from projects.Task import Task

EXPORT_FORMAT = "fancyprojects"
EXPORT_VERSION = 1


def serialize_project(project):
    return {
        "format": EXPORT_FORMAT,
        "version": EXPORT_VERSION,
        "project": {
            "name": project.projectName,
            "workflow_type": project.workflow_type,
            "pages": [
                {
                    "tasks": [
                        {
                            "name": task.getTaskName(),
                            "hours_predicted": task.getHoursPredicted(),
                            "hours_completed": task.getHoursCompleted(),
                            "completed": task.getCompletedTask(),
                        }
                        for task in page.getTasks()
                    ]
                }
                for page in project.getPages()
            ],
        },
    }


def _build_task(data):
    name = data["name"]
    predicted = int(data["hours_predicted"])
    completed = max(0, min(int(data["hours_completed"]), predicted))
    task = Task(name, predicted)
    task.updateTask(name, predicted, completed, bool(data.get("completed", False)) or completed >= predicted)
    return task


def deserialize_project(data):
    if not isinstance(data, dict) or data.get("format") != EXPORT_FORMAT:
        raise ValueError("El archivo no tiene el formato de Fancy Projects.")
    if data.get("version") not in (EXPORT_VERSION,):
        raise ValueError(
            "Versión del archivo no soportada: {}.".format(data.get("version"))
        )
    project_data = data.get("project")
    if not isinstance(project_data, dict) or "name" not in project_data:
        raise ValueError("El archivo no contiene un proyecto válido.")

    pages = []
    for page_data in project_data.get("pages", []):
        tasks = [_build_task(task_data) for task_data in page_data.get("tasks", [])]
        pages.append(Page(tasks))

    return Project(
        project_data["name"],
        pages,
        workflow_type=project_data.get("workflow_type", "continuous"),
    )


def export_project(project, path):
    path = Path(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(serialize_project(project), f, ensure_ascii=False, indent=2)


def import_project(path):
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError("El archivo no es JSON válido: {}.".format(e))
    return deserialize_project(data)