import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gio, GObject, Gtk, Pango

from appWindow.new_project_dialog import WORKFLOW_LABELS


class RowItem(GObject.Object):
    def __init__(self, element="", hours="", state="", bold=False):
        super().__init__()
        self.element = element
        self.hours = hours
        self.state = state
        self.bold = bold


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

        self.store = Gio.ListStore.new(RowItem)
        model = Gtk.SingleSelection.new(self.store)
        self.column_view = Gtk.ColumnView(model=model)
        self.column_view.set_vexpand(True)
        self.column_view.set_hexpand(True)

        self._append_column("Elemento", lambda row: row.element, 0)
        self._append_column("Horas", lambda row: row.hours, 160)
        self._append_column("Estado", lambda row: row.state, 160)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.column_view)
        page.append(scrolled)
        return page

    def _append_column(self, title, getter, width):
        column = Gtk.ColumnViewColumn(title=title)
        if width:
            column.set_fixed_width(width)
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._factory_setup)
        factory.connect("bind", lambda factory, list_item: self._factory_bind(factory, list_item, getter))
        column.set_factory(factory)
        self.column_view.append_column(column)

    @staticmethod
    def _factory_setup(factory, list_item):
        label = Gtk.Label(label="", xalign=0.0)
        label.set_margin_start(12)
        label.set_margin_end(12)
        list_item.set_child(label)

    @staticmethod
    def _factory_bind(factory, list_item, getter):
        label = list_item.get_child()
        row = list_item.get_item()
        label.set_text(getter(row))
        if row.bold:
            attributes = Pango.AttrList()
            attributes.insert(Pango.attr_weight_new(Pango.Weight.BOLD))
            label.set_attributes(attributes)
        else:
            label.set_attributes(None)

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

        self.store.remove_all()
        for page_index, page in enumerate(project.getPages(), start=1):
            self.store.append(RowItem(
                element="Página {}".format(page_index),
                hours="{:.0f} h".format(page.getTotalEstimatedHours()),
                state="",
                bold=True,
            ))
            for task in page.getTasks():
                state = "Completada" if task.getCompletedTask() else "Pendiente"
                self.store.append(RowItem(
                    element="  " + task.getTaskName(),
                    hours="{:.0f} / {:.0f} h".format(task.getHoursCompleted(), task.getHoursPredicted()),
                    state=state,
                    bold=False,
                ))