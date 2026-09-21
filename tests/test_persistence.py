import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from persistence.project_repository import ProjectRepository
from projects.Page import Page
from projects.Project import Project
from projects.Task import Task


class ProjectRepositoryTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test_projects.db"
        self.repository = ProjectRepository(self.db_path)

    def tearDown(self):
        self.tempdir.cleanup()

    def build_sample_project(self):
        task1 = Task("Task 1", 100)
        task1.updateTask("Task 1", 100, 40, False)
        task2 = Task("Task 2", 50)
        page1 = Page([task1, task2])

        task3 = Task("Task 3", 20)
        task3.updateTask("Task 3", 20, 20, True)
        page2 = Page([task3])

        return Project("Sample", [page1, page2])


class TestProjectRepository(ProjectRepositoryTestCase):
    def test_workflow_type_roundtrip(self):
        project = Project("Comic", [Page([Task("boceto", 0)])], workflow_type="by_task")
        self.repository.save_project(project)

        loaded = self.repository.load_project(project.id)
        self.assertEqual(loaded.workflow_type, "by_task")

    def test_workflow_type_default(self):
        project = Project("Comic", [])
        self.repository.save_project(project)
        self.assertEqual(project.workflow_type, "continuous")

        loaded = self.repository.load_project(project.id)
        self.assertEqual(loaded.workflow_type, "continuous")

    def test_save_and_load_roundtrip(self):
        project = self.build_sample_project()
        self.repository.save_project(project)

        loaded = self.repository.load_project(project.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.projectName, "Sample")
        self.assertEqual(len(loaded.pages), 2)
        self.assertEqual(loaded.getTotalEstimatedHours(), 170)
        self.assertEqual(loaded.getTotalCompletedHours(), 60)
        self.assertAlmostEqual(loaded.percentComplete(), 60.0 / 170.0 * 100)

    def test_load_preserves_task_data_and_status(self):
        project = self.build_sample_project()
        self.repository.save_project(project)

        loaded = self.repository.load_project(project.id)
        tasks = loaded.getPages()[0].getTasks()
        self.assertEqual(tasks[0].getTaskName(), "Task 1")
        self.assertEqual(tasks[0].getHoursPredicted(), 100)
        self.assertEqual(tasks[0].getHoursCompleted(), 40)
        self.assertEqual(tasks[0].getHoursLeft(), 60)
        self.assertFalse(tasks[0].getCompletedTask())
        self.assertTrue(loaded.getPages()[1].getTasks()[0].getCompletedTask())

    def test_save_assigns_ids(self):
        project = self.build_sample_project()
        self.assertIsNone(project.id)
        self.repository.save_project(project)
        self.assertIsNotNone(project.id)
        for page in project.pages:
            self.assertIsNotNone(page.id)
            for task in page.getTasks():
                self.assertIsNotNone(task.id)

    def test_resave_updates_name_and_replace_children(self):
        project = self.build_sample_project()
        self.repository.save_project(project)

        project.pages = [Page([Task("New only", 5)])]
        project.projectName = "Renamed"
        self.repository.save_project(project)

        loaded = self.repository.load_project(project.id)
        self.assertEqual(loaded.projectName, "Renamed")
        self.assertEqual(len(loaded.pages), 1)
        self.assertEqual(len(loaded.getPages()[0].getTasks()), 1)
        self.assertEqual(loaded.getPages()[0].getTasks()[0].getTaskName(), "New only")
        self.assertEqual(loaded.getTotalEstimatedHours(), 5)

    def test_preserves_page_and_task_order(self):
        tasks = [Task("A", 1), Task("B", 2), Task("C", 3)]
        project = Project("Order", [Page(tasks)])
        self.repository.save_project(project)

        loaded = self.repository.load_project(project.id)
        names = [t.getTaskName() for t in loaded.getPages()[0].getTasks()]
        self.assertEqual(names, ["A", "B", "C"])

    def test_load_nonexistent_returns_none(self):
        self.assertIsNone(self.repository.load_project(999))

    def test_list_projects(self):
        project = self.build_sample_project()
        self.repository.save_project(project)
        project2 = Project("Second", [])
        self.repository.save_project(project2)

        projects = self.repository.list_projects()
        self.assertEqual([p.projectName for p in projects], ["Sample", "Second"])
        self.assertEqual([p.id for p in projects], [project.id, project2.id])
        self.assertTrue(all(p.getPages() == [] for p in projects))

    def test_delete_project(self):
        project = self.build_sample_project()
        self.repository.save_project(project)

        self.repository.delete_project(project.id)

        self.assertIsNone(self.repository.load_project(project.id))
        self.assertEqual(self.repository.list_projects(), [])

    def test_empty_project_roundtrip(self):
        project = Project("Empty", [])
        self.repository.save_project(project)

        loaded = self.repository.load_project(project.id)
        self.assertEqual(loaded.projectName, "Empty")
        self.assertEqual(loaded.getPages(), [])
        self.assertEqual(loaded.percentComplete(), 0)


if __name__ == "__main__":
    unittest.main()