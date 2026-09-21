import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

WORKFLOW_LABELS = {
    "continuous": "Workflow continuo",
    "by_task": "Workflow por tareas",
}


class ProjectView(Gtk.Stack):
    def __init__(self):
        super().__init__()
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        self.empty_page = self._build_empty_page()
        self.project_page = self._build_project_page()
        self.add_named(self.empty_page, "empty")
        self.add_named(self.project_page, "project")
        self.show_empty()

    def _build_empty_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        icon = Gtk.Image.new_from_icon_name("folder-documents-symbolic", Gtk.IconSize.DIALOG)
        icon.set_pixel_size(64)
        icon.set_opacity(0.4)

        title = Gtk.Label(label="No hay ningún proyecto abierto")
        title.get_style_context().add_class("dim-label")

        hint = Gtk.Label(label="Usa File ▸ Nuevo proyecto para crear uno,\no File ▸ Abrir para cargar uno guardado.")
        hint.get_style_context().add_class("dim-label")

        box.pack_start(icon, False, False, 0)
        box.pack_start(title, False, False, 0)
        box.pack_start(hint, False, False, 0)
        return box

    def _build_project_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(12)
        page.set_margin_bottom(12)
        page.set_margin_start(18)
        page.set_margin_end(18)

        self.header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.project_title = Gtk.Label(label="", xalign=0.0)
        self.project_title.get_style_context().add_class("title-1")
        self.workflow_label = Gtk.Label(label="", xalign=0.0)
        self.workflow_label.get_style_context().add_class("dim-label")
        self.summary_label = Gtk.Label(label="", xalign=0.0)
        self.summary_label.get_style_context().add_class("dim-label")

        self.header_box.pack_start(self.project_title, False, False, 0)
        self.header_box.pack_start(self.workflow_label, False, False, 0)
        self.header_box.pack_start(self.summary_label, False, False, 0)
        page.pack_start(self.header_box, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        self.tree = Gtk.TreeView()
        self.tree.set_headers_visible(False)
        self.store = Gtk.TreeStore(str, str, str)
        self.tree.set_model(self.store)

        column = Gtk.TreeViewColumn()
        cell = Gtk.CellRendererText()
        cell.set_property("weight", 700)
        column.pack_start(cell, False)
        column.add_attribute(cell, "text", 0)
        self.tree.append_column(column)

        hours_col = Gtk.TreeViewColumn(title="Horas")
        hours_cell = Gtk.CellRendererText()
        hours_col.pack_start(hours_cell, False)
        hours_col.add_attribute(hours_cell, "text", 1)
        self.tree.append_column(hours_col)

        state_col = Gtk.TreeViewColumn(title="Estado")
        state_cell = Gtk.CellRendererText()
        state_col.pack_start(state_cell, False)
        state_col.add_attribute(state_cell, "text", 2)
        self.tree.append_column(state_col)

        scrolled.add(self.tree)
        page.pack_start(scrolled, True, True, 0)
        return page

    def show_empty(self):
        self.set_visible_child_name("empty")

    def show_project(self, project):
        self.set_visible_child_name("project")

        self.project_title.set_text(project.projectName)
        self.workflow_label.set_text(WORKFLOW_LABELS.get(project.workflow_type, project.workflow_type))
        self.summary_label.set_text(
            "{:.0f} h estimadas · {:.0f} h completadas · {:.0f}% completado".format(
                project.getTotalEstimatedHours(),
                project.getTotalCompletedHours(),
                project.percentComplete(),
            )
        )

        self.store.clear()
        for page_index, page in enumerate(project.getPages(), start=1):
            page_name = "Página {}".format(page_index)
            page_iter = self.store.append(
                None,
                (page_name, "{:.0f} h".format(page.getTotalEstimatedHours()), ""),
            )
            for task in page.getTasks():
                state = "Completada" if task.getCompletedTask() else "Pendiente"
                self.store.append(
                    page_iter,
                    (
                        "  " + task.getTaskName(),
                        "{:.0f} / {:.0f} h".format(task.getHoursCompleted(), task.getHoursPredicted()),
                        state,
                    ),
                )
        self.tree.expand_all()