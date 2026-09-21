import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from projects.Project import WorkflowType


WORKFLOW_LABELS = {
    WorkflowType.CONTINUOUS: "Workflow continuo",
    WorkflowType.BY_TASK: "Workflow por tareas",
}


class NewProjectDialog(Gtk.Dialog):
    def __init__(self, parent_window):
        super().__init__(
            title="Nuevo proyecto",
            transient_for=parent_window,
            modal=True,
            resizable=False,
        )
        self.set_default_size(480, -1)
        self.add_buttons("_Cancelar", Gtk.ResponseType.CANCEL, "_Crear", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        self._tasks = []

        content = self.get_content_area()
        content.set_border_width(18)
        content.set_spacing(14)

        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(12)
        content.add(grid)

        # Nombre
        name_label = Gtk.Label(label="Nombre", xalign=0.0)
        name_label.get_style_context().add_class("dim-label")
        self.entry_name = Gtk.Entry()
        self.entry_name.set_placeholder_text("P. ej. Comic de superheroes")
        grid.attach(name_label, 0, 0, 1, 1)
        grid.attach(self.entry_name, 1, 0, 1, 1)

        # Número de páginas
        pages_label = Gtk.Label(label="Páginas", xalign=0.0)
        pages_label.get_style_context().add_class("dim-label")
        self.spin_pages = Gtk.SpinButton()
        self.spin_pages.set_range(1, 10000)
        self.spin_pages.set_increments(1, 5)
        self.spin_pages.set_value(1)
        grid.attach(pages_label, 0, 1, 1, 1)
        grid.attach(self.spin_pages, 1, 1, 1, 1)

        # Tareas
        tasks_label = Gtk.Label(label="Tareas", xalign=0.0)
        tasks_label.get_style_context().add_class("dim-label")
        grid.attach(tasks_label, 0, 2, 1, 1)

        tasks_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.tasks_box = Gtk.ListBox()
        self.tasks_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.tasks_box.set_size_request(-1, 120)
        tasks_vbox.pack_start(self.tasks_box, True, True, 0)

        add_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.entry_task = Gtk.Entry()
        self.entry_task.set_placeholder_text("Nombre de la tarea (p. ej. Boceto)")
        self.entry_task.set_hexpand(True)
        self.entry_task.connect("activate", self._on_add_task)
        add_btn = Gtk.Button.new_with_label("Añadir")
        add_btn.connect("clicked", self._on_add_task)
        add_row.pack_start(self.entry_task, True, True, 0)
        add_row.pack_start(add_btn, False, False, 0)
        tasks_vbox.pack_start(add_row, False, False, 0)
        grid.attach(tasks_vbox, 1, 2, 1, 1)

        # Workflow
        workflow_label = Gtk.Label(label="Workflow", xalign=0.0)
        workflow_label.get_style_context().add_class("dim-label")
        grid.attach(workflow_label, 0, 3, 1, 1)

        workflow_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.radio_continuous = Gtk.RadioButton.new_with_label_from_widget(
            None, WORKFLOW_LABELS[WorkflowType.CONTINUOUS]
        )
        self.radio_continuous.set_active(True)
        desc_continuous = Gtk.Label(label="Se hace la tarea de la página 1, luego su siguiente tarea,\ny así página a página.", xalign=0.0)
        desc_continuous.get_style_context().add_class("dim-label")
        self.radio_by_task = Gtk.RadioButton.new_with_label_from_widget(
            self.radio_continuous, WORKFLOW_LABELS[WorkflowType.BY_TASK]
        )
        desc_by_task = Gtk.Label(label="Primero se completan todas las tareas de un tipo\nsobre todas las páginas, y luego la siguiente tarea.", xalign=0.0)
        desc_by_task.get_style_context().add_class("dim-label")

        workflow_vbox.pack_start(self.radio_continuous, False, False, 0)
        workflow_vbox.pack_start(desc_continuous, False, False, 0)
        workflow_vbox.pack_start(self.radio_by_task, False, False, 0)
        workflow_vbox.pack_start(desc_by_task, False, False, 0)
        grid.attach(workflow_vbox, 1, 3, 1, 1)

        self.error_label = Gtk.Label(label="", xalign=0.0)
        self.error_label.get_style_context().add_class("error")
        self.error_label.set_visible(False)
        content.pack_end(self.error_label, False, False, 0)

        self.connect("response", self._on_response)

        self.show_all()
        self.entry_name.grab_focus()

    def _on_add_task(self, *args):
        name = self.entry_task.get_text().strip()
        if name and name not in self._tasks:
            self._tasks.append(name)
            self._add_task_row(name)
        self.entry_task.set_text("")
        self.entry_task.grab_focus()

    def _add_task_row(self, name):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_top(4)
        box.set_margin_bottom(4)

        label = Gtk.Label(label=name, xalign=0.0)
        label.set_hexpand(True)
        remove_btn = Gtk.Button.new_from_icon_name(
            "list-remove-symbolic", Gtk.IconSize.BUTTON
        )
        remove_btn.set_relief(Gtk.ReliefStyle.NONE)
        remove_btn.set_tooltip_text("Eliminar tarea")
        remove_btn.connect("clicked", self._on_remove_task, name, row)

        box.pack_start(label, True, True, 0)
        box.pack_start(remove_btn, False, False, 0)
        row.add(box)
        self.tasks_box.add(row)
        self.tasks_box.show_all()

    def _on_remove_task(self, button, name, row):
        if name in self._tasks:
            self._tasks.remove(name)
        self.tasks_box.remove(row)

    def _on_response(self, dialog, response_id):
        if response_id != Gtk.ResponseType.OK:
            return
        if not self._is_valid():
            self.error_label.set_text(self._error_message())
            self.error_label.show()
            dialog.stop_emission("response")

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