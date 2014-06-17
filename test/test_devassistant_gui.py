import os
from devassistant.gui import run_gui


class TestDevAssistantGUI(object):
    """
    Test class for running DevAssistant GUI
    """
    def test_environment_display(self):
        """
        test for detection wrong environment DISPLAY variable
        """
        os.environ['DISPLAY'] = ""
        try:
            run_gui()
        except SystemExit as se:
            assert se.code == 1