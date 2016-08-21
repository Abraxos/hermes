from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView
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
from kivy.factory import Factory
from settings import settings_json

# data items
class Message(object):
	def __init__(self, msg='', is_selected=False):
                self.msg = msg
		self.is_selected = is_selected

# view items
class ProfileView(SelectableView, Button):
        pass

class TextView(Label):
        pass

class MessageView(SelectableView, BoxLayout, Button):
        pass

class ChannelListItem(Button):
        def __init__(self, name='', is_selected=False):
                self.name = name
                self.is_selected = is_selected

class ChannelScreen(Screen):
        message_list_item_args_converter = lambda row_index, obj: {'name':obj.msg, 
                                                                   'size_hint_y': None,
                                                                   'font_size':15,
                                                                   'halign':'left'}
	message_list_adapter = ListAdapter(data=[],
                                           args_converter=message_list_item_args_converter,
                                           propagate_selection_to_data=True,
                                           cls=MessageView)

class MenuScreen(Screen):
        pass

class SettingScreen(Screen):
        pass

class MainWindow(GridLayout):

        # I'm not sure if kivy maintains a record of screens, their ordered, and current one in view, if it does then the 
        # three globals below are totally unnecessary and can be refractored. 
        screens = []
        current_screen_index = 0
        latest_screen_id = 0

        saved_channels_list=[]
        saved_channels_list_item_args_converter = lambda row_index, obj: {'text':obj.msg, 
                                                                          'size_hint_y': None,
                                                                          'font_size':15,
                                                                          'halign':'left'}
        saved_channels_list_adapter = ListAdapter(data=saved_channels_list,
                                                  args_converter=saved_channels_list_item_args_converter,
                                                  propagate_selection_to_data=True,
                                                  cls=ListItemButton)
                
        # Add menu and setting screens
        screens.append(('setting',None))
        screens.append(('menu',None))
        
        # message controls
        def send_message(self):
                self.post_message()

        def recieve_message(self):
                self.post_message()
        
        # channel controls
        def new_channel(self):
                self.add_channel_to_UI()

        def join_channel(self):
                self.add_channel_to_UI()

        def leave_channel(self):
                self.remove_channel_from_UI()

        # GUI actions
        def post_message(self):
                current_channel = self.screens[self.current_screen_index][1]
                if current_channel is not None:
                        current_channel_message_log = self.screens[self.current_screen_index][2]
                        current_channel_message_log.append(Message(msg='msg_1'))
                        message_list_item_args_converter = lambda row_index, obj: {'name':'message', 
                                                                                   'size_hint_y': None,
                                                                                   'font_size':15,
                                                                                   'halign':'left'}

                        current_channel.ids['chat_log'].adapter = ListAdapter(data=current_channel_message_log,
                                                                              args_converter=message_list_item_args_converter,
                                                                              propagate_selection_to_data=True,
                                                                              cls=MessageView)

                        current_channel.ids['chat_log'].adapter.bind(on_selection_change=self.press_message_list_item)

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

        def press_message_list_item(self, list_adapter, *args):
                if(list_adapter.selection[0].name == 'message'):
                        self.selected_message_control()
                elif(list_adapter.selection[0].name == 'sender'):
                        self.selected_view_profile()

        def find_index_of_selected_channel(self,selection):
                idx = 0
                for screen in self.screens:
                        if(screen[0] == selection):
                                self.current_screen_index = idx
                        idx+=1
        

        # okay... so for this function I wasn't quite sure how to properly index self.screens so that I could
        # simply call self.screens[list_adapter.selection[0].text]. So I resorted to iterating over screens
        # to find the one I'm looking to switch too. If some one could attempt to refractor this that would be great,
        # mhm..kay?
        def press_transition_channel_list_item(self, list_adapter, *args):
                if(len(list_adapter.selection) > 0):
                        for obj in self.screens:
                                if obj[0] == list_adapter.selection[0].text:
                                        sc = self.ids['screen_controls']
                                        sc.transition.direction='up'
                                        sc.current = list_adapter.selection[0].text
                                        self.find_index_of_selected_channel(list_adapter.selection[0].text)
                

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
        
        def add_channel_to_UI(self):
                name = "channel_"+str(self.latest_screen_id)
                new_channel_screen  = ChannelScreen(name=name)
                message_log = []
                
                self.current_screen_index = len(self.screens)
                self.screens.append((name,new_channel_screen,message_log))
                
                self.saved_channels_list.append(ChannelListItem(name=name))
                
                sc = self.ids['screen_controls']
                sc.add_widget(new_channel_screen)
                sc.transition.direction = 'up'
                sc.current = name

                channels_list = self.ids['channel_list']
                self.saved_channels_list_item_args_converter = lambda row_index, obj: {'text':obj.name, 
                                                                                       'size_hint_y': None, 
                                                                                       'font_size':25,
                                                                                       'halign':'right'}
                channels_list.adapter = ListAdapter(data=self.saved_channels_list,
                                                    args_converter=self.saved_channels_list_item_args_converter,
                                                    propagate_selection_to_data=True,
                                                    selection_mode='single',
                                                    allow_empty_selection=False,
                                                    cls=ListItemButton)

                channels_list.adapter.bind(on_selection_change=self.press_transition_channel_list_item)
                
                current_channel = self.screens[self.current_screen_index][1]
                message_list_item_args_converter = lambda row_index, obj: {'name':obj.msg, 
                                                                           'size_hint_y': None,
                                                                           'font_size':15,
                                                                           'halign':'left'}

                current_channel.ids['chat_log'].adapter = ListAdapter(data=message_log,
                                                                      args_converter=message_list_item_args_converter,
                                                                      propagate_selection_to_data=True,
                                                                      cls=MessageView)

                current_channel.ids['chat_log'].adapter.bind(on_selection_change=self.press_message_list_item)

                self.latest_screen_id+=1

        def remove_channel_from_UI(self):
                current_channel = self.screens[self.current_screen_index][1]
                current_channel_name = self.screens[self.current_screen_index][0]

                del self.screens[self.current_screen_index]
                self.current_screen_index = 1
                
                for obj in self.saved_channels_list:
                        if obj.name == current_channel_name:
                                self.saved_channels_list.remove(obj)

                sc = self.ids['screen_controls']
                sc.remove_widget(current_channel)
                sc.transition.direction = 'down'
                sc.current = 'menu'

                channels_list = self.ids['channel_list']
                self.saved_channels_list_item_args_converter = lambda row_index, obj: {'text':obj.name, 
                                                                                       'size_hint_y': None, 
                                                                                       'font_size':25,
                                                                                       'halign':'right'}
                channels_list.adapter = ListAdapter(data=self.saved_channels_list,
                                                    args_converter=self.saved_channels_list_item_args_converter,
                                                    propagate_selection_to_data=True,
                                                    selection_mode='single',
                                                    allow_empty_selection=False,
                                                    cls=ListItemButton)

                channels_list.adapter.bind(on_selection_change=self.press_transition_channel_list_item)

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
