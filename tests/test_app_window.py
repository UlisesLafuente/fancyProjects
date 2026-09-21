import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk, GLib

display_available = Gtk.init_check()

from appWindow.app_window import ProjectApp, ProjectPickerDialog, ProjectWindow, install_stylesheet, STYLE_CSS, install_app_icon, APP_ICON_NAME, install_log_filter, _swallow_libadwaita_measure_warnings, _safe_filename
from appWindow.global_view import GlobalView
from appWindow.hour_grid import HourGridView
from appWindow.main_view import ProjectView
from appWindow.new_project_dialog import NewProjectDialog
from appWindow.project_options_dialog import ProjectOptionsDialog
from persistence.project_io import export_project, import_project
from persistence.project_repository import ProjectRepository
from projects.Page import Page
from projects.Project import Project, WorkflowType
from projects.Task import Task


@unittest.skipUnless(display_available, "No hay display disponible")
class TestNewProjectDialog(unittest.TestCase):
    def setUp(self):
        self.dialog = NewProjectDialog()

    def test_get_data_has_no_workflow(self):
        self.dialog.entry_name.set_text("Comic de superheroes")
        self.dialog.spin_pages.set_value(15)
        for name, hours in (("Boceto", 2), ("Tinta", 3), ("Color", 4)):
            self.dialog.entry_task.set_text(name)
            self.dialog.spin_task_hours.set_value(hours)
            self.dialog._on_add_task()
            self.dialog.entry_task.set_text("")

        data = self.dialog.get_data()
        self.assertEqual(data["project_name"], "Comic de superheroes")
        self.assertEqual(data["pages"], 15)
        self.assertEqual(data["tasks"], [("Boceto", 2), ("Tinta", 3), ("Color", 4)])
        self.assertNotIn("workflow_type", data)

    def test_validation_rejects_empty_name_and_tasks(self):
        self.dialog.entry_name.set_text("")
        self.assertFalse(self.dialog._is_valid())
        self.dialog.entry_name.set_text("Comic")
        self.assertFalse(self.dialog._is_valid())

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
class TestProjectOptionsDialog(unittest.TestCase):
    def setUp(self):
        self.project = Project("Comic", [
            Page([Task("Boceto", 2), Task("Tinta", 3)]),
            Page([Task("Boceto", 2), Task("Tinta", 3)]),
        ])
        self.dialog = ProjectOptionsDialog(self.project)

    def test_initial_state_matches_project(self):
        self.assertEqual(self.dialog.spin_pages.get_value(), 2)
        self.assertEqual(self.dialog._tasks, [("Boceto", 2), ("Tinta", 3)])

    def test_get_data_returns_pages_and_tasks(self):
        self.dialog.spin_pages.set_value(5)
        self.dialog.entry_task.set_text("Color")
        self.dialog.spin_task_hours.set_value(4)
        self.dialog._on_add_task()
        self.assertEqual(
            self.dialog.get_data(),
            {"pages": 5, "tasks": [("Boceto", 2), ("Tinta", 3), ("Color", 4)]},
        )

    def test_remove_task(self):
        row = self.dialog.tasks_box.get_first_child()
        self.dialog._on_remove_task(None, "Boceto", row)
        self.assertEqual(self.dialog._tasks, [("Tinta", 3)])

    def test_validation_requires_one_task(self):
        for name, _ in list(self.dialog._tasks):
            row = self.dialog.tasks_box.get_first_child()
            self.dialog._on_remove_task(None, name, row)
        self.assertFalse(self.dialog._is_valid())


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
        project = Project("Comic", pages)

        self.view.show_project(project)
        self.assertEqual(self.view.get_visible_child_name(), "project")
        self.assertEqual(self.view.project_title.get_text(), "Comic")

        self.assertEqual(len(self.view.page_expanders), 2)
        first = self.view.page_expanders[0]
        self.assertIsInstance(first, Adw.ExpanderRow)
        self.assertEqual(first.get_title(), "Página 1")
        self.assertFalse(first.get_expanded())
        self.assertEqual(len(self.view.task_rows[0]), 2)
        self.assertEqual(self.view.task_rows[0][0].get_title(), "Boceto")
        self.assertEqual(self.view.task_rows[0][0].get_subtitle(), "Pendiente · 0 / 2 h")

    def test_show_empty_returns_to_empty_state(self):
        self.view.show_empty()
        self.assertEqual(self.view.get_visible_child_name(), "empty")

    def test_refresh_preserves_expansion(self):
        tasks = [Task("Boceto", 2), Task("Tinta", 3)]
        pages = [Page(list(tasks)), Page(list(tasks))]
        project = Project("Comic", pages)

        self.view.show_project(project)
        self.view.page_expanders[1].set_expanded(True)

        self.view.refresh(project)
        self.assertEqual(len(self.view.page_expanders), 2)
        self.assertFalse(self.view.page_expanders[0].get_expanded())
        self.assertTrue(self.view.page_expanders[1].get_expanded())

    def test_refresh_updates_widgets_in_place(self):
        task = Task("Boceto", 2)
        project = Project("Comic", [Page([task])])
        self.view.show_project(project)
        row = self.view.task_rows[0][0]
        stepper = self.view.task_steppers[0][0]

        task.setHoursCompleted(1)
        self.view.refresh(project)

        self.assertEqual(row.get_subtitle(), "Pendiente · 1 / 2 h")
        self.assertEqual(stepper.get_hours(), 2)

        task.setHoursCompleted(2)
        self.view.refresh(project)
        self.assertEqual(row.get_subtitle(), "Completada · 2 / 2 h")

    def test_refresh_page_only_updates_that_page(self):
        tasks = [Task("Boceto", 2)]
        project = Project("Comic", [Page(list(tasks)), Page(list(tasks))])
        self.view.show_project(project)

        project.getPages()[0].getTasks()[0].setHoursCompleted(2)
        self.view.refresh_page(project, project.getPages()[0])

        self.assertEqual(self.view.task_rows[0][0].get_subtitle(), "Completada · 2 / 2 h")
        self.assertEqual(self.view.task_rows[1][0].get_subtitle(), "Pendiente · 0 / 2 h")
        self.assertIsNotNone(self.view.completion_checks[0])
        self.assertFalse(self.view.completion_checks[1].get_visible())

    def test_refresh_rebuilds_when_structure_changes(self):
        project = Project("Comic", [Page([Task("Boceto", 2)]), Page([Task("Tinta", 3)])])
        self.view.show_project(project)
        project.getPages().pop()

        self.view.refresh(project)
        self.assertEqual(len(self.view.page_expanders), 1)

    def test_completed_page_shows_check(self):
        done = Task("Boceto", 2)
        done.setHoursCompleted(2)
        pending = Task("Boceto", 2)
        project = Project("Comic", [Page([done]), Page([pending])])

        self.view.show_project(project)
        self.assertTrue(self.view.completion_checks[0].get_visible())
        self.assertFalse(self.view.completion_checks[1].get_visible())

    def test_completion_check_appears_after_refresh(self):
        task = Task("Boceto", 2)
        project = Project("Comic", [Page([task])])

        self.view.show_project(project)
        self.assertFalse(self.view.completion_checks[0].get_visible())

        task.setHoursCompleted(2)
        self.view.refresh(project)
        self.assertTrue(self.view.completion_checks[0].get_visible())

    def test_completed_page_gets_green_background(self):
        done = Task("Boceto", 2)
        done.setHoursCompleted(2)
        pending = Task("Boceto", 2)
        project = Project("Comic", [Page([done]), Page([pending])])

        self.view.show_project(project)
        self.assertTrue(self.view.page_expanders[0].has_css_class("page-completed"))
        self.assertFalse(self.view.page_expanders[1].has_css_class("page-completed"))

    def test_completed_task_gets_green_background(self):
        done = Task("Boceto", 2)
        done.setHoursCompleted(2)
        pending = Task("Tinta", 3)
        project = Project("Comic", [Page([done, pending])])

        self.view.show_project(project)
        self.assertTrue(self.view.task_rows[0][0].has_css_class("task-completed"))
        self.assertFalse(self.view.task_rows[0][1].has_css_class("task-completed"))

    def test_refresh_toggles_green_background(self):
        task = Task("Boceto", 2)
        project = Project("Comic", [Page([task])])

        self.view.show_project(project)
        self.assertFalse(self.view.task_rows[0][0].has_css_class("task-completed"))
        self.assertFalse(self.view.page_expanders[0].has_css_class("page-completed"))

        task.setHoursCompleted(2)
        self.view.refresh(project)
        self.assertTrue(self.view.task_rows[0][0].has_css_class("task-completed"))
        self.assertTrue(self.view.page_expanders[0].has_css_class("page-completed"))

        task.setHoursCompleted(0)
        self.view.refresh(project)
        self.assertFalse(self.view.task_rows[0][0].has_css_class("task-completed"))
        self.assertFalse(self.view.page_expanders[0].has_css_class("page-completed"))

    def test_task_row_has_hours_stepper(self):
        project = Project("Comic", [Page([Task("Boceto", 2)])])
        self.view.show_project(project)
        stepper = self.view.task_steppers[0][0]
        self.assertEqual(stepper.get_hours(), 2)
        self.assertEqual(stepper.entry.get_text(), "2")

    def test_page_fill_uses_last_completed_task_color(self):
        boceto = Task("Boceto", 2)
        tinta = Task("Tinta", 3)
        project = Project("Comic", [Page([boceto, tinta])])
        self.view.show_project(project)
        self.assertTrue(self.view.page_expanders[0].has_css_class("page-fill-neutral"))

        boceto.setHoursCompleted(2)
        self.view.refresh(project)
        self.assertTrue(self.view.page_expanders[0].has_css_class("page-fill-0"))

        tinta.setHoursCompleted(3)
        self.view.refresh(project)
        self.assertTrue(self.view.page_expanders[0].has_css_class("page-fill-1"))
        self.assertFalse(self.view.page_expanders[0].has_css_class("page-fill-0"))

    def test_page_fill_returns_to_neutral_when_uncompleted(self):
        task = Task("Boceto", 2)
        project = Project("Comic", [Page([task])])
        self.view.show_project(project)
        task.setHoursCompleted(2)
        self.view.refresh(project)
        self.assertTrue(self.view.page_expanders[0].has_css_class("page-fill-0"))

        task.setHoursCompleted(0)
        self.view.refresh(project)
        self.assertTrue(self.view.page_expanders[0].has_css_class("page-fill-neutral"))
        self.assertFalse(self.view.page_expanders[0].has_css_class("page-fill-0"))

    def test_plus_increments_estimated_hours(self):
        changes = []
        view = ProjectView(on_estimated_hours_change=lambda t, p: changes.append(t))
        project = Project("Comic", [Page([Task("Boceto", 2)])])
        view.show_project(project)
        task = project.getPages()[0].getTasks()[0]

        view.task_steppers[0][0]._on_plus()

        self.assertEqual(task.getHoursPredicted(), 3)
        self.assertEqual(task.getHoursLeft(), 3)
        self.assertEqual(changes, [task])

    def test_minus_decrements_estimated_hours(self):
        view = ProjectView()
        project = Project("Comic", [Page([Task("Boceto", 3)])])
        view.show_project(project)
        task = project.getPages()[0].getTasks()[0]

        view.task_steppers[0][0]._on_minus()

        self.assertEqual(task.getHoursPredicted(), 2)
        self.assertEqual(view.task_steppers[0][0].get_hours(), 2)

    def test_minus_floors_at_one(self):
        view = ProjectView()
        project = Project("Comic", [Page([Task("Boceto", 1)])])
        view.show_project(project)
        task = project.getPages()[0].getTasks()[0]

        view.task_steppers[0][0]._on_minus()

        self.assertEqual(task.getHoursPredicted(), 1)
        self.assertEqual(view.task_steppers[0][0].get_hours(), 1)

    def test_entry_commit_applies_value(self):
        view = ProjectView()
        project = Project("Comic", [Page([Task("Boceto", 2)])])
        view.show_project(project)
        task = project.getPages()[0].getTasks()[0]

        stepper = view.task_steppers[0][0]
        stepper.entry.set_text("7")
        stepper._on_entry_commit()

        self.assertEqual(task.getHoursPredicted(), 7)
        self.assertEqual(stepper.get_hours(), 7)

    def test_entry_commit_rejects_invalid_values(self):
        view = ProjectView()
        project = Project("Comic", [Page([Task("Boceto", 2)])])
        view.show_project(project)
        task = project.getPages()[0].getTasks()[0]

        stepper = view.task_steppers[0][0]
        stepper.entry.set_text("abc")
        stepper._on_entry_commit()
        self.assertEqual(task.getHoursPredicted(), 2)
        self.assertEqual(stepper.get_hours(), 2)

        stepper.entry.set_text("0")
        stepper._on_entry_commit()
        self.assertEqual(task.getHoursPredicted(), 2)
        self.assertEqual(stepper.get_hours(), 2)

        stepper.entry.set_text("2000")
        stepper._on_entry_commit()
        self.assertEqual(task.getHoursPredicted(), 2)
        self.assertEqual(stepper.get_hours(), 2)


