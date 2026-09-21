import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

from appWindow.new_project_dialog import WORKFLOW_LABELS


class ProjectView(Gtk.Stack):
    def __init__(self):
        super().__init__()
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        self.page_expanders = []
        self.task_rows = []

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

        self.pages_list.remove_all()
        self.page_expanders = []
        self.task_rows = []

        for page_index, page in enumerate(project.getPages(), start=1):
            expander = Adw.ExpanderRow()
            expander.set_title("Página {}".format(page_index))
            expander.set_subtitle(
                "{:.0f} h estimadas · {:.0f}% completado".format(
                    page.getTotalEstimatedHours(),
                    page.getPercentileCompleted(),
                )
            )

            task_rows = []
            for task in page.getTasks():
                row = Adw.ActionRow(title=task.getTaskName())
                row.set_subtitle("Completada" if task.getCompletedTask() else "Pendiente")
                hours = Gtk.Label(
                    label="{:.0f} / {:.0f} h".format(task.getHoursCompleted(), task.getHoursPredicted())
                )
                hours.add_css_class("dim-label")
                row.add_suffix(hours)
                expander.add_row(row)
                task_rows.append(row)

            self.pages_list.append(expander)
            self.page_expanders.append(expander)
            self.task_rows.append(task_rows)