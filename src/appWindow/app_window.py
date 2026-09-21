import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gio, Gtk

from persistence.project_repository import ProjectRepository
from projects.Page import Page
from projects.Project import Project
from projects.Task import Task

from appWindow.main_view import ProjectView, WORKFLOW_LABELS
from appWindow.new_project_dialog import NewProjectDialog

APP_ID = "com.ulises.fancyprojects"


class ProjectPickerDialog(Gtk.Dialog):
    def __init__(self, parent_window, projects):
        super().__init__(
            title="Abrir proyecto",
            transient_for=parent_window,
            modal=True,
            resizable=False,
        )
        self.set_default_size(420, -1)
        self.add_buttons("_Cancelar", Gtk.ResponseType.CANCEL, "_Abrir", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        self._selected = None
        self._projects = projects

        content = self.get_content_area()
        content.set_border_width(18)
        content.set_spacing(12)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-activated", self._on_row_activated)
        for project in projects:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=project.projectName, xalign=0.0)
            label.set_margin_start(8)
            label.set_margin_end(8)
            label.set_margin_top(6)
            label.set_margin_bottom(6)
            row.add(label)
            self.listbox.add(row)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(200)
        scrolled.add(self.listbox)
        content.add(scrolled)

        self.connect("response", self._on_response)
        self.show_all()

    def _on_row_activated(self, listbox, row):
        self._on_response(self, Gtk.ResponseType.OK)

    def _on_response(self, dialog, response_id):
        if response_id != Gtk.ResponseType.OK:
            return
        selected = self.listbox.get_selected_row()
        if selected is None:
            dialog.stop_emission("response")
            return
        index = selected.get_index()
        self._selected = self._projects[index].id

    def get_selected_id(self):
        return self._selected


class ProjectWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Gestor de Proyectos")
        self.app = app
        self.set_default_size(920, 660)

        headerbar = Gtk.HeaderBar()
        headerbar.set_show_close_button(True)
        headerbar.props.title = "Gestor de Proyectos"
        headerbar.props.subtitle = "Proyectos y workflows"

        new_btn = Gtk.Button.new_from_icon_name("document-new-symbolic", Gtk.IconSize.BUTTON)
        new_btn.set_tooltip_text("Nuevo proyecto (Ctrl+N)")
        new_btn.connect("clicked", self._on_new_clicked)
        open_btn = Gtk.Button.new_from_icon_name("document-open-symbolic", Gtk.IconSize.BUTTON)
        open_btn.set_tooltip_text("Abrir proyecto (Ctrl+O)")
        open_btn.connect("clicked", self._on_open_clicked)
        save_btn = Gtk.Button.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON)
        save_btn.set_tooltip_text("Guardar proyecto (Ctrl+S)")
        save_btn.connect("clicked", self._on_save_clicked)

        headerbar.pack_start(new_btn)
        headerbar.pack_start(open_btn)
        headerbar.pack_start(save_btn)
        self.set_titlebar(headerbar)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.pack_start(self._build_menu_bar(), False, False, 0)

        self.view = ProjectView()
        self.view.show_empty()
        vbox.pack_start(self.view, True, True, 0)

        self.status_label = Gtk.Label(label="", xalign=0.0)
        self.status_label.set_margin_start(12)
        self.status_label.set_margin_end(12)
        self.status_label.set_margin_top(4)
        self.status_label.set_margin_bottom(4)
        self.status_label.get_style_context().add_class("dim-label")
        vbox.pack_end(self.status_label, False, False, 0)

        self.add(vbox)
        self.show_all()

        self._set_status("Listo")

    def _build_menu_bar(self):
        self.menu_bar = Gtk.MenuBar()
        file_item = Gtk.MenuItem.new_with_mnemonic("_File")
        file_menu = Gtk.Menu()

        new_item = Gtk.MenuItem(label="Nuevo proyecto…")
        new_item.connect("activate", self._on_new_clicked)
        open_item = Gtk.MenuItem(label="Abrir…")
        open_item.connect("activate", self._on_open_clicked)
        save_item = Gtk.MenuItem(label="Guardar")
        save_item.connect("activate", self._on_save_clicked)
        separator = Gtk.SeparatorMenuItem()
        quit_item = Gtk.MenuItem(label="Salir")
        quit_item.connect("activate", self._on_quit_clicked)

        file_menu.append(new_item)
        file_menu.append(open_item)
        file_menu.append(save_item)
        file_menu.append(separator)
        file_menu.append(quit_item)

        file_item.set_submenu(file_menu)
        self.menu_bar.append(file_item)
        return self.menu_bar

    def _set_status(self, message):
        self.status_label.set_text(message)

    def _on_new_clicked(self, *args):
        dialog = NewProjectDialog(self)
        dialog.connect("response", self._on_new_response)
        dialog.show_all()

    def _on_new_response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            data = dialog.get_data()
            project = self._build_project(data)
            self.app.current_project = project
            self.view.show_project(project)
            self._set_status("Proyecto \"{}\" creado. Usa File ▸ Guardar para persistirlo.".format(project.projectName))
        dialog.destroy()

    @staticmethod
    def _build_project(data):
        tasks = [Task(name, 0) for name in data["tasks"]]
        pages = [
            Page([Task(name, 0) for name in data["tasks"]])
            for _ in range(data["pages"])
        ]
        return Project(
            data["project_name"],
            pages,
            workflow_type=data["workflow_type"],
        )

    def _on_open_clicked(self, *args):
        projects = self.app.repository.list_projects()
        if not projects:
            self._show_info("Abrir proyecto", "Todavía no hay proyectos guardados.\nCrea uno con File ▸ Nuevo proyecto.")
            return
        dialog = ProjectPickerDialog(self, projects)
        dialog.connect("response", self._on_open_response)
        dialog.show_all()

    def _on_open_response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            project_id = dialog.get_selected_id()
            project = self.app.repository.load_project(project_id)
            if project is not None:
                self.app.current_project = project
                self.view.show_project(project)
                self._set_status("Proyecto \"{}\" cargado.".format(project.projectName))
        dialog.destroy()

    def _on_save_clicked(self, *args):
        project = self.app.current_project
        if project is None:
            self._show_info("Guardar", "No hay ningún proyecto abierto para guardar.")
            return
        self.app.repository.save_project(project)
        self._set_status("Proyecto \"{}\" guardado.".format(project.projectName))

    def _on_quit_clicked(self, *args):
        self.close()

    def _show_info(self, title, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(message)
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.show_all()


class ProjectApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.current_project = None
        self.repository = ProjectRepository()

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self._create_actions()

    def do_activate(self):
        window = self.props.active_window
        if not window:
            window = ProjectWindow(self)
            self.add_window(window)
        window.present()

    def _create_actions(self):
        actions = {
            "new-project": (self._action_new, ["<Control>n"]),
            "open-project": (self._action_open, ["<Control>o"]),
            "save-project": (self._action_save, ["<Control>s"]),
            "quit": (self._action_quit, ["<Control>q"]),
        }
        for name, (handler, accels) in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", handler)
            self.add_action(action)
            self.set_accels_for_action("app." + name, accels)

    def _action_new(self, action, param):
        window = self.props.active_window
        dialog = NewProjectDialog(window)
        dialog.connect("response", window._on_new_response)
        dialog.show_all()

    def _action_open(self, action, param):
        window = self.props.active_window
        window._on_open_clicked()

    def _action_save(self, action, param):
        window = self.props.active_window
        window._on_save_clicked()

    def _action_quit(self, action, param):
        window = self.props.active_window
        window._on_quit_clicked()