@unittest.skipUnless(display_available, "No hay display disponible")
class TestGlobalView(unittest.TestCase):
    def setUp(self):
        self.view = GlobalView()
        self.window = Gtk.Window()
        self.window.set_child(self.view)
        self.window.present()

    def tearDown(self):
        self.window.destroy()

    @staticmethod
    def _make_project(pages=3):
        return Project(
            "Comic",
            [Page([Task("Boceto", 2), Task("Tinta", 3)]) for _ in range(pages)],
        )

    @staticmethod
    def _children(widget):
        children = []
        child = widget.get_first_child()
        while child is not None:
            children.append(child)
            child = child.get_next_sibling()
        return children

    def test_separated_builds_one_rect_per_page(self):
        project = self._make_project(3)
        self.view.show_project(project)
        self.assertEqual(len(self.view.page_widgets), 3)

    def test_spread_groups_first_alone_then_pairs(self):
        project = self._make_project(5)
        self.view.set_pages_mode(GlobalView.SPREAD)
        self.view.show_project(project)
        self.assertEqual(len(self.view.page_widgets), 5)
        rows = self._children(self.view.container)
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(self._children(rows[0])), 1)
        self.assertEqual(len(self._children(rows[1])), 2)
        self.assertEqual(len(self._children(rows[2])), 2)

    def test_spread_odd_last_page_alone(self):
        project = self._make_project(4)
        self.view.set_pages_mode(GlobalView.SPREAD)
        self.view.show_project(project)
        rows = self._children(self.view.container)
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(self._children(rows[0])), 1)
        self.assertEqual(len(self._children(rows[1])), 2)
        self.assertEqual(len(self._children(rows[2])), 1)

    def test_color_uses_last_completed_task(self):
        boceto = Task("Boceto", 2)
        tinta = Task("Tinta", 3)
        project = Project("Comic", [Page([boceto, tinta])])
        self.view.show_project(project)
        page, _, rect, _ = self.view.page_widgets[0]
        self.assertTrue(rect.has_css_class("global-page-neutral"))

        boceto.setHoursCompleted(2)
        self.view.refresh_status()
        self.assertTrue(rect.has_css_class("global-page-fill-0"))

        tinta.setHoursCompleted(3)
        self.view.refresh_status()
        self.assertTrue(rect.has_css_class("global-page-fill-1"))
        self.assertFalse(rect.has_css_class("global-page-fill-0"))

    def test_caption_shows_page_number_and_percent(self):
        project = self._make_project(1)
        self.view.show_project(project)
        _, page_index, _, caption = self.view.page_widgets[0]
        self.assertEqual(page_index, 1)
        self.assertIn("Página 1", caption.get_text())
        self.assertIn("0 %", caption.get_text())

    def test_show_empty_clears_widgets(self):
        project = self._make_project(2)
        self.view.show_project(project)
        self.view.show_empty()
        self.assertEqual(self.view.page_widgets, [])

    def test_click_on_page_invokes_callback(self):
        clicked = []
        self.view.on_page_click = clicked.append
        project = self._make_project(2)
        self.view.show_project(project)
        self.view._on_page_released(None, 1, 0.0, 0.0, project.getPages()[1])
        self.assertEqual(clicked, [project.getPages()[1]])

    def test_page_boxes_have_click_controller(self):
        project = self._make_project(1)
        self.view.show_project(project)
        box = self.view.page_boxes[0]
        controllers = box.observe_controllers()
        self.assertGreaterEqual(controllers.get_n_items(), 1)


