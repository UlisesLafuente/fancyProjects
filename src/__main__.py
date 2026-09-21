import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from appWindow.app_window import ProjectApp


def main():
    app = ProjectApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()