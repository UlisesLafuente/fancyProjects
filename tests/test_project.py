import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from projects.Page import Page
from projects.Project import Project
from projects.Task import Task


class TestProjectTotals(unittest.TestCase):
    def setUp(self):
        task1 = Task("T1", 100)
        task1.updateTask("T1", 100, 40, False)
        task2 = Task("T2", 50)
        task3 = Task("T3", 20)
        task3.updateTask("T3", 20, 20, True)
        page1 = Page([task1, task2])
        page2 = Page([task3])
        self.project = Project("Website", [page1, page2])

    def test_total_estimated_hours(self):
        self.assertEqual(self.project.getTotalEstimatedHours(), 170)

    def test_total_hours_left(self):
        self.assertEqual(self.project.getTotalHoursLeft(), 110)

    def test_total_completed_hours(self):
        self.assertEqual(self.project.getTotalCompletedHours(), 60)

    def test_empty_project_totals(self):
        empty = Project("Empty", [])
        self.assertEqual(empty.getTotalEstimatedHours(), 0)
        self.assertEqual(empty.getTotalHoursLeft(), 0)
        self.assertEqual(empty.getTotalCompletedHours(), 0)


class TestProjectPercentComplete(unittest.TestCase):
    def test_percent_complete(self):
        task = Task("T1", 100)
        task.updateTask("T1", 100, 40, False)
        project = Project("P", [Page([task])])
        self.assertAlmostEqual(project.percentComplete(), 40.0)

    def test_percent_complete_multiple_pages(self):
        task1 = Task("T1", 100)
        task1.updateTask("T1", 100, 40, False)
        task2 = Task("T2", 50)
        task3 = Task("T3", 20)
        task3.updateTask("T3", 20, 20, True)
        project = Project("P", [Page([task1, task2]), Page([task3])])
        self.assertAlmostEqual(project.percentComplete(), 60.0 / 170.0 * 100)

    def test_percent_complete_fully_completed(self):
        task = Task("T1", 10)
        task.updateTask("T1", 10, 10, True)
        project = Project("P", [Page([task])])
        self.assertAlmostEqual(project.percentComplete(), 100.0)

    def test_percent_complete_empty_project_returns_zero(self):
        self.assertEqual(Project("Empty", []).percentComplete(), 0)


class TestProjectPages(unittest.TestCase):
    def setUp(self):
        self.project = Project("P", [])

    def test_add_page(self):
        page = Page([])
        self.project.addPage(page)
        self.assertIn(page, self.project.getPages())
        self.assertEqual(len(self.project.getPages()), 1)

    def test_get_pages(self):
        page = Page([])
        project = Project("P", [page])
        self.assertEqual(project.getPages(), [page])


if __name__ == "__main__":
    unittest.main()