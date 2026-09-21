import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from projects.Page import Page
from projects.Task import Task


class TestPageTotals(unittest.TestCase):
    def setUp(self):
        self.task1 = Task("T1", 100)
        self.task1.updateTask("T1", 100, 40, False)
        self.task2 = Task("T2", 50)
        self.page = Page([self.task1, self.task2])

    def test_total_estimated_hours(self):
        self.assertEqual(self.page.getTotalEstimatedHours(), 150)

    def test_total_hours_left(self):
        self.assertEqual(self.page.getTotalHoursLeft(), 110)

    def test_total_completed_hours(self):
        self.assertEqual(self.page.getTotalCompletedHours(), 40)

    def test_empty_page_totals(self):
        empty = Page([])
        self.assertEqual(empty.getTotalEstimatedHours(), 0)
        self.assertEqual(empty.getTotalHoursLeft(), 0)
        self.assertEqual(empty.getTotalCompletedHours(), 0)


class TestPagePercentile(unittest.TestCase):
    def test_percentile_completed(self):
        task = Task("T1", 100)
        task.updateTask("T1", 100, 40, False)
        page = Page([task])
        self.assertAlmostEqual(page.getPercentileCompleted(), 40.0)

    def test_percentile_partial(self):
        task1 = Task("T1", 100)
        task1.updateTask("T1", 100, 40, False)
        task2 = Task("T2", 50)
        page = Page([task1, task2])
        self.assertAlmostEqual(page.getPercentileCompleted(), 40.0 / 150.0 * 100)

    def test_percentile_fully_completed(self):
        task = Task("T1", 100)
        task.updateTask("T1", 100, 100, True)
        page = Page([task])
        self.assertAlmostEqual(page.getPercentileCompleted(), 100.0)

    def test_percentile_empty_page_returns_zero(self):
        self.assertEqual(Page([]).getPercentileCompleted(), 0)


class TestPageTasks(unittest.TestCase):
    def setUp(self):
        self.page = Page([])

    def test_add_task(self):
        task = Task("New", 3)
        self.page.addTask(task)
        self.assertIn(task, self.page.getTasks())
        self.assertEqual(len(self.page.getTasks()), 1)

    def test_get_tasks(self):
        task = Task("Single", 1)
        page = Page([task])
        self.assertEqual(page.getTasks(), [task])


if __name__ == "__main__":
    unittest.main()