import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

display_available = Gtk.init_check()[0]

from appWindow.app_window import ProjectApp, ProjectPickerDialog
from appWindow.new_project_dialog import NewProjectDialog
from appWindow.main_view import ProjectView, WORKFLOW_LABELS
from persistence.project_repository import ProjectRepository
from projects.Project import Project, WorkflowType
from projects.Page import Page
from projects.Task import Task


@unittest.skipUnless(display_available, "No hay display disponible")
class TestNewProjectDialog(unittest.TestCase):
    def setUp(self):
        window = Gtk.Window()
        self.dialog = NewProjectDialog(window)

    def tearDown(self):
        self.dialog.destroy()

    def test_default_workflow_is_continuous(self):
        self.assertEqual(self.dialog.get_workflow_type(), WorkflowType.CONTINUOUS)
        self.assertTrue(self.dialog.radio_continuous.get_active())

    def test_validation_rejects_empty_name_and_tasks(self):
        self.dialog.entry_name.set_text("")
        self.assertFalse(self.dialog._is_valid())

    def test_get_data(self):
        self.dialog.entry_name.set_text("Comic de superheroes")
        self.dialog.spin_pages.set_value(15)
        for name in ("Boceto", "Tinta", "Color"):
            self.dialog.entry_task.set_text(name)
            self.dialog._on_add_task()
            self.dialog.entry_task.set_text("")
        self.dialog.radio_by_task.set_active(True)

        data = self.dialog.get_data()
        self.assertEqual(data["project_name"], "Comic de superheroes")
        self.assertEqual(data["pages"], 15)
        self.assertEqual(data["tasks"], ["Boceto", "Tinta", "Color"])
        self.assertEqual(data["workflow_type"], WorkflowType.BY_TASK)


@unittest.skipUnless(display_available, "No hay display disponible")
class TestProjectView(unittest.TestCase):
    def setUp(self):
        self.view = ProjectView()
        self.window = Gtk.Window()
        self.window.add(self.view)
        self.window.show_all()

    def tearDown(self):
        self.window.destroy()

    def test_empty_view_default(self):
        self.assertEqual(self.view.get_visible_child_name(), "empty")

    def test_show_project_populates_tree(self):
        tasks = [Task("Boceto", 2), Task("Tinta", 3)]
        pages = [Page(list(tasks)), Page(list(tasks))]
        project = Project("Comic", pages, workflow_type=WorkflowType.BY_TASK)

        self.view.show_project(project)
        self.assertEqual(self.view.get_visible_child_name(), "project")
        self.assertEqual(self.view.project_title.get_text(), "Comic")
        self.assertIn(WORKFLOW_LABELS[WorkflowType.BY_TASK], self.view.workflow_label.get_text())

        page_iter = self.view.store.get_iter_first()
        self.assertIsNotNone(page_iter)
        self.assertEqual(self.view.store.get_value(page_iter, 0), "Página 1")

    def test_show_empty_returns_to_empty_state(self):
        self.view.show_empty()
        self.assertEqual(self.view.get_visible_child_name(), "empty")


@unittest.skipUnless(display_available, "No hay display disponible")
class TestProjectApp(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "gui_projects.db"
        self.app = ProjectApp()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_repository_uses_configured_db(self):
        self.app.repository = ProjectRepository(self.db_path)
        project = Project("Demo", [])
        self.app.repository.save_project(project)
        self.assertIsNotNone(self.app.repository.load_project(project.id))

    def test_picker_dialog_requires_selection(self):
        projects = [Project("A", []), Project("B", [])]
        window = Gtk.Window()
        dialog = ProjectPickerDialog(window, projects)
        dialog.connect("response", lambda d, r: d.destroy())
        dialog._on_response(dialog, Gtk.ResponseType.OK)
        self.assertIsNone(dialog.get_selected_id())
        dialog.destroy()


if __name__ == "__main__":
    unittest.main()