import sys

sys.path.insert(0, "/usr/share/fanzyprojects/src")

from appWindow.app_window import ProjectApp

sys.exit(ProjectApp().run(sys.argv))