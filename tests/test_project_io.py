import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from persistence.project_io import (
    EXPORT_FORMAT,
    deserialize_project,
    export_project,
    import_project,
    serialize_project,
)
from projects.Page import Page
from projects.Project import Project, WorkflowType
from projects.Task import Task


def build_sample_project():
    task1 = Task("Boceto", 100)
    task1.updateTask("Boceto", 100, 40, False)
    task2 = Task("Tinta", 50)
    task2.updateTask("Tinta", 50, 50, True)
    page1 = Page([task1, task2])
    page2 = Page([Task("Color", 20)])

    project = Project("Comic", [page1, page2], id=7, workflow_type=WorkflowType.BY_TASK)
    task2.id = 3
    page1.id = 10
    return project


class TestSerialize(unittest.TestCase):
    def test_serialize_contains_format_and_version(self):
        data = serialize_project(build_sample_project())
        self.assertEqual(data["format"], EXPORT_FORMAT)
        self.assertEqual(data["version"], 1)

    def test_serialize_keeps_structure(self):
        project = build_sample_project()
        data = serialize_project(project)
        self.assertEqual(data["project"]["name"], "Comic")
        self.assertEqual(data["project"]["workflow_type"], "by_task")
        self.assertEqual(len(data["project"]["pages"]), 2)
        tasks = data["project"]["pages"][0]["tasks"]
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["name"], "Boceto")
        self.assertEqual(tasks[0]["hours_predicted"], 100)
        self.assertEqual(tasks[0]["hours_completed"], 40)
        self.assertFalse(tasks[0]["completed"])
        self.assertTrue(tasks[1]["completed"])

    def test_serialize_does_not_include_db_ids(self):
        project = build_sample_project()
        data = serialize_project(project)
        self.assertNotIn("id", data["project"])
        self.assertNotIn("id", data["project"]["pages"][0])
        self.assertNotIn("id", data["project"]["pages"][0]["tasks"][0])


class TestDeserialize(unittest.TestCase):
    def test_roundtrip_preserves_content(self):
        original = build_sample_project()
        restored = deserialize_project(serialize_project(original))

        self.assertEqual(restored.projectName, "Comic")
        self.assertEqual(restored.workflow_type, "by_task")
        self.assertIsNone(restored.id)
        self.assertEqual(len(restored.getPages()), 2)
        page = restored.getPages()[0]
        self.assertEqual([t.getTaskName() for t in page.getTasks()], ["Boceto", "Tinta"])
        self.assertEqual(page.getTasks()[0].getHoursPredicted(), 100)
        self.assertEqual(page.getTasks()[0].getHoursCompleted(), 40)
        self.assertFalse(page.getTasks()[0].getCompletedTask())
        self.assertTrue(page.getTasks()[1].getCompletedTask())
        self.assertEqual(restored.getTotalEstimatedHours(), 170)
        self.assertEqual(restored.getTotalCompletedHours(), 90)

    def test_roundtrip_progress_and_completion(self):
        task = Task("Única", 8)
        task.setHoursCompleted(8)
        project = Project("Página completa", [Page([task])])
        restored = deserialize_project(serialize_project(project))

        self.assertTrue(restored.getPages()[0].getTasks()[0].getCompletedTask())
        self.assertTrue(restored.getPages()[0].isCompleted())
        self.assertEqual(restored.percentComplete(), 100)

    def test_rejects_wrong_format(self):
        with self.assertRaises(ValueError):
            deserialize_project({"format": "otra-cosa", "version": 1, "project": {}})

    def test_rejects_unsupported_version(self):
        with self.assertRaises(ValueError):
            deserialize_project({"format": EXPORT_FORMAT, "version": 99, "project": {}})

    def test_rejects_non_dict(self):
        with self.assertRaises(ValueError):
            deserialize_project(["no", "object"])

    def test_missing_project_field(self):
        with self.assertRaises(ValueError):
            deserialize_project({"format": EXPORT_FORMAT, "version": 1})

    def test_defaults_workflow_when_absent(self):
        data = serialize_project(build_sample_project())
        del data["project"]["workflow_type"]
        self.assertEqual(deserialize_project(data).workflow_type, "continuous")

    def test_clamps_completed_hours_to_predicted(self):
        project = deserialize_project({
            "format": EXPORT_FORMAT,
            "version": 1,
            "project": {
                "name": "Raro",
                "pages": [{
                    "tasks": [{
                        "name": "T",
                        "hours_predicted": 4,
                        "hours_completed": 99,
                        "completed": False,
                    }]
                }],
            },
        })
        task = project.getPages()[0].getTasks()[0]
        self.assertEqual(task.getHoursCompleted(), 4)
        self.assertTrue(task.getCompletedTask())


class TestFiles(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_export_and_import_roundtrip(self):
        project = build_sample_project()
        path = Path(self.tempdir.name) / "comic.fancyproject"
        export_project(project, path)

        self.assertTrue(path.exists())
        restored = import_project(path)
        self.assertEqual(restored.projectName, "Comic")
        self.assertEqual(restored.getTotalEstimatedHours(), 170)
        self.assertEqual(restored.getTotalCompletedHours(), 90)
        self.assertEqual(restored.workflow_type, "by_task")

    def test_import_rejects_invalid_json(self):
        path = Path(self.tempdir.name) / "raro.txt"
        path.write_text("esto no es json", encoding="utf-8")
        with self.assertRaises(ValueError):
            import_project(path)

    def test_import_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            import_project(Path(self.tempdir.name) / "no_existe.fancyproject")


if __name__ == "__main__":
    unittest.main()