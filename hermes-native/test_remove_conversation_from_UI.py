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
        app.main_window.add_conversation_to_UI()
        
        sc = app.main_window.ids['screen_controls']
        current_conversation_index = app.main_window.current_screen_index
        current_conversation_object = app.main_window.screens[current_conversation_index]
        conversation_list_item = app.main_window.ids['conversation_list'].data[0]

        # Execute
        app.main_window.remove_conversation_from_UI()

        # Assert
        self.assertNotIn(current_conversation_object, app.main_window.screens)
        self.assertNotIn(current_conversation_object[1], sc.children)
        self.assertNotIn(conversation_list_item,app.main_window.ids['conversation_list'].data)
        self.assertEqual(sc.current,'menu')

        # Comment out if you are editing the test, it'll leave the
        # Window opened.
        app.stop()

    # same named function as the filename(!)
    def test_remove_conversation_from_UI(self):
        app = Messanger()
        p = partial(self.run_test, app)
        Clock.schedule_once(p, 0.000001)
        app.run()

if __name__ == '__main__':
    unittest.main()
