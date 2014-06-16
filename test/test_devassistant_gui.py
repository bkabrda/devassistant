import os
import sys

from devassistant.gui import run_gui


class TestDevAssistantGUI(object):
    """
    Test class for DevAssistant GUI
    """

    def test_executable_gui(self):
        os.environ['DISPLAY'] = ""
        assert run_gui() == sys.exit(1)


