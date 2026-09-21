import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

from appWindow.new_project_dialog import WORKFLOW_LABELS


def _task_subtitle(task):
    state = "Completada" if task.getCompletedTask() else "Pendiente"
    return "{} · {:.0f} / {:.0f} h".format(
        state, task.getHoursCompleted(), task.getHoursPredicted()
    )


class HoursStepper(Gtk.Box):
    MIN_HOURS = 1
    MAX_HOURS = 1000

    def __init__(self, hours, on_change=None):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        self._hours = int(hours)
        self._on_change = on_change

        self.minus = Gtk.Button()
        self.minus.set_child(Gtk.Image.new_from_icon_name("list-remove-symbolic"))
        self.minus.add_css_class("flat")
        self.minus.set_tooltip_text("Reducir horas estimadas")
        self.minus.connect("clicked", self._on_minus)

        self.entry = Gtk.Entry()
        self.entry.set_width_chars(3)
        self.entry.set_max_length(4)
        self.entry.set_text(str(self._hours))
        self.entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
        self.entry.connect("activate", self._on_entry_commit)
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect("leave", self._on_entry_commit)
        self.entry.add_controller(focus_controller)

        self.plus = Gtk.Button()
        self.plus.set_child(Gtk.Image.new_from_icon_name("list-add-symbolic"))
        self.plus.add_css_class("flat")
        self.plus.set_tooltip_text("Aumentar horas estimadas")
        self.plus.connect("clicked", self._on_plus)

        hours_label = Gtk.Label(label=" h")
        hours_label.add_css_class("dim-label")

        self.append(self.minus)
        self.append(self.entry)
        self.append(self.plus)
        self.append(hours_label)

    def _emit(self, value):
        if not (self.MIN_HOURS <= value <= self.MAX_HOURS) or value == self._hours:
            self.entry.set_text(str(self._hours))
            return
        self._hours = value
        self.entry.set_text(str(value))
        if self._on_change is not None:
            self._on_change(value)

    def _on_plus(self, *args):
        self._emit(self._hours + 1)

    def _on_minus(self, *args):
        self._emit(self._hours - 1)

    def _on_entry_commit(self, *args):
        text = self.entry.get_text().strip()
        try:
            value = int(text)
        except ValueError:
            self.entry.set_text(str(self._hours))
            return
        self._emit(value)

    def set_hours(self, hours):
        self._hours = int(hours)
        self.entry.set_text(str(self._hours))

    def get_hours(self):
        return self._hours


