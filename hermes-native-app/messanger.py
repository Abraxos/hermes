from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView
from kivy.uix.recycleview import RecycleView
from kivy.uix.listview import ListItemLabel
from kivy.uix.listview import ListItemButton
from kivy.uix.selectableview import SelectableView
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.settings import SettingsWithSidebar
from kivy.adapters.listadapter import ListAdapter
from kivy.clock import Clock
from kivy.factory import Factory
from settings import settings_json

# VIEW ITEMS
# any newly defined custom UI classes will go here

# SUB-COMPONENTS
# UI items inside the main window
class UserAvatar(SelectableView, Button):
        pass

class MessageTextBox(SelectableView, Button, Label):
        pass

class MessageView(SelectableView, BoxLayout):
        pass

class ConversationListItemView(SelectableView, Button):
        pass

class ConversationScreen(Screen):
        pass

class MenuScreen(Screen):
        pass

class SettingScreen(Screen):
        pass

# MAIN WINDOW
# root window, the parent of all other components
class MainWindow(GridLayout):
        
        # INITIALIZE
        
        # note-to-self: Ivan Pozdnyakov
        # I'm not sure if kivy maintains a record of screens, their ordered, and current one in view, if it does then the 
        # three globals below are totally unnecessary and can be refractored out.
        screens = []
        current_screen_index = 0
        latest_screen_id = 0

        def __init__(self,**kwargs):
                super(MainWindow, self).__init__(**kwargs)
                Clock.schedule_once(self.finish_init)
        
        # USER ACTIONS
        
        # message controls
        def send_message(self):
                self.post_message()

        def recieve_message(self):
                self.post_message()
        
        # conversation controls
        def new_conversation(self):
                self.add_conversation_to_UI()

        def join_conversation(self):
                self.add_conversation_to_UI()

        def leave_conversation(self):
                self.remove_conversation_from_UI()

        def press_message_list_item(self, list_adapter, *args):
                if(len(list_adapter.selection) == 0):
                        pass
                elif(list_adapter.selection[0].name == 'message'):
                        self.selected_message_control()
                elif(list_adapter.selection[0].name == 'user_avatar'):
                        self.selected_view_profile()

        # INTERNALS
        def finish_init(self, dt):
                # Application core will set these based on user data
                self.ids['conversation_list'].data = [{text: item.name} for item in []]
                self.screens.append(('setting',None))
                self.screens.append(('menu',None))
                self.current_screen_index = 0
                self.latest_screen_id = 0

        def post_message(self):
                current_user = 'Ivan Pozdnyakov' 
                text_input = self.ids['text_entry'].text
                current_conversation = self.screens[self.current_screen_index][1]
                if(current_conversation is not None and text_input != ''):
                      current_conversation_message_log = self.screens[self.current_screen_index][2]
                      current_conversation_message_log.append({'text': current_user+':\n'+text_input})
                      current_conversation.ids['chat_log'].data = current_conversation_message_log

        def selected_message_control(self):
                 content = GridLayout(cols=1)
                 content_cancel = Button(text='Cancel', size_hint_y=None, height=40)
                 content.add_widget(Button(text='Reply'))
                 content.add_widget(Button(text='Forward'))
                 content.add_widget(Button(text='Select'))
                 content.add_widget(Button(text='Delete'))
                 content.add_widget(content_cancel)
                
                 popup = Popup(title='Test popup',
                               size_hint=(None, None), size=(256, 256),
                               content=content, disabled=False)
                 
                 content_cancel.bind(on_release=popup.dismiss)
                 popup.open()

        def selected_view_profile(self):
                content = GridLayout(cols=1)
                content_cancel = Button(text='Cancel', size_hint_y=None, height=40)
                content.add_widget(Button(text='Profile'))
                content.add_widget(Button(text='Block'))
                content.add_widget(Button(text='Kick'))
                content.add_widget(Button(text='Ban'))
                content.add_widget(content_cancel)
                
                popup = Popup(title='Test popup',
                              size_hint=(None, None), size=(256, 256),
                              content=content, disabled=False)
                 
                content_cancel.bind(on_release=popup.dismiss)
                popup.open()

        def find_index_of_selected_conversation(self,selection):
                idx = 0
                for screen in self.screens:
                        if(screen[0] == selection):
                                self.current_screen_index = idx
                        idx+=1
        
        def select_transition(self,selection):
                for obj in self.screens:
                       if obj[0] == selection:
                               sc = self.ids['screen_controls']
                               sc.transition.direction='up'
                               sc.current = selection
                               self.find_index_of_selected_conversation(selection)
                

        def swipe_transition(self, direction):
                sc = self.ids['screen_controls']
                if(direction =='left' and self.current_screen_index == 0):
                        sc.transition.direction='left'
                        self.current_screen_index=len(self.screens)-1
                        sc.current = self.screens[self.current_screen_index][0]
                elif(direction == 'right' and self.current_screen_index == len(self.screens)-1):
                        sc.transition.direction = 'right'
                        self.current_screen_index=0
                        sc.current = self.screens[self.current_screen_index][0]
                elif(direction == 'left'):
                        sc.transition.direction = 'left'
                        self.current_screen_index=self.current_screen_index-1
                        sc.current = self.screens[self.current_screen_index][0]
                elif(direction == 'right'):
                        sc.transition.direction = 'right'
                        self.current_screen_index=self.current_screen_index+1
                        sc.current = self.screens[self.current_screen_index][0]
        
        def add_conversation_to_UI(self):
                name = "conversation_"+str(self.latest_screen_id)
                new_conversation_screen  = ConversationScreen(name=name)
                
                self.current_screen_index = len(self.screens)
                self.screens.append((name,new_conversation_screen,[]))
                
                sc = self.ids['screen_controls']
                sc.add_widget(new_conversation_screen)
                sc.transition.direction = 'up'
                sc.current = self.screens[self.current_screen_index][0]

                self.ids['conversation_list'].data.append({'text':name})
                current_conversation = self.screens[self.current_screen_index][1]

                self.latest_screen_id+=1

        def remove_conversation_from_UI(self):
                current_conversation = self.screens[self.current_conversation_index][1]
                current_conversation_name = self.screens[self.current_screen_index][0]

                del self.screens[self.current_screen_index]
                self.current_screen_index = 1
                
                for obj in self.ids['conversation_list'].data:
                        if obj['text'] == current_conversation_name:
                                self.ids['conversation_list'].data.remove(obj)

                sc = self.ids['screen_controls']
                sc.remove_widget(current_conversation)
                sc.transition.direction = 'down'
                sc.current = 'menu'

class Messanger(App):
	def build(self):
                self.settings_cls = SettingsWithSidebar
                self.use_kivy_settings = False
                settings = self.config.get('example', 'boolexample')
		return MainWindow()

        def build_config(self, config):
                config.setdefaults('example',{
                        'boolexample': True,
                        'numericexample':10,
                        'optionsexample': 'option2',
                        'stringexample': 'some_string',
                        'pathexample': '/some/path'})

        def build_settings(self, settings):
                settings.add_json_panel('Panel Name', 
                                        self.config, 
                                        data=settings_json)

        def on_config_change(self, config, section, key, value):
                print config, section, key, value

if __name__ == "__main__":
	Messanger().run()
