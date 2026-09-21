import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from projects.Task import Task


class TestTaskInit(unittest.TestCase):
    def test_init_sets_defaults(self):
        task = Task("Write docs", 8)
        self.assertEqual(task.getTaskName(), "Write docs")
        self.assertEqual(task.getHoursPredicted(), 8)
        self.assertEqual(task.getEstimatedHours(), 8)
        self.assertEqual(task.getHoursCompleted(), 0)
        self.assertEqual(task.getHoursLeft(), 8)
        self.assertFalse(task.getCompletedTask())


class TestTaskGetters(unittest.TestCase):
    def setUp(self):
        self.task = Task("Review", 5)

    def test_getters_after_update(self):
        self.task.updateTask("Review final", 10, 4, False)
        self.assertEqual(self.task.getTaskName(), "Review final")
        self.assertEqual(self.task.getHoursPredicted(), 10)
        self.assertEqual(self.task.getEstimatedHours(), 10)
        self.assertEqual(self.task.getHoursCompleted(), 4)
        self.assertEqual(self.task.getHoursLeft(), 6)
        self.assertFalse(self.task.getCompletedTask())

    def test_completed_task_status(self):
        self.task.updateTask("Review", 5, 5, True)
        self.assertTrue(self.task.getCompletedTask())
        self.assertEqual(self.task.getHoursLeft(), 0)


class TestTaskUpdateTask(unittest.TestCase):
    def test_update_with_more_completed_than_predicted(self):
        task = Task("Code", 5)
        stream = StringIO()
        with redirect_stdout(stream):
            task.updateTask("Code v2", 5, 10, True)
        self.assertIn("cannot exceed predicted hours", stream.getvalue())
        self.assertFalse(task.getCompletedTask())
        self.assertEqual(task.getHoursCompleted(), 0)

    def test_update_recovers_after_invalid_state(self):
        task = Task("Debug", 3)
        stream = StringIO()
        with redirect_stdout(stream):
            task.updateTask("Debug", 3, 99, True)
        task.updateTask("Debug", 3, 2, False)
        self.assertEqual(task.getHoursCompleted(), 2)
        self.assertEqual(task.getHoursLeft(), 1)


class TestTaskSetHoursCompleted(unittest.TestCase):
    def test_set_hours_updates_left_and_status(self):
        task = Task("Entintar", 4)
        task.setHoursCompleted(2)
        self.assertEqual(task.getHoursCompleted(), 2)
        self.assertEqual(task.getHoursLeft(), 2)
        self.assertFalse(task.getCompletedTask())

    def test_set_all_hours_marks_completed(self):
        task = Task("Entintar", 4)
        task.setHoursCompleted(4)
        self.assertEqual(task.getHoursLeft(), 0)
        self.assertTrue(task.getCompletedTask())

    def test_set_hours_out_of_range_raises(self):
        task = Task("Entintar", 4)
        with self.assertRaises(ValueError):
            task.setHoursCompleted(5)
        with self.assertRaises(ValueError):
            task.setHoursCompleted(-1)


class TestTaskSetEstimatedHours(unittest.TestCase):
    def test_increase_keeps_completed(self):
        task = Task("Boceto", 2)
        task.setHoursCompleted(1)
        task.setEstimatedHours(5)
        self.assertEqual(task.getHoursPredicted(), 5)
        self.assertEqual(task.getHoursCompleted(), 1)
        self.assertEqual(task.getHoursLeft(), 4)
        self.assertFalse(task.getCompletedTask())

    def test_decrease_recomputes_left(self):
        task = Task("Boceto", 5)
        task.setHoursCompleted(2)
        task.setEstimatedHours(3)
        self.assertEqual(task.getHoursPredicted(), 3)
        self.assertEqual(task.getHoursCompleted(), 2)
        self.assertEqual(task.getHoursLeft(), 1)
        self.assertFalse(task.getCompletedTask())

    def test_decrease_below_completed_clamps(self):
        task = Task("Boceto", 5)
        task.setHoursCompleted(4)
        task.setEstimatedHours(2)
        self.assertEqual(task.getHoursPredicted(), 2)
        self.assertEqual(task.getHoursCompleted(), 2)
        self.assertEqual(task.getHoursLeft(), 0)
        self.assertTrue(task.getCompletedTask())

    def test_hours_a_tiny_minimum(self):
        task = Task("Boceto", 2)
        task.setEstimatedHours(1)
        self.assertEqual(task.getHoursPredicted(), 1)

    def test_zero_raises(self):
        task = Task("Boceto", 2)
        with self.assertRaises(ValueError):
            task.setEstimatedHours(0)


class TestTaskStr(unittest.TestCase):
    def test_str_returns_formatted_text(self):
        task = Task("Design", 20)
        task.updateTask("Design", 20, 8, False)
        rendered = str(task)
        self.assertIsInstance(rendered, str)
        self.assertIn("Task name: Design", rendered)
        self.assertIn("Total predicted hours: 20", rendered)
        self.assertIn("Predicted hours left to complete: 12", rendered)
        self.assertIn("Task status: False", rendered)


if __name__ == "__main__":
    unittest.main()