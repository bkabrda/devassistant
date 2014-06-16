import sys
import os

from devassistant.gui import main_window
from devassistant.gui import creator_window

GUI_MESSAGE = "DevAssistant GUI requires a running X server."
GUI_MESSAGE_DISPLAY="Environment variable DISPLAY is not set."

def run_gui():
    """
    Function for running DevAssistant GUI
    """
    try:
        from gi.repository import Gtk
    except RuntimeError as e:
        print(GUI_MESSAGE)
        print("%s: %r" % (e.__class__.__name__, str(e)))
        sys.exit(1)

    if not os.environ.get('DISPLAY'):
        print("%s %s" % (GUI_MESSAGE, GUI_MESSAGE_DISPLAY))
        sys.exit(1)
    main_window.MainWindow()


def run_yaml_gui():
    """
    Function for running DevAssistant YAML Creator GUI
    """
    try:
        from gi.repository import Gtk
    except RuntimeError as e:
        print(GUI_MESSAGE)
        print("%s: %r" % (e.__class__.__name__, str(e)))
        sys.exit(1)

    creator_window.CreatorWindow()
