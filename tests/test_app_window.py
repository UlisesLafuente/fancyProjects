import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

display_available = Gtk.init_check()

from appWindow.app_window import ProjectApp, ProjectPickerDialog, ProjectWindow, install_stylesheet, STYLE_CSS
from appWindow.main_view import ProjectView, WORKFLOW_LABELS
from appWindow.new_project_dialog import NewProjectDialog
from persistence.project_repository import ProjectRepository
from projects.Page import Page
from projects.Project import Project, WorkflowType
from projects.Task import Task


@unittest.skipUnless(display_available, "No hay display disponible")
class TestNewProjectDialog(unittest.TestCase):
    def setUp(self):
        self.dialog = NewProjectDialog()

    def test_default_workflow_is_continuous(self):
        self.assertEqual(self.dialog.get_workflow_type(), WorkflowType.CONTINUOUS)
        self.assertTrue(self.dialog.radio_continuous.get_active())

    def test_validation_rejects_empty_name_and_tasks(self):
        self.dialog.entry_name.set_text("")
        self.assertFalse(self.dialog._is_valid())

    def test_get_data(self):
        self.dialog.entry_name.set_text("Comic de superheroes")
        self.dialog.spin_pages.set_value(15)
        for name, hours in (("Boceto", 2), ("Tinta", 3), ("Color", 4)):
            self.dialog.entry_task.set_text(name)
            self.dialog.spin_task_hours.set_value(hours)
            self.dialog._on_add_task()
            self.dialog.entry_task.set_text("")
        self.dialog.radio_by_task.set_active(True)

        data = self.dialog.get_data()
        self.assertEqual(data["project_name"], "Comic de superheroes")
        self.assertEqual(data["pages"], 15)
        self.assertEqual(data["tasks"], [("Boceto", 2), ("Tinta", 3), ("Color", 4)])
        self.assertEqual(data["workflow_type"], WorkflowType.BY_TASK)

    def test_add_task_defaults_to_one_hour(self):
        self.dialog.entry_task.set_text("Boceto")
        self.dialog._on_add_task()
        self.assertEqual(self.dialog._tasks, [("Boceto", 1)])

    def test_add_task_ignores_duplicates(self):
        self.dialog.entry_task.set_text("Boceto")
        self.dialog._on_add_task()
        self.dialog.entry_task.set_text("Boceto")
        self.dialog._on_add_task()
        self.assertEqual(self.dialog._tasks, [("Boceto", 1)])

    def test_remove_task(self):
        self.dialog.entry_task.set_text("Boceto")
        self.dialog._on_add_task()
        row = self.dialog.tasks_box.get_first_child()
        self.dialog._on_remove_task(None, "Boceto", row)
        self.assertEqual(self.dialog._tasks, [])


@unittest.skipUnless(display_available, "No hay display disponible")
class TestProjectView(unittest.TestCase):
    def setUp(self):
        self.view = ProjectView()
        self.window = Gtk.Window()
        self.window.set_child(self.view)
        self.window.present()

    def tearDown(self):
        self.window.destroy()

    def test_empty_view_default(self):
        self.assertEqual(self.view.get_visible_child_name(), "empty")

    def test_show_project_populates_list(self):
        tasks = [Task("Boceto", 2), Task("Tinta", 3)]
        pages = [Page(list(tasks)), Page(list(tasks))]
        project = Project("Comic", pages, workflow_type=WorkflowType.BY_TASK)

        self.view.show_project(project)
        self.assertEqual(self.view.get_visible_child_name(), "project")
        self.assertEqual(self.view.project_title.get_text(), "Comic")
        self.assertIn(WORKFLOW_LABELS[WorkflowType.BY_TASK], self.view.workflow_label.get_text())

        self.assertEqual(len(self.view.page_expanders), 2)
        first = self.view.page_expanders[0]
        self.assertIsInstance(first, Adw.ExpanderRow)
        self.assertEqual(first.get_title(), "Página 1")
        self.assertFalse(first.get_expanded())
        self.assertEqual(len(self.view.task_rows[0]), 2)
        self.assertEqual(self.view.task_rows[0][0].get_title(), "Boceto")
        self.assertEqual(self.view.task_rows[0][0].get_subtitle(), "Pendiente")

    def test_show_empty_returns_to_empty_state(self):
        self.view.show_empty()
        self.assertEqual(self.view.get_visible_child_name(), "empty")


@unittest.skipUnless(display_available, "No hay display disponible")
class TestProjectApp(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "gui_projects.db"
        app_id = "com.ulises.fancyprojects.test{}".format(id(self))
        self.app = ProjectApp(application_id=app_id)
        self.app.register()

    def tearDown(self):
        self.app.quit()
        self.tempdir.cleanup()

    def test_repository_uses_configured_db(self):
        self.app.repository = ProjectRepository(self.db_path)
        project = Project("Demo", [])
        self.app.repository.save_project(project)
        self.assertIsNotNone(self.app.repository.load_project(project.id))

    def test_create_project_applies_task_hours(self):
        window = ProjectWindow(application=self.app)
        window._create_project({
            "project_name": "Comic de superheroes",
            "pages": 2,
            "tasks": [("Boceto", 2), ("Tinta", 3)],
            "workflow_type": WorkflowType.BY_TASK,
        })
        project = window.current_project
        self.assertEqual(len(project.getPages()), 2)
        tasks = project.getPages()[0].getTasks()
        self.assertEqual(
            [(t.getTaskName(), t.getHoursPredicted()) for t in tasks],
            [("Boceto", 2), ("Tinta", 3)],
        )
        self.assertEqual(project.getTotalEstimatedHours(), 10)
        window.destroy()

    def test_picker_dialog_requires_selection(self):
        projects = [Project("A", []), Project("B", [])]
        dialog = ProjectPickerDialog(projects)
        dialog._choose()
        self.assertIsNone(dialog.get_selected_id())
        dialog.close()

    def test_picker_dialog_selects_project(self):
        projects = [Project("A", []), Project("B", [])]
        dialog = ProjectPickerDialog(projects)
        dialog.listbox.select_row(dialog.listbox.get_row_at_index(1))
        dialog._choose()
        self.assertEqual(dialog.get_selected_id(), projects[1].id)
        dialog.close()


@unittest.skipUnless(display_available, "No hay display disponible")
class TestStylesheet(unittest.TestCase):
    def test_stylesheet_loads(self):
        self.assertTrue(STYLE_CSS.exists())
        install_stylesheet()
        provider = Gtk.CssProvider()
        provider.load_from_path(str(STYLE_CSS))


if __name__ == "__main__":
    unittest.main()