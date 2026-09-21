import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

from projects.Project import WorkflowType


WORKFLOW_LABELS = {
    WorkflowType.CONTINUOUS: "Workflow continuo",
    WorkflowType.BY_TASK: "Workflow por tareas",
}


WORKFLOW_DESCRIPTIONS = {
    WorkflowType.CONTINUOUS: "Se hace la tarea de la página 1, luego su siguiente tarea,\ny así página a página.",
    WorkflowType.BY_TASK: "Primero se completan todas las tareas de un tipo\nsobre todas las páginas, y luego la siguiente tarea.",
}


class NewProjectDialog(Adw.Dialog):
    def __init__(self, on_create=None):
        super().__init__()
        self.set_title("Nuevo proyecto")
        self.set_size_request(480, -1)
        self._create_callback = on_create
        self._tasks = []

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(18)
        box.set_margin_bottom(18)
        box.set_margin_start(24)
        box.set_margin_end(24)

        group = Adw.PreferencesGroup(title="Datos del proyecto")

        self.entry_name = Adw.EntryRow(title="Nombre")
        group.add(self.entry_name)

        self.spin_pages = Adw.SpinRow.new_with_range(1, 10000, 1)
        self.spin_pages.set_title("Páginas")
        self.spin_pages.set_value(1)
        group.add(self.spin_pages)

        box.append(group)

        tasks_heading = Gtk.Label(label="Tareas", xalign=0.0)
        tasks_heading.add_css_class("heading")
        tasks_heading.set_margin_top(10)
        box.append(tasks_heading)

        self.tasks_box = Gtk.ListBox()
        self.tasks_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.tasks_box.add_css_class("boxed-list")
        box.append(self.tasks_box)

        add_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.entry_task = Gtk.Entry()
        self.entry_task.set_hexpand(True)
        self.entry_task.set_placeholder_text("Nombre de la tarea")
        self.spin_task_hours = Gtk.SpinButton.new_with_range(1, 1000, 1)
        self.spin_task_hours.set_value(1)
        self.spin_task_hours.set_tooltip_text("Horas estimadas")
        hours_label = Gtk.Label(label="h")
        add_btn = Gtk.Button(label="Añadir")
        add_btn.add_css_class("suggested-action")
        self.entry_task.connect("activate", self._on_add_task)
        self.spin_task_hours.connect("activate", self._on_add_task)
        add_btn.connect("clicked", self._on_add_task)
        add_row.append(self.entry_task)
        add_row.append(self.spin_task_hours)
        add_row.append(hours_label)
        add_row.append(add_btn)
        add_row.set_margin_top(6)
        box.append(add_row)

        workflow_group = Adw.PreferencesGroup(title="Workflow")
        self.radio_continuous = Gtk.CheckButton()
        self.radio_continuous.set_active(True)
        self.radio_by_task = Gtk.CheckButton(group=self.radio_continuous)

        self._append_workflow_option(
            workflow_group, self.radio_continuous,
            WORKFLOW_LABELS[WorkflowType.CONTINUOUS],
            WORKFLOW_DESCRIPTIONS[WorkflowType.CONTINUOUS],
        )
        self._append_workflow_option(
            workflow_group, self.radio_by_task,
            WORKFLOW_LABELS[WorkflowType.BY_TASK],
            WORKFLOW_DESCRIPTIONS[WorkflowType.BY_TASK],
        )
        box.append(workflow_group)

        self.error_label = Gtk.Label(label="", xalign=0.0)
        self.error_label.add_css_class("error")
        self.error_label.set_visible(False)
        box.append(self.error_label)

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_box.set_halign(Gtk.Align.END)
        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", self._on_cancel)
        create_btn = Gtk.Button(label="Crear")
        create_btn.add_css_class("suggested-action")
        create_btn.connect("clicked", self._on_create)
        action_box.append(cancel_btn)
        action_box.append(create_btn)
        box.append(action_box)

        self.set_child(box)

    @staticmethod
    def _append_workflow_option(group, checkbutton, title, description):
        row = Adw.ActionRow(title=title, subtitle=description)
        row.set_activatable_widget(checkbutton)
        row.add_suffix(checkbutton)
        group.add(row)

    def _on_cancel(self, *args):
        self.close()

    def _on_create(self, *args):
        if not self._is_valid():
            self.error_label.set_text(self._error_message())
            self.error_label.set_visible(True)
            return
        if self._create_callback is not None:
            self._create_callback(self.get_data())
        self.close()

    def _on_add_task(self, *args):
        name = self.entry_task.get_text().strip()
        hours = int(self.spin_task_hours.get_value())
        if name and all(task_name != name for task_name, _ in self._tasks):
            self._tasks.append((name, hours))
            self._add_task_row(name, hours)
            self.error_label.set_visible(False)
        self.entry_task.set_text("")
        self.spin_task_hours.set_value(1)
        self.entry_task.grab_focus()

    def _add_task_row(self, name, hours):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)

        label = Gtk.Label(label=name, xalign=0.0)
        label.set_hexpand(True)
        hours_label = Gtk.Label(label="{} h".format(hours))
        hours_label.add_css_class("dim-label")
        remove_btn = Gtk.Button()
        remove_btn.set_child(Gtk.Image.new_from_icon_name("list-remove-symbolic"))
        remove_btn.add_css_class("flat")
        remove_btn.set_tooltip_text("Eliminar tarea")
        remove_btn.connect("clicked", self._on_remove_task, name, row)

        box.append(label)
        box.append(hours_label)
        box.append(remove_btn)
        row.set_child(box)
        self.tasks_box.append(row)

    def _on_remove_task(self, button, name, row):
        self._tasks = [task for task in self._tasks if task[0] != name]
        self.tasks_box.remove(row)

    def _is_valid(self):
        return bool(self.entry_name.get_text().strip()) and bool(self._tasks)

    def _error_message(self):
        if not self.entry_name.get_text().strip():
            return "El nombre del proyecto no puede estar vacío."
        if not self._tasks:
            return "Añade al menos una tarea."
        return ""

    def get_workflow_type(self):
        if self.radio_by_task.get_active():
            return WorkflowType.BY_TASK
        return WorkflowType.CONTINUOUS

    def get_data(self):
        return {
            "project_name": self.entry_name.get_text().strip(),
            "pages": int(self.spin_pages.get_value()),
            "tasks": list(self._tasks),
            "workflow_type": self.get_workflow_type(),
        }