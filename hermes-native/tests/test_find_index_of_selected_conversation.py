import unittest

import os
import sys
import time
import os.path as op
from functools import partial
from kivy.clock import Clock

main_path = op.dirname(op.dirname(op.abspath(__file__)))
sys.path.append(main_path)

from messenger import Messenger

class Test(unittest.TestCase):
    # sleep function that catches `dt` from Clock
    def pause(*args):
        time.sleep(0.000001)

    # main test function
    def run_test(self, app, *args):
        Clock.schedule_interval(self.pause, 0.000001)

        # Setup
        app.main_window.finish_init(None)
        app.main_window.add_conversation_to_UI()

        # Execute
        app.main_window.find_index_of_selected_conversation('conversation_0')

        # Assert
        self.assertEqual(app.main_window.current_screen_index, 2)

        # Comment out if you are editing the test, it'll leave the
        # Window opened.
        app.stop()

    # same named function as the filename(!)
    def test_find_index_of_selected_conversation(self):
        app = Messenger()
        p = partial(self.run_test, app)
        Clock.schedule_once(p, 0.000001)
        app.run()

if __name__ == '__main__':
    unittest.main()
