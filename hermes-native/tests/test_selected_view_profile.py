import unittest

import os
import sys
import time
import os.path as op
from functools import partial
from kivy.clock import Clock

main_path = op.dirname(op.dirname(op.abspath(__file__)))
sys.path.append(main_path)

from messanger import Messanger

class Test(unittest.TestCase):
    # sleep function that catches `dt` from Clock
    def pause(*args):
        time.sleep(0.000001)

    # main test function
    def run_test(self, app, *args):
        Clock.schedule_interval(self.pause, 0.000001)

        # Setup
        app.main_window.finish_init(None)
        
        # Execute
        app.main_window.selected_view_profile()

        # Assert
        self.assertEqual("Cancel", app.profile_control.children[0].text)
        self.assertEqual("Ban", app.profile_control.children[1].text)
        self.assertEqual("Kick", app.profile_control.children[2].text)
        self.assertEqual("Block", app.profile_control.children[3].text)
        self.assertEqual("Profile", app.profile_control.children[4].text)
        # Comment out if you are editing the test, it'll leave the
        # Window opened.
        app.stop()

    # same named function as the filename(!)
    def test_selected_view_profile(self):
        app = Messanger()
        p = partial(self.run_test, app)
        Clock.schedule_once(p, 0.000001)
        app.run()

if __name__ == '__main__':
    unittest.main()
