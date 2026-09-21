from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, Gtk

from persistence.project_repository import ProjectRepository
from projects.Page import Page
from projects.Project import Project
from projects.Task import Task

from appWindow.main_view import ProjectView
from appWindow.new_project_dialog import NewProjectDialog

APP_ID = "com.ulises.fancyprojects"
STYLE_CSS = Path(__file__).parent / "style.css"


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


class ProjectPickerDialog(Adw.Dialog):
    def __init__(self, projects, on_open=None):
        super().__init__()
        self.set_title("Abrir proyecto")
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
        open_btn = Gtk.Button(label="Abrir")
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

        toolbar = Adw.ToolbarView()
        self.set_content(toolbar)

        headerbar = Adw.HeaderBar()
        self._add_header_buttons(headerbar)
        toolbar.add_top_bar(headerbar)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.append(self._build_menu_bar())

        self.view = ProjectView()
        vbox.append(self.view)

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
        file_menu.append("Guardar", "app.save-project")
        file_menu.append("Salir", "app.quit")
        root.append_submenu("File", file_menu)
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
                Page([Task(name, 0) for name in data["tasks"]])
                for _ in range(data["pages"])
            ],
            workflow_type=data["workflow_type"],
        )
        self.current_project = project
        self.view.show_project(project)
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
            self._set_status("Proyecto \"{}\" cargado.".format(project.projectName))

    def _on_save_clicked(self, *args):
        project = self.current_project
        if project is None:
            self._show_info("Guardar", "No hay ningún proyecto abierto para guardar.")
            return
        self.app.repository.save_project(project)
        self._set_status("Proyecto \"{}\" guardado.".format(project.projectName))

    def _show_info(self, title, message):
        dialog = Adw.MessageDialog.new(self, title, message)
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.connect("response", lambda d, r: d.close())
        dialog.present()


class ProjectApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.repository = ProjectRepository()

    def do_startup(self):
        Adw.Application.do_startup(self)
        self._create_actions()

    def do_activate(self):
        install_stylesheet()
        window = self.props.active_window
        if not window:
            window = ProjectWindow(application=self)
            self.add_window(window)
        window.present()

    def _create_actions(self):
        handlers = {
            "new-project": (self._action_new, ["<Control>n"]),
            "open-project": (self._action_open, ["<Control>o"]),
            "save-project": (self._action_save, ["<Control>s"]),
        }
        for name, (handler, accels) in handlers.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", handler)
            self.add_action(action)
            self.set_accels_for_action("app." + name, accels)
        self.set_accels_for_action("app.quit", ["<Control>q"])

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