@unittest.skipUnless(display_available, "No hay display disponible")
class TestHourGridView(unittest.TestCase):
    def setUp(self):
        self.changes = []
        self.view = HourGridView(on_change=lambda *_: self.changes.append(True))
        self.window = Gtk.Window()
        self.window.set_child(self.view)
        self.window.present()

    def tearDown(self):
        self.window.destroy()

    @staticmethod
    def _make_project():
        pages = [
            Page([Task("Boceto", 2), Task("Tinta", 3)]),
            Page([Task("Boceto", 2), Task("Tinta", 3)]),
        ]
        return Project("Comic", pages)

    def test_continuous_creates_page_and_task_boxes(self):
        project = self._make_project()
        self.view.show_project(project)
        self.assertEqual(len(self.view.page_boxes), 2)
        self.assertEqual(len(self.view.task_checkboxes), 4)
        first_task, checkboxes = self.view.task_checkboxes[0]
        self.assertEqual(first_task.getTaskName(), "Boceto")
        self.assertEqual(len(checkboxes), 2)

    def test_by_task_groups_one_box_per_task_type(self):
        self.view.set_view_mode(WorkflowType.BY_TASK)
        project = self._make_project()
        self.view.show_project(project)
        self.assertEqual(len(self.view.page_boxes), 2)
        self.assertEqual(len(self.view.task_checkboxes), 4)

    def test_toggling_hour_updates_task(self):
        project = self._make_project()
        self.view.show_project(project)
        task, checkboxes = self.view.task_checkboxes[0]
        checkboxes[0].set_active(True)
        self.assertEqual(task.getHoursCompleted(), 1)
        self.assertEqual(len(self.changes), 1)

    def test_toggling_fills_previous_hours(self):
        project = self._make_project()
        self.view.show_project(project)
        task, checkboxes = self.view.task_checkboxes[1]
        checkboxes[2].set_active(True)
        self.assertEqual(task.getHoursCompleted(), 3)
        self.assertTrue(all(box.get_active() for box in checkboxes))

    def test_unchecking_clears_following_hours(self):
        project = self._make_project()
        self.view.show_project(project)
        task, checkboxes = self.view.task_checkboxes[1]
        task.setHoursCompleted(3)
        self.view.show_project(project)
        task, checkboxes = self.view.task_checkboxes[1]
        checkboxes[1].set_active(False)
        self.assertEqual(task.getHoursCompleted(), 1)
        self.assertFalse(checkboxes[2].get_active())

    def test_show_empty_clears_grid(self):
        project = self._make_project()
        self.view.show_project(project)
        self.view.show_empty()
        self.assertEqual(self.view.task_checkboxes, [])

    def test_page_check_hidden_until_completed(self):
        project = self._make_project()
        self.view.show_project(project)
        self.assertEqual(len(self.view.page_checks), 2)
        self.assertFalse(self.view.page_checks[0][1].get_visible())

        for task in project.getPages()[0].getTasks():
            task.setHoursCompleted(task.getHoursPredicted())
        self.view.refresh_status()

        self.assertTrue(self.view.page_checks[0][1].get_visible())
        self.assertFalse(self.view.page_checks[1][1].get_visible())

    def test_checking_all_hours_marks_page_completed(self):
        project = self._make_project()
        self.view.show_project(project)
        for _, checkboxes in self.view.task_checkboxes[:2]:
            checkboxes[-1].set_active(True)
        self.view.refresh_status()
        self.assertTrue(self.view.page_checks[0][1].get_visible())
        self.assertFalse(self.view.page_checks[1][1].get_visible())

    def test_set_view_mode_rerenders_current_project(self):
        project = self._make_project()
        self.view.show_project(project)
        self.view.set_view_mode(WorkflowType.BY_TASK)
        self.assertEqual(self.view.view_mode, WorkflowType.BY_TASK)
        self.assertEqual(len(self.view.task_checkboxes), 4)

    def test_update_task_hours_replaces_only_that_hours_row(self):
        project = self._make_project()
        self.view.show_project(project)
        task, _ = self.view.task_checkboxes[0]
        self.view.update_task_hours(task, project.getPages()[0])
        entry = next((t, boxes) for t, boxes in self.view.task_checkboxes if t is task)
        self.assertEqual(len(entry[1]), 2)


