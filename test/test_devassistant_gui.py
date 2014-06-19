import os
import pytest
from devassistant.gui import run_gui


class TestDevAssistantGUI(object):
    """
    Test class for running DevAssistant GUI
    """
    def test_environment_display(self):
        """
        test for detection wrong environment DISPLAY variable
        """
        with pytest.raises(SystemExit):
            display = os.environ.get('DISPLAY')
            os.environ['DISPLAY'] = ""
            run_gui()
            os.environ['DISPLAY'] = display
