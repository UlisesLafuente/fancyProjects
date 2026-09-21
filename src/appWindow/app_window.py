import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from persistence.project_io import export_project, import_project
from persistence.project_repository import ProjectRepository
from projects.Page import Page
from projects.Project import Project, WorkflowType
from projects.Task import Task

from appWindow.hour_grid import HourGridView
from appWindow.main_view import ProjectView
from appWindow.new_project_dialog import NewProjectDialog

APP_ID = "com.ulises.fancyprojects"
APP_ICON_NAME = APP_ID

VIEW_MODE_LABELS = {
    WorkflowType.CONTINUOUS: "Workflow continuo",
    WorkflowType.BY_TASK: "Workflow por tareas (página a página)",
}


def resource_path(relative: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative
    return Path(__file__).resolve().parent / relative


def get_res_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "res"
    return Path(__file__).resolve().parent.parent / "res"


STYLE_CSS = resource_path("style.css")


def _safe_filename(name):
    cleaned = "".join(c if c not in "/\\:" else "-" for c in name)
    return cleaned.strip() or "proyecto"


def install_stylesheet():
    if not STYLE_CSS.exists():
        return
    provider = Gtk.CssProvider()
    provider.load_from_path(str(STYLE_CSS))
    display = Gdk.Display.get_default()
    if display is not None:
        Gtk.StyleContext.add_provider_for_display(
            display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


def install_app_icon():
    res_dir = get_res_dir()
    if not (res_dir / (APP_ICON_NAME + ".svg")).exists():
        return
    display = Gdk.Display.get_default()
    if display is not None:
        Gtk.IconTheme.get_for_display(display).add_search_path(str(res_dir))
    Gtk.Window.set_default_icon_name(APP_ICON_NAME)


def _swallow_libadwaita_measure_warnings(log_domain, log_level, message):
    if message is not None and "natural size must be >= min size" in message:
        return
    GLib.log_default_handler(log_domain, log_level, message)


def install_log_filter():
    if getattr(sys, "_fancyprojects_log_filter", False):
        return
    sys._fancyprojects_log_filter = True
    GLib.log_set_handler(
        None,
        GLib.LogLevelFlags.LEVEL_MESSAGE
        | GLib.LogLevelFlags.LEVEL_WARNING
        | GLib.LogLevelFlags.LEVEL_CRITICAL,
        _swallow_libadwaita_measure_warnings,
    )


class ProjectPickerDialog(Adw.Dialog):
    def __init__(self, projects, on_open=None, title="Abrir proyecto", confirm_label="Abrir"):
        super().__init__()
        self.set_title(title)
        self.set_size_request(480, -1)
        self._on_open = on_open
        self._selected = None

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(18)
        box.set_margin_bottom(18)
        box.set_margin_start(24)
        box.set_margin_end(24)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.add_css_class("boxed-list")
        self.listbox.connect("row-activated", lambda lb, row: self._choose())
        for project in projects:
            row = Gtk.ListBoxRow()
            row.child = project
            label = Gtk.Label(label=project.projectName, xalign=0.0)
            label.set_margin_start(12)
            label.set_margin_end(12)
            label.set_margin_top(8)
            label.set_margin_bottom(8)
            row.set_child(label)
            self.listbox.append(row)

        box.append(self.listbox)

        self.error_label = Gtk.Label(label="Selecciona un proyecto.", xalign=0.0)
        self.error_label.add_css_class("error")
        self.error_label.set_visible(False)
        box.append(self.error_label)

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_box.set_halign(Gtk.Align.END)
        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", lambda *_: self.close())
        open_btn = Gtk.Button(label=confirm_label)
        open_btn.add_css_class("suggested-action")
        open_btn.connect("clicked", lambda *_: self._choose())
        action_box.append(cancel_btn)
        action_box.append(open_btn)
        box.append(action_box)

        self.set_child(box)

    def _choose(self):
        selected = self.listbox.get_selected_row()
        if selected is None:
            self.error_label.set_visible(True)
            return
        self.error_label.set_visible(False)
        self._selected = selected.child.id
        if self._on_open is not None:
            self._on_open(self._selected)
        self.close()

    def get_selected_id(self):
        return self._selected


class ProjectWindow(Adw.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application)
        self.app = application
        self.set_default_size(920, 660)
        self.set_title("Gestor de Proyectos")
        self.current_project = None
        self.view_mode = WorkflowType.CONTINUOUS
        self._refresh_scheduled = False
        self._pending_pages = set()
        self._pending_full = False

        toolbar = Adw.ToolbarView()
        self.set_content(toolbar)

        headerbar = Adw.HeaderBar()
        self._add_header_buttons(headerbar)
        toolbar.add_top_bar(headerbar)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.append(self._build_menu_bar())

        self.view = ProjectView(on_estimated_hours_change=self._on_estimated_hours_changed)
        self.hour_view = HourGridView(on_change=self._on_hours_changed)

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_wide_handle(True)
        paned.set_vexpand(True)
        paned.set_position(460)
        paned.set_start_child(self.view)
        paned.set_end_child(self.hour_view)
        self.paned = paned
        vbox.append(paned)

        self.status_label = Gtk.Label(label="", xalign=0.0)
        self.status_label.set_margin_start(12)
        self.status_label.set_margin_end(12)
        self.status_label.set_margin_top(4)
        self.status_label.set_margin_bottom(4)
        self.status_label.add_css_class("dim-label")
        vbox.append(self.status_label)

        toolbar.set_content(vbox)
        self._set_status("Listo")

    def _add_header_buttons(self, headerbar):
        headerbar.pack_start(self._make_icon_button(
            "document-new-symbolic", "Nuevo proyecto (Ctrl+N)", self._on_new_clicked))
        headerbar.pack_start(self._make_icon_button(
            "document-open-symbolic", "Abrir proyecto (Ctrl+O)", self._on_open_clicked))
        headerbar.pack_start(self._make_icon_button(
            "document-save-symbolic", "Guardar proyecto (Ctrl+S)", self._on_save_clicked))

    @staticmethod
    def _make_icon_button(icon_name, tooltip, handler):
        button = Gtk.Button()
        button.set_child(Gtk.Image.new_from_icon_name(icon_name))
        button.set_tooltip_text(tooltip)
        button.connect("clicked", handler)
        return button

    def _build_menu_bar(self):
        root = Gio.Menu()
        file_menu = Gio.Menu()
        file_menu.append("Nuevo proyecto…", "app.new-project")
        file_menu.append("Abrir…", "app.open-project")
        file_menu.append("Cerrar proyecto", "app.close-project")
        file_menu.append("Guardar", "app.save-project")
        file_menu.append("Importar proyecto…", "app.import-project")
        file_menu.append("Exportar proyecto…", "app.export-project")
        file_menu.append("Eliminar proyecto…", "app.delete-project")
        file_menu.append("Salir", "app.quit")
        root.append_submenu("File", file_menu)

        view_menu = Gio.Menu()
        for mode in (WorkflowType.CONTINUOUS, WorkflowType.BY_TASK):
            item = Gio.MenuItem.new(VIEW_MODE_LABELS[mode], "app.view-workflow")
            item.set_attribute_value("target", GLib.Variant.new_string(mode))
            view_menu.append_item(item)
        root.append_submenu("View", view_menu)
        return Gtk.PopoverMenuBar.new_from_model(root)

    def _set_status(self, message):
        self.status_label.set_text(message)

    def _on_new_clicked(self, *args):
        dialog = NewProjectDialog(on_create=self._create_project)
        dialog.present(self)

    def _create_project(self, data):
        project = Project(
            data["project_name"],
            [
                Page([Task(name, hours) for name, hours in data["tasks"]])
                for _ in range(data["pages"])
            ],
        )
        self.current_project = project
        self.view.show_project(project)
        self.hour_view.show_project(project)
        self._set_status("Proyecto \"{}\" creado. Usa File ▸ Guardar para persistirlo.".format(project.projectName))

    def _on_open_clicked(self, *args):
        projects = self.app.repository.list_projects()
        if not projects:
            self._show_info(
                "Abrir proyecto",
                "Todavía no hay proyectos guardados.\nCrea uno con File ▸ Nuevo proyecto.",
            )
            return
        dialog = ProjectPickerDialog(projects, on_open=self._open_project)
        dialog.present(self)

    def _open_project(self, project_id):
        project = self.app.repository.load_project(project_id)
        if project is not None:
            self.current_project = project
            self.view.show_project(project)
            self.hour_view.show_project(project)
            self._set_status("Proyecto \"{}\" cargado.".format(project.projectName))

    def _on_close_clicked(self, *args):
        if self.current_project is None:
            self._show_info("Cerrar proyecto", "No hay ningún proyecto abierto para cerrar.")
            return
        self.current_project = None
        self._pending_pages.clear()
        self._pending_full = False
        self._refresh_scheduled = False
        self.view.show_empty()
        self.hour_view.show_empty()
        self._set_status("Proyecto cerrado. Listo.")

    def _on_hours_changed(self, task=None, page=None):
        if self.current_project is None:
            return
        if page is None:
            self._pending_full = True
        else:
            self._pending_pages.add(page)
        if self._refresh_scheduled:
            return
        self._refresh_scheduled = True
        GLib.idle_add(self._flush_refresh)

    def _flush_refresh(self):
        self._refresh_scheduled = False
        project = self.current_project
        if project is None:
            self._pending_pages.clear()
            self._pending_full = False
            return False
        if self._pending_full:
            self.view.refresh(project)
        else:
            for page in self._pending_pages:
                self.view.refresh_page(project, page)
        self._pending_pages.clear()
        self._pending_full = False
        self.hour_view.refresh_status()
        self._set_status(
            "Progreso actualizado: {:.0f}% completado.".format(project.percentComplete())
        )
        return False

    def _on_estimated_hours_changed(self, task, page):
        project = self.current_project
        if project is None:
            return
        self._refresh_scheduled = False
        self._pending_pages.clear()
        self._pending_full = False
        self.view.refresh_page(project, page)
        self.hour_view.update_task_hours(task, page)
        try:
            page_number = project.getPages().index(page) + 1
        except ValueError:
            page_number = "?"
        self._set_status(
            "Horas estimadas de \"{}\" (página {}) actualizadas: {} h.".format(
                task.getTaskName(), page_number, task.getHoursPredicted()
            )
        )

    def _apply_view_mode(self, mode):
        self.view_mode = mode
        self.hour_view.set_view_mode(mode)
        self._set_status("Vista: {}.".format(VIEW_MODE_LABELS[mode]))

    def _on_save_clicked(self, *args):
        project = self.current_project
        if project is None:
            self._show_info("Guardar", "No hay ningún proyecto abierto para guardar.")
            return
        self.app.repository.save_project(project)
        self._set_status("Proyecto \"{}\" guardado.".format(project.projectName))

    @staticmethod
    def _project_file_filter():
        filterbox = Gtk.FileFilter()
        filterbox.set_name("Proyectos Fancy Projects (*.fancyproject)")
        filterbox.add_pattern("*.fancyproject")
        return filterbox

    def _on_import_clicked(self, *args):
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Importar proyecto")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(self._project_file_filter())
        file_dialog.set_filters(filters)
        file_dialog.open(self, None, self._on_import_dialog_response)

    def _on_import_dialog_response(self, file_dialog, result):
        try:
            file = file_dialog.open_finish(result)
        except GLib.Error:
            return
        self._import_file(file.get_path())

    def _import_file(self, path):
        try:
            project = import_project(path)
        except (ValueError, OSError) as e:
            self._show_info("Importar proyecto", "No se pudo importar el proyecto:\n{}".format(e))
            return
        self.app.repository.save_project(project)
        self.current_project = project
        self.view.show_project(project)
        self.hour_view.show_project(project)
        self._set_status("Proyecto \"{}\" importado.".format(project.projectName))

    def _on_export_clicked(self, *args):
        project = self.current_project
        if project is None:
            self._show_info("Exportar proyecto", "No hay ningún proyecto abierto para exportar.")
            return
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Exportar proyecto")
        file_dialog.set_initial_name(_safe_filename(project.projectName) + ".fancyproject")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(self._project_file_filter())
        file_dialog.set_filters(filters)
        file_dialog.save(self, None, self._on_export_dialog_response)

    def _on_export_dialog_response(self, file_dialog, result):
        try:
            file = file_dialog.save_finish(result)
        except GLib.Error:
            return
        self._export_to(file.get_path())

    def _export_to(self, path):
        project = self.current_project
        if project is None:
            return
        try:
            export_project(project, path)
        except OSError as e:
            self._show_info("Exportar proyecto", "No se pudo exportar el proyecto:\n{}".format(e))
            return
        self._set_status("Proyecto \"{}\" exportado a {}.".format(project.projectName, path))

    def _on_delete_clicked(self, *args):
        projects = self.app.repository.list_projects()
        if not projects:
            self._show_info("Eliminar proyecto", "No hay proyectos guardados para eliminar.")
            return
        dialog = ProjectPickerDialog(
            projects,
            on_open=self._confirm_delete,
            title="Eliminar proyecto",
            confirm_label="Eliminar",
        )
        dialog.present(self)

    def _confirm_delete(self, project_id):
        project = self.app.repository.load_project(project_id)
        name = project.projectName if project is not None else str(project_id)
        dialog = Adw.MessageDialog.new(
            self,
            "Eliminar proyecto",
            "Se eliminará \"{}\" permanentemente.\nEsta acción no se puede deshacer.".format(name),
        )
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("delete", "Eliminar")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.connect("response", self._on_delete_confirmed, project_id)
        dialog.present()

    def _on_delete_confirmed(self, dialog, response, project_id):
        if dialog is not None:
            dialog.close()
        if response != "delete":
            return
        self.app.repository.delete_project(project_id)
        if self.current_project is not None and self.current_project.id == project_id:
            self.current_project = None
            self.view.show_empty()
            self.hour_view.show_empty()
        self._set_status("Proyecto eliminado.")

    def _show_info(self, title, message):
        dialog = Adw.MessageDialog.new(self, title, message)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.connect("response", lambda d, r: d.close())
        dialog.present()


class ProjectApp(Adw.Application):
    def __init__(self, application_id=APP_ID):
        super().__init__(application_id=application_id)
        self.repository = ProjectRepository()

    def do_startup(self):
        Adw.Application.do_startup(self)
        install_log_filter()
        self._create_actions()

    def do_activate(self):
        install_stylesheet()
        install_app_icon()
        window = self.props.active_window
        if not window:
            window = ProjectWindow(application=self)
            self.add_window(window)
        window.present()

    def _create_actions(self):
        handlers = {
            "new-project": (self._action_new, ["<Control>n"]),
            "open-project": (self._action_open, ["<Control>o"]),
            "close-project": (self._action_close, None),
            "save-project": (self._action_save, ["<Control>s"]),
            "import-project": (self._action_import, None),
            "export-project": (self._action_export, None),
            "delete-project": (self._action_delete, None),
        }
        for name, (handler, accels) in handlers.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", handler)
            self.add_action(action)
            if accels is not None:
                self.set_accels_for_action("app." + name, accels)
        self.set_accels_for_action("app.quit", ["<Control>q"])

        view_mode = Gio.SimpleAction.new_stateful(
            "view-workflow",
            GLib.VariantType.new("s"),
            GLib.Variant.new_string(WorkflowType.CONTINUOUS),
        )
        view_mode.connect("activate", self._action_view_workflow)
        self.add_action(view_mode)

    def _action_view_workflow(self, action, param):
        action.set_state(param)
        window = self.props.active_window
        if window is not None:
            window._apply_view_mode(param.unpack())

    def _action_new(self, action, param):
        window = self.props.active_window
        if window is not None:
            window._on_new_clicked()

    def _action_open(self, action, param):
        window = self.props.active_window
        if window is not None:
            window._on_open_clicked()

    def _action_save(self, action, param):
        window = self.props.active_window
        if window is not None:
            window._on_save_clicked()

    def _action_close(self, action, param):
        window = self.props.active_window
        if window is not None:
            window._on_close_clicked()

    def _action_import(self, action, param):
        window = self.props.active_window
        if window is not None:
            window._on_import_clicked()

    def _action_export(self, action, param):
        window = self.props.active_window
        if window is not None:
            window._on_export_clicked()

    def _action_delete(self, action, param):
        window = self.props.active_window
        if window is not None:
            window._on_delete_clicked()