@unittest.skipUnless(display_available, "No hay display disponible")
class TestProjectApp(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "gui_projects.db"
        app_id = "com.ulises.fanzyprojects.test{}".format(id(self))
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

    def test_project_options_add_and_remove_tasks(self):
        window = ProjectWindow(application=self.app)
        window._create_project({
            "project_name": "Comic",
            "pages": 2,
            "tasks": [("Boceto", 2), ("Tinta", 3)],
        })
        window._apply_project_options({
            "pages": 2,
            "tasks": [("Boceto", 2), ("Tinta", 3), ("Color", 4)],
        })
        project = window.current_project
        self.assertTrue(window._dirty)
        self.assertEqual(
            [(t.getTaskName(), t.getEstimatedHours()) for t in project.getPages()[0].getTasks()],
            [("Boceto", 2), ("Tinta", 3), ("Color", 4)],
        )
        self.assertEqual(
            [(t.getTaskName(), t.getEstimatedHours()) for t in project.getPages()[1].getTasks()],
            [("Boceto", 2), ("Tinta", 3), ("Color", 4)],
        )

        window._apply_project_options({"pages": 2, "tasks": [("Boceto", 5)]})
        self.assertEqual(
            [(t.getTaskName(), t.getEstimatedHours()) for t in project.getPages()[1].getTasks()],
            [("Boceto", 5)],
        )
        window.destroy()

    def test_project_options_change_page_count(self):
        window = ProjectWindow(application=self.app)
        window._create_project({
            "project_name": "Comic",
            "pages": 2,
            "tasks": [("Boceto", 2)],
        })
        project = window.current_project
        project.getPages()[-1].getTasks()[0].setHoursCompleted(2)

        window._apply_project_options({"pages": 4, "tasks": [("Boceto", 2)]})
        self.assertEqual(len(project.getPages()), 4)
        self.assertTrue(project.getPages()[1].getTasks()[0].getCompletedTask())
        self.assertFalse(project.getPages()[2].getTasks()[0].getCompletedTask())

        window._apply_project_options({"pages": 1, "tasks": [("Boceto", 2)]})
        self.assertEqual(len(project.getPages()), 1)
        window.destroy()

    def test_window_shows_three_columns(self):
        window = ProjectWindow(application=self.app)
        window._create_project({
            "project_name": "Comic de superheroes",
            "pages": 2,
            "tasks": [("Boceto", 2), ("Tinta", 3)],
        })
        self.assertIs(window.paned.get_start_child(), window.view)
        self.assertIs(window.paned.get_end_child(), window.right_paned)
        self.assertIs(window.right_paned.get_start_child(), window.hour_view)
        self.assertIs(window.right_paned.get_end_child(), window.global_view)
        self.assertTrue(window.view.get_visible())
        self.assertTrue(window.hour_view.get_visible())
        self.assertTrue(window.global_view.get_visible())
        self.assertEqual(len(window.hour_view.task_checkboxes), 4)
        window.destroy()

    def test_column_toggles_hide_and_show_views(self):
        window = ProjectWindow(application=self.app)
        window._create_project({
            "project_name": "Comic",
            "pages": 1,
            "tasks": [("Boceto", 2)],
        })
        window._set_column_visible("hours", False)
        self.assertFalse(window.hour_view.get_visible())
        self.assertTrue(window.global_view.get_visible())
        window._set_column_visible("hours", True)
        self.assertTrue(window.hour_view.get_visible())
        window._set_column_visible("global", False)
        self.assertFalse(window.global_view.get_visible())
        window.destroy()

    def test_global_page_click_expands_page_in_project_view(self):
        window = ProjectWindow(application=self.app)
        window._create_project({
            "project_name": "Comic",
            "pages": 3,
            "tasks": [("Boceto", 2)],
        })
        page = window.current_project.getPages()[1]
        window._on_global_page_clicked(page)
        self.assertTrue(window.view.page_expanders[1].get_expanded())
        self.assertFalse(window.view.page_expanders[0].get_expanded())
        window.destroy()

    def test_pages_mode_toggles_global_view(self):
        window = ProjectWindow(application=self.app)
        window._create_project({
            "project_name": "Comic",
            "pages": 3,
            "tasks": [("Boceto", 2)],
        })
        window._set_pages_mode(GlobalView.SPREAD)
        self.assertEqual(window.global_view.pages_mode, GlobalView.SPREAD)
        window._set_pages_mode(GlobalView.SEPARATED)
        self.assertEqual(window.global_view.pages_mode, GlobalView.SEPARATED)
        window.destroy()

    def test_headerbar_has_app_icon(self):
        window = ProjectWindow(application=self.app)
        self.assertIsInstance(window.app_icon, Gtk.Image)
        self.assertEqual(window.app_icon.get_pixel_size(), 24)
        self.assertEqual(window.app_icon.get_icon_name(), APP_ICON_NAME)
        window.destroy()

    def test_close_request_prompts_only_when_dirty(self):
        window = ProjectWindow(application=self.app)
        window._create_project({
            "project_name": "Comic",
            "pages": 1,
            "tasks": [("Boceto", 2)],
        })
        self.assertFalse(window._on_close_request())
        window._dirty = True
        calls = []
        window._guard_before_discard = lambda proceed: calls.append(proceed)
        self.assertTrue(window._on_close_request())
        self.assertEqual(len(calls), 1)
        window.destroy()

    def test_dirty_flag_and_save_flow(self):
        window = ProjectWindow(application=self.app)
        window._create_project({
            "project_name": "Comic",
            "pages": 1,
            "tasks": [("Boceto", 2)],
        })
        self.assertFalse(window._dirty)
        window._on_hours_changed(None, None)
        self.assertTrue(window._dirty)
        window._on_save_clicked()
        self.assertFalse(window._dirty)
        window.destroy()

    def test_guard_runs_immediately_when_clean(self):
        window = ProjectWindow(application=self.app)
        window._create_project({
            "project_name": "Comic",
            "pages": 1,
            "tasks": [("Boceto", 2)],
        })
        ran = []
        window._guard_before_discard(lambda: ran.append(True))
        self.assertEqual(ran, [True])
        self.assertIsNotNone(window.current_project)
        window.destroy()

    def test_view_workflow_toggles_hour_view(self):
        window = ProjectWindow(application=self.app)
        window._create_project({
            "project_name": "Comic",
            "pages": 1,
            "tasks": [("Boceto", 2)],
        })
        window._apply_view_mode(WorkflowType.BY_TASK)
        self.assertEqual(window.view_mode, WorkflowType.BY_TASK)
        self.assertEqual(window.hour_view.view_mode, WorkflowType.BY_TASK)
        self.assertEqual(len(window.hour_view.task_checkboxes), 1)
        window._apply_view_mode(WorkflowType.CONTINUOUS)
        self.assertEqual(window.hour_view.view_mode, WorkflowType.CONTINUOUS)
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

    def test_safe_filename_sanitizes(self):
        self.assertEqual(_safe_filename("Comic de heroes"), "Comic de heroes")
        self.assertEqual(_safe_filename("A/B:C\\D"), "A-B-C-D")
        self.assertEqual(_safe_filename("   "), "proyecto")


@unittest.skipUnless(display_available, "No hay display disponible")
class TestImportExportDelete(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "io_projects.db"
        app_id = "com.ulises.fanzyprojects.testio{}".format(id(self))
        self.app = ProjectApp(application_id=app_id)
        self.app.register()
        self.app.repository = ProjectRepository(self.db_path)
        self.window = ProjectWindow(application=self.app)

    def tearDown(self):
        self.window.destroy()
        self.app.quit()
        self.tempdir.cleanup()

    def _open_saved_project(self):
        project = Project("Comic", [Page([Task("Boceto", 2), Task("Tinta", 3)])])
        self.app.repository.save_project(project)
        self.window._open_project(project.id)
        return project

    def test_import_file_creates_and_opens_project(self):
        path = Path(self.tempdir.name) / "comic.fancyproject"
        export_project(Project("Comic", [Page([Task("Boceto", 2)])]), path)

        self.window._import_file(path)

        project = self.window.current_project
        self.assertIsNotNone(project)
        self.assertEqual(project.projectName, "Comic")
        self.assertIsNotNone(project.id)
        self.assertEqual(self.window.view.get_visible_child_name(), "project")
        self.assertEqual(len(self.window.hour_view.task_checkboxes), 1)
        self.assertEqual(len(self.app.repository.list_projects()), 1)

    def test_import_file_invalid_reports_error_without_changes(self):
        path = Path(self.tempdir.name) / "malo.fancyproject"
        path.write_text("no json", encoding="utf-8")
        self.window._import_file(path)
        self.assertIsNone(self.window.current_project)
        self.assertEqual(self.app.repository.list_projects(), [])

    def test_export_to_writes_isolated_file(self):
        self._open_saved_project()
        path = Path(self.tempdir.name) / "copia.fancyproject"

        self.window._export_to(path)

        restored = import_project(path)
        self.assertEqual(restored.projectName, "Comic")
        self.assertEqual(restored.getTotalEstimatedHours(), 5)
        self.assertIn("copia.fancyproject", self.window.status_label.get_text())

    def test_editing_estimated_hours_updates_views(self):
        self._open_saved_project()
        project = self.window.current_project
        task = project.getPages()[0].getTasks()[0]
        def checkboxes_of(t):
            return next(boxes for existing, boxes in self.window.hour_view.task_checkboxes if existing is t)
        self.assertEqual(len(checkboxes_of(task)), 2)

        task.setEstimatedHours(6)
        self.window._on_estimated_hours_changed(task, project.getPages()[0])

        self.assertEqual(len(checkboxes_of(task)), 6)
        self.assertEqual(
            self.window.view.task_rows[0][0].get_subtitle(), "Pendiente · 0 / 6 h"
        )
        self.assertIn("6 h", self.window.status_label.get_text())

    def test_delete_confirmed_removes_project(self):
        project = self._open_saved_project()
        self.assertEqual(len(self.app.repository.list_projects()), 1)

        self.window._on_delete_confirmed(None, "delete", project.id)

        self.assertEqual(self.app.repository.list_projects(), [])
        self.assertIsNone(self.window.current_project)
        self.assertEqual(self.window.view.get_visible_child_name(), "empty")

    def test_delete_cancelled_keeps_project(self):
        project = self._open_saved_project()
        self.window._on_delete_confirmed(None, "cancel", project.id)
        self.assertEqual(len(self.app.repository.list_projects()), 1)
        self.assertIsNotNone(self.window.current_project)

    def test_close_project_returns_to_empty_state(self):
        self._open_saved_project()
        self.assertEqual(self.window.view.get_visible_child_name(), "project")

        self.window._on_close_clicked()

        self.assertIsNone(self.window.current_project)
        self.assertEqual(self.window.view.get_visible_child_name(), "empty")
        self.assertEqual(self.window.hour_view.task_checkboxes, [])
        self.assertIn("cerrado", self.window.status_label.get_text())

    def test_close_without_project_shows_info(self):
        self.assertIsNone(self.window.current_project)
        self.window._on_close_clicked()
        self.assertEqual(self.window.view.get_visible_child_name(), "empty")


@unittest.skipUnless(display_available, "No hay display disponible")
class TestStylesheet(unittest.TestCase):
    def test_stylesheet_loads(self):
        self.assertTrue(STYLE_CSS.exists())
        install_stylesheet()
        provider = Gtk.CssProvider()
        provider.load_from_path(str(STYLE_CSS))


@unittest.skipUnless(display_available, "No hay display disponible")
class TestAppIcon(unittest.TestCase):
    def test_res_icon_exists(self):
        from appWindow.app_window import get_res_dir

        icon = get_res_dir() / (APP_ICON_NAME + ".svg")
        self.assertTrue(icon.is_file())

    def test_install_app_icon_registers_name(self):
        install_app_icon()
        self.assertEqual(Gtk.Window.get_default_icon_name(), APP_ICON_NAME)

    def test_icon_resolves_in_theme(self):
        from gi.repository import Gdk

        install_app_icon()
        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        icon = theme.lookup_icon(APP_ICON_NAME, None, 48, 1, Gtk.TextDirection.LTR, 0)
        self.assertIsNotNone(icon)


@unittest.skipUnless(display_available, "No hay display disponible")
class TestLogFilter(unittest.TestCase):
    def setUp(self):
        self._original_handler = GLib.log_default_handler

    def tearDown(self):
        GLib.log_default_handler = self._original_handler

    def test_installs_once(self):
        install_log_filter()
        install_log_filter()

    def _spy(self):
        calls = []
        GLib.log_default_handler = lambda d, l, m: calls.append(m)
        return calls

    def test_matching_measure_warning_is_swallowed(self):
        calls = self._spy()
        _swallow_libadwaita_measure_warnings(
            None,
            GLib.LogLevelFlags.LEVEL_WARNING,
            "AdwBreakpointBin reported min height 613 and natural height 512 in "
            "measure() with for_size=572; natural size must be >= min size",
        )
        self.assertEqual(calls, [])

    def test_other_warnings_pass_through(self):
        calls = self._spy()
        _swallow_libadwaita_measure_warnings(
            None, GLib.LogLevelFlags.LEVEL_WARNING, "otra cosa"
        )
        self.assertEqual(calls, ["otra cosa"])


if __name__ == "__main__":
    unittest.main()