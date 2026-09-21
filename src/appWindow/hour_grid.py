import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk

from appWindow.colors import COLOR_COUNT, task_color_indices
from appWindow.scrolling import scroll_into_view
from projects.Project import WorkflowType


class HourGridView(Gtk.ScrolledWindow):
    def __init__(self, on_change=None):
        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.on_change = on_change
        self.view_mode = WorkflowType.CONTINUOUS
        self._syncing = False
        self._color_index = {}
        self._project = None
        self.page_boxes = []
        self.task_checkboxes = []
        self.page_checks = []
        self._hours_slots = {}
        self._page_targets = {}

        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.container.set_margin_top(12)
        self.container.set_margin_bottom(12)
        self.container.set_margin_start(12)
        self.container.set_margin_end(12)
        self.set_child(self.container)

        self.show_empty()

    def _clear(self):
        child = self.container.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.container.remove(child)
            child = next_child

    def show_empty(self):
        self._clear()
        self.page_boxes = []
        self.task_checkboxes = []
        self.page_checks = []
        self._hours_slots = {}
        self._page_targets = {}
        self._project = None
        label = Gtk.Label(label="No hay ningún proyecto abierto")
        label.add_css_class("dim-label")
        label.set_valign(Gtk.Align.CENTER)
        label.set_vexpand(True)
        self.container.append(label)

    def set_view_mode(self, mode):
        self.view_mode = mode
        if self._project is not None:
            self.show_project(self._project)

    def show_project(self, project):
        self._clear()
        self.page_boxes = []
        self.task_checkboxes = []
        self.page_checks = []
        self._hours_slots = {}
        self._page_targets = {}
        self._project = project
        self._color_index = task_color_indices(project)

        self.container.append(self._build_legend())

        if self.view_mode == WorkflowType.BY_TASK:
            self._build_by_task(project)
        else:
            self._build_continuous(project)

    def _color(self, task_name):
        return self._color_index.get(task_name, 0) % COLOR_COUNT

    def _build_legend(self):
        legend = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        legend.add_css_class("hour-legend")
        for name, index in self._color_index.items():
            item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            dot = Gtk.Label(label="●")
            dot.add_css_class("hour-task-label-{}".format(index % COLOR_COUNT))
            text = Gtk.Label(label=name)
            text.add_css_class("caption")
            item.append(dot)
            item.append(text)
            legend.append(item)
        return legend

    def _completion_check(self, page):
        check = Gtk.Image.new_from_icon_name("object-select-symbolic")
        check.add_css_class("success")
        check.set_tooltip_text("Página completada")
        check.set_visible(page.isCompleted())
        self.page_checks.append((page, check))
        return check

    def refresh_status(self):
        for page, check in self.page_checks:
            check.set_visible(page.isCompleted())

    def scroll_to_page(self, page):
        scroll_into_view(self, self.container, self._page_targets.get(page))

    def _build_continuous(self, project):
        for page_index, page in enumerate(project.getPages(), start=1):
            page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            page_box.add_css_class("hour-page")

            header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            title = Gtk.Label(label="Página {}".format(page_index), xalign=0.0)
            title.add_css_class("heading")
            header.append(title)
            header.append(self._completion_check(page))
            page_box.append(header)

            for task in page.getTasks():
                task_box = self._build_task_box(task, page)
                page_box.append(task_box)
                self._hours_slots[(task, page)] = (task_box, task_box.get_first_child())

            self.container.append(page_box)
            self.page_boxes.append(page_box)
            self._page_targets[page] = page_box

    def _build_task_box(self, task, page):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.add_css_class("hour-task")
        box.add_css_class("hour-task-{}".format(self._color(task.getTaskName())))

        label = Gtk.Label(label=task.getTaskName(), xalign=0.0)
        label.add_css_class("caption")
        label.add_css_class("hour-task-label-{}".format(self._color(task.getTaskName())))
        box.append(label)
        box.append(self._build_hours(task, page))
        return box

    def _build_by_task(self, project):
        for task_name, index in self._color_index.items():
            group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            group.add_css_class("hour-task")
            group.add_css_class("hour-task-{}".format(index % COLOR_COUNT))

            header = Gtk.Label(label=task_name, xalign=0.0)
            header.add_css_class("heading")
            header.add_css_class("hour-task-label-{}".format(index % COLOR_COUNT))
            group.append(header)

            for page_index, page in enumerate(project.getPages(), start=1):
                task = self._find_task(page, task_name)
                if task is None:
                    continue
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                page_label = Gtk.Label(label="P{:<3}".format(page_index))
                page_label.add_css_class("dim-label")
                page_label.set_width_chars(4)
                row.append(page_label)
                check = self._completion_check(page)
                row.append(check)
                row.append(self._build_hours(task, page))
                group.append(row)
                self._hours_slots[(task, page)] = (row, check)
                self._page_targets.setdefault(page, group)

            self.container.append(group)
            self.page_boxes.append(group)

    @staticmethod
    def _find_task(page, task_name):
        for task in page.getTasks():
            if task.getTaskName() == task_name:
                return task
        return None

    def _build_hours(self, task, page):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        row.set_valign(Gtk.Align.CENTER)

        checkboxes = []
        for index in range(task.getHoursPredicted()):
            checkbox = Gtk.CheckButton()
            checkbox.set_active(index < task.getHoursCompleted())
            checkbox.set_tooltip_text("Hora {}".format(index + 1))
            checkbox.connect("toggled", self._on_hour_toggled, index, checkboxes, task, page)
            checkboxes.append(checkbox)
            row.append(checkbox)

        if not checkboxes:
            empty = Gtk.Label(label="Sin horas")
            empty.add_css_class("dim-label")
            row.append(empty)

        self.task_checkboxes.append((task, checkboxes))
        return row

    def _on_hour_toggled(self, checkbox, index, checkboxes, task, page):
        if self._syncing:
            return
        self._syncing = True
        target = index + 1 if checkbox.get_active() else index
        for position, box in enumerate(checkboxes):
            box.set_active(position < target)
        task.setHoursCompleted(target)
        self._syncing = False
        if self.on_change is not None:
            self.on_change(task, page)

    def update_task_hours(self, task, page):
        slot = self._hours_slots.get((task, page))
        if slot is None:
            return
        parent, ref = slot
        parent.remove(parent.get_last_child())
        for index, (existing, _boxes) in enumerate(self.task_checkboxes):
            if existing is task:
                del self.task_checkboxes[index]
                break
        parent.insert_child_after(self._build_hours(task, page), ref)
        self.refresh_status()