class ProjectView(Gtk.Stack):
    def __init__(self, on_estimated_hours_change=None):
        super().__init__()
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.on_estimated_hours_change = on_estimated_hours_change

        self.page_expanders = []
        self.task_rows = []
        self.task_steppers = []
        self.completion_checks = []

        self.empty_page = self._build_empty_page()
        self.project_page = self._build_project_page()
        self.add_named(self.empty_page, "empty")
        self.add_named(self.project_page, "project")
        self.show_empty()

    def _build_empty_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        icon = Gtk.Image.new_from_icon_name("folder-documents-symbolic")
        icon.set_pixel_size(64)
        icon.set_opacity(0.4)

        title = Gtk.Label(label="No hay ningún proyecto abierto")
        title.add_css_class("dim-label")

        hint = Gtk.Label(label="Usa File ▸ Nuevo proyecto para crear uno,\no File ▸ Abrir para cargar uno guardado.")
        hint.add_css_class("dim-label")

        box.append(icon)
        box.append(title)
        box.append(hint)
        return box

    def _build_project_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(12)
        page.set_margin_bottom(12)
        page.set_margin_start(18)
        page.set_margin_end(18)

        self.header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.project_title = Gtk.Label(label="", xalign=0.0)
        self.project_title.add_css_class("title-1")
        self.workflow_label = Gtk.Label(label="", xalign=0.0)
        self.workflow_label.add_css_class("dim-label")
        self.summary_label = Gtk.Label(label="", xalign=0.0)
        self.summary_label.add_css_class("dim-label")

        self.header_box.append(self.project_title)
        self.header_box.append(self.workflow_label)
        self.header_box.append(self.summary_label)
        page.append(self.header_box)

        self.pages_list = Gtk.ListBox()
        self.pages_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.pages_list.add_css_class("boxed-list")

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.pages_list)
        page.append(scrolled)
        return page

    def show_empty(self):
        self.set_visible_child_name("empty")

    def refresh(self, project):
        if not self._matches(project):
            self.show_project(project)
            return
        self._update_summary(project)
        for index, page in enumerate(project.getPages()):
            self._refresh_page_at(index, page)

    def refresh_page(self, project, page):
        if not self._matches(project):
            self.show_project(project)
            return
        try:
            index = project.getPages().index(page)
        except ValueError:
            self.refresh(project)
            return
        self._refresh_page_at(index, page)
        self._update_summary(project)

    def _matches(self, project):
        if self.get_visible_child_name() != "project":
            return False
        pages = project.getPages()
        if len(pages) != len(self.page_expanders):
            return False
        for index, page in enumerate(pages):
            if len(page.getTasks()) != len(self.task_rows[index]):
                return False
        return True

    def _refresh_page_at(self, index, page):
        expander = self.page_expanders[index]
        expander.set_subtitle(
            "{:.0f} h estimadas · {:.0f}% completado".format(
                page.getTotalEstimatedHours(),
                page.getPercentileCompleted(),
            )
        )
        self.completion_checks[index].set_visible(page.isCompleted())
        self._set_completed(expander, page.isCompleted(), "page-completed")
        for task, row, stepper in zip(page.getTasks(), self.task_rows[index], self.task_steppers[index]):
            row.set_subtitle(_task_subtitle(task))
            self._set_completed(row, task.getCompletedTask(), "task-completed")
            stepper.set_hours(task.getHoursPredicted())

    def _on_stepper_change(self, task, page, value):
        task.setEstimatedHours(value)
        if self.on_estimated_hours_change is not None:
            self.on_estimated_hours_change(task, page)

    @staticmethod
    def _set_completed(widget, completed, css_class):
        if completed:
            widget.add_css_class(css_class)
        else:
            widget.remove_css_class(css_class)

    def _update_summary(self, project):
        self.summary_label.set_text(
            "{:.0f} h estimadas · {:.0f} h completadas · {:.0f}% completado".format(
                project.getTotalEstimatedHours(),
                project.getTotalCompletedHours(),
                project.percentComplete(),
            )
        )

    def show_project(self, project):
        self.set_visible_child_name("project")

        self.project_title.set_text(project.projectName)
        self.workflow_label.set_text(WORKFLOW_LABELS.get(project.workflow_type, project.workflow_type))
        self._update_summary(project)

        self.pages_list.remove_all()
        self.page_expanders = []
        self.task_rows = []
        self.task_steppers = []
        self.completion_checks = []

        for page_index, page in enumerate(project.getPages(), start=1):
            expander = Adw.ExpanderRow()
            expander.set_title("Página {}".format(page_index))
            expander.set_subtitle(
                "{:.0f} h estimadas · {:.0f}% completado".format(
                    page.getTotalEstimatedHours(),
                    page.getPercentileCompleted(),
                )
            )
            check = Gtk.Image.new_from_icon_name("object-select-symbolic")
            check.add_css_class("success")
            check.set_tooltip_text("Página completada")
            check.set_visible(page.isCompleted())
            expander.add_suffix(check)
            self.completion_checks.append(check)
            self._set_completed(expander, page.isCompleted(), "page-completed")

            task_rows = []
            task_steppers = []
            for task in page.getTasks():
                row = Adw.ActionRow(title=task.getTaskName())
                row.set_subtitle(_task_subtitle(task))
                self._set_completed(row, task.getCompletedTask(), "task-completed")
                stepper = HoursStepper(
                    task.getHoursPredicted(),
                    on_change=lambda value, t=task, p=page: self._on_stepper_change(t, p, value),
                )
                row.add_suffix(stepper)
                expander.add_row(row)
                task_rows.append(row)
                task_steppers.append(stepper)

            self.pages_list.append(expander)
            self.page_expanders.append(expander)
            self.task_rows.append(task_rows)
            self.task_steppers.append(task_steppers)