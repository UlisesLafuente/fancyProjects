import sys

sys.path.insert(0, "/usr/share/fancyprojects/src")

from appWindow.app_window import ProjectApp

sys.exit(ProjectApp().run(sys.argv))