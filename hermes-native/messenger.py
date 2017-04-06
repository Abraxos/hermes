"""This module houses the native-application UI/GUI application code,
it will use the Hermes API under the hood."""
import os
import base64
import hashlib
import binascii
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView #pylint: disable=W0611
from kivy.uix.recycleview import RecycleView #pylint: disable=W0611
from kivy.uix.listview import ListItemLabel #pylint: disable=W0611
from kivy.uix.listview import ListItemButton #pylint: disable=W0611
from kivy.uix.selectableview import SelectableView
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput #pylint: disable=W0611
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition #pylint: disable=W0611
from kivy.uix.dropdown import DropDown #pylint: disable=W0611
from kivy.uix.settings import SettingsWithSidebar
from kivy.adapters.listadapter import ListAdapter #pylint: disable=W0611
from kivy.clock import Clock
from kivy.factory import Factory #pylint: disable=W0611
#from kivy.support import install_twisted_reactor #D##ISABLING FOR NOW###
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from settings import settings_json

# PRELIMINARY
#install_twisted_reactor() ###DISABLING FOR NOW###

from twisted.internet import reactor, protocol #pylint: disable=C0413

# UTILITY
# Custom Application Methods will go here, components that need something from
# here will inherit this class.
class MessengerUtility(object):
    """Contains useful custom utilities specific to this application."""
    def find_main_window(self):
        """Find the main window, to call methods encapsulated there."""
        return self.__search_main_window(self)

    def __search_main_window(self, root):
        """Simple recursive search for main window."""
        if hasattr(root, 'name') and root.name is 'main_window':
            return root
        else:
            return self.__search_main_window(root.parent)


# VIEW ITEMS
# any newly defined custom UI classes will go here

# SUB-COMPONENTS
# UI items inside the main window

class ContactNameBox(SelectableView, Button, Label, MessengerUtility):
    """Contact Name Banner Box element."""
    pass

class ContactDeleteBox(SelectableView, Button, MessengerUtility):
    """Contact Delete Box element."""
    pass

class ContactView(SelectableView, BoxLayout, MessengerUtility):
    """Contact list item element."""
    pass

class UserAvatar(SelectableView, Button, MessengerUtility):
    """User avatar element."""
    pass

class MessageTextBox(SelectableView, Button, Label, MessengerUtility):
    """Message text box element."""
    pass

class MessageView(SelectableView, BoxLayout, MessengerUtility):
    """Message container element."""
    pass

class ConversationListItemView(SelectableView, Button, MessengerUtility):
    """Conversation list item element."""
    pass

class ConversationScreen(Screen, MessengerUtility):
    """A screen for a specific conversation, will house the message log."""
    pass

class AddConversationScreen(Screen, MessengerUtility):
    """A screen for adding new conversations, either creating or joining."""
    pass

class CreateConversation(BoxLayout, MessengerUtility):
    """Form for conversation creation."""
    pass

class JoinConversation(BoxLayout, MessengerUtility):
    """Form for conversation joining."""
    pass

class ContactsList(BoxLayout, MessengerUtility):
    """contact list."""
    pass

class ContactsAdd(BoxLayout, MessengerUtility):
    """Form for adding contacts."""
    pass

class ContactsScreen(Screen, MessengerUtility):
    """A screen for displaying all of a users contacts."""
    pass

class SettingScreen(Screen, MessengerUtility):
    """A screen for changing user and application configuration settings."""
    pass

class LoginScreen(Screen, MessengerUtility):
    """A screen for login into the application (will unlock the local data cache)."""
    pass

class RegisterScreen(Screen, MessengerUtility):
    """A screen for registering a passphrase (for decryption)."""
    pass

# MAIN WINDOW
# root window, the parent of all other components
class MainWindow(GridLayout):
    """The root element of the application."""
    # INITIALIZE

    # note-to-self: Ivan Pozdnyakov
    # I'm not sure if kivy maintains a record of screens, their ordered, and
    # current one in view, if it does then the
    # three globals below are totally unnecessary and can be refractored out.
    latest_screen_id = 0

    # These handle global logic for whether you are logged in/etc
    no_passphrase = True
    no_login = True

    # This is used to encrypt and decrypt local cache
    fernet = None

    # Salt for creating hashs
    salt = None

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        Clock.schedule_once(self.finish_init)
        app = App.get_running_app()
        # Expose for testing
        app.main_window = self

    # USER ACTIONS

    # start up actions
    def login(self, passphrase):
        """login."""
        with open('archive/init.config', 'rb') as config_file:
            self.salt = config_file.read()
        self.init_fernet(passphrase)
        try:
            self.unlock()
        except InvalidToken:
            self.display_error('login error', 'Opps, password is incorrect.')

    def register(self, passphrase, reenter_passphrase):
        """register."""
        if passphrase != reenter_passphrase:
            self.display_error('register error', 'Passphrases not matchings, try again.')
        elif len(passphrase) < 15:
            self.display_error('register error', 'Passphrases less than 15 characters, try again.')
        else:
            self.salt = os.urandom(16)
            self.no_passphrase = False
            self.init_fernet(passphrase)
            self.populate_archive()
            self.unlock()

    # message controls
    def send_message(self, text_input):
        """send a message to converation."""
        screen_controls = self.ids['screen_controls']
        app = App.get_running_app()
        current_user = 'Ivan Pozdnyakov'
        current_conversation = screen_controls.get_screen(screen_controls.current)
        #if text_input and app.connection:
        # app.connection.write(str(text_input)) ###DISABLING FOR NOW###
        self.post_message_visually(current_user, current_conversation, text_input)
        self.update_conversation_log()

        self.ids['text_entry'].text = ""

    def recieve_message(self, text_recieved):
        """recieve a message from the converation."""
        peer_user = 'Shadow Ivan Pozdnyakov'
        screen_controls = self.ids['screen_controls']
        current_conversation = screen_controls.get_screen(screen_controls.current)
        self.post_message_visually(peer_user, current_conversation, text_recieved)
        self.update_conversation_log()

    # conversation controls
    def new_conversation(self):
        """create a converation."""
        name = "conversation_"+str(self.latest_screen_id)
        self.add_conversation_visually(name)
        self.create_conversation_log()

    def join_conversation(self):
        """join a converation."""
        name = "conversation_"+str(self.latest_screen_id)
        self.add_conversation_visually(name)
        self.create_conversation_log()

    def leave_conversation(self):
        """leave a conversation."""
        self.delete_conversation_log()
        self.remove_conversation_visually()

    def press_message_list_item(self, selection):
        """select a message container element, will execute differently
        depending on whether avatar or message is selected."""
        if selection == 'message':
            self.selected_message_control()
        elif selection == 'user_avatar':
            self.selected_view_profile()

    # contact screen controls
    def add_contact(self, username):
        self.add_contact_visually(username)
        self.create_a_contact_file(username)

    def delete_contact(self, username):
        self.remove_contact_visually(username)
        self.delete_a_contact_file(username)

    def invite_contact(self):
        """Invite a contact to a group."""
        pass

    # INTERNALS
    def display_error(self, error, message):
        """Display an error popup with specific error title and messsage."""
        content = GridLayout(cols=1)
        content_cancel = Button(text='Cancel', size_hint_y=None, height=40)
        content.add_widget(Label(text=message))
        content.add_widget(content_cancel)

        popup = Popup(title=error,
                      size_hint=(None, None), size=(256, 256), content=content, disabled=False)

        content_cancel.bind(on_release=popup.dismiss)
        popup.open()

    def finish_init(self, delta_time): #pylint: disable=W0613
        """A call back for when the application is finished initializing."""
        # Application core will set these based on user data
        self.ids['conversation_list'].data = [{'text': item.name} for item in []]
        self.latest_screen_id = 0
        self.no_passphrase = self.archive_not_populated()
        if self.no_passphrase:
            self.force_transition('register')
        else:
            self.force_transition('login')

    def archive_not_populated(self):
        """check whether the archive folder is populated."""
        if os.listdir('archive') == []:
            return True
        else:
            return False

    def populate_archive(self):
        """Save our salt in the archive folder."""
        with open('archive/init.config', 'wb') as outfile:
            outfile.write(self.salt)

    def unlock(self):
        """Unlock the application data on filesystem and populate in the UI."""
        for log in os.listdir('archive'):
            if log.endswith('conversation.log'):
                with open('archive/'+log, 'r') as log_file:
                    read_title = True
                    for cipher in log_file:
                        clear = self.fernet.decrypt(str.encode(cipher.rstrip()))
                        if read_title:
                            self.add_conversation_visually(clear.decode())
                            read_title = False
                        else:
                            screen_controls = self.ids['screen_controls']
                            message = clear.decode().split(':\n')
                            conversation = screen_controls.get_screen(screen_controls.current)
                            self.post_message_visually(message[0], conversation, message[1])
            elif log.endswith('contact.log'):
                with open('archive/'+log, 'r') as log_file:
                    for cipher in log_file:
                        clear = self.fernet.decrypt(str.encode(cipher))
                        self.add_contact_visually(clear.decode())


        self.no_login = False
        self.force_transition('settings')

    def init_fernet(self, passphrase):
        """initialize our fernet global, which we can use for encryption/decryption."""
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=bytes(self.salt),
                         iterations=100000, backend=default_backend())
        key = base64.urlsafe_b64encode(kdf.derive(str.encode(passphrase)))
        self.fernet = Fernet(key)

    def post_message_visually(self, current_user, current_conversation, text_input):
        """visually display any new messages."""
        if current_conversation is not None and text_input != '':
            message_log = current_conversation.ids['chat_log'].data
            message_log.append({'text': current_user+':\n'+text_input})
            current_conversation.ids['chat_log'].data = message_log

    def selected_message_control(self): #pylint: disable=R0201
        """visually display a message select popup."""
        content = GridLayout(cols=1)
        content_cancel = Button(text='Cancel', size_hint_y=None, height=40)
        content.add_widget(Button(text='Reply'))
        content.add_widget(Button(text='Forward'))
        content.add_widget(Button(text='Select'))
        content.add_widget(Button(text='Delete'))
        content.add_widget(content_cancel)

        popup = Popup(title='Test popup', size_hint=(None, None),
                      size=(256, 256), content=content, disabled=False)
        content_cancel.bind(on_release=popup.dismiss)
        popup.open()

        # expose for unit testing
        app = App.get_running_app()
        app.message_control = content

    def selected_view_profile(self): #pylint: disable=R0201
        """visually display a profile select popup."""
        content = GridLayout(cols=1)
        content_cancel = Button(text='Cancel', size_hint_y=None, height=40)
        content.add_widget(Button(text='Profile'))
        content.add_widget(Button(text='Block'))
        content.add_widget(Button(text='Kick'))
        content.add_widget(Button(text='Ban'))
        content.add_widget(content_cancel)

        popup = Popup(title='Test popup',
                      size_hint=(None, None), size=(256, 256), content=content, disabled=False)

        content_cancel.bind(on_release=popup.dismiss)
        popup.open()

        # expose for unit testing
        app = App.get_running_app()
        app.profile_control = content

    def select_transition(self, selection):
        """Do a visual transition on conversation select."""
        screen_controls = self.ids['screen_controls']
        screen_controls.transition.direction = 'up'
        screen_controls.current = selection

    def force_transition(self, too):
        """Visually do a transition when programatically selected."""
        screen_controls = self.ids['screen_controls']
        screen_controls.transition.direction = 'up'
        if self.no_passphrase:
            # Go to Register screen
            screen_controls.current = 'register'
        elif self.no_login:
            # Go to Login screen
            screen_controls.current = 'login'
        else:
            # Go to page that was requested
            screen_controls.current = too

    def add_conversation_visually(self, name):
        """Visually add a new conversation screen."""
        new_conversation_screen = ConversationScreen(name=name)

        screen_controls = self.ids['screen_controls']
        screen_controls.add_widget(new_conversation_screen)
        screen_controls.transition.direction = 'up'
        screen_controls.current = name

        self.ids['conversation_list'].data.append({'text':name})

        self.latest_screen_id += 1

    def remove_conversation_visually(self):
        """Visually remove a conversation screen."""
        screen_controls = self.ids['screen_controls']

        for obj in self.ids['conversation_list'].data:
            if obj['text'] == screen_controls.current:
                self.ids['conversation_list'].data.remove(obj)

        screen_controls.remove_widget(screen_controls.current_screen)
        screen_controls.transition.direction = 'down'
        screen_controls.current = 'settings'

    def add_contact_visually(self, username):
        """Visually add a contact to contact list."""
        contact_screen = self.ids['screen_controls'].get_screen('contacts')
        contact_screen.ids['contact_list_container'].\
        ids['contact_list'].data.append({'text':username})

    def remove_contact_visually(self, username):
        """Visually remove a contact from contact list."""
        contact_screen = self.ids['screen_controls'].get_screen('contacts')

        for obj in contact_screen.ids['contact_list_container'].ids['contact_list'].data:
            print(obj['text'])
            if obj['text'] == username:
                contact_screen.ids['contact_list_container'].ids['contact_list'].data.remove(obj)

    # Will update the conversation log when message is posted.
    def update_conversation_log(self):
        """Update the local conversation log with latest message."""
        screen_controls = self.ids['screen_controls']
        dk = hashlib.pbkdf2_hmac('sha256', str.encode(screen_controls.current), self.salt, 100000)
        with open('archive/'+binascii.hexlify(dk).decode()+'_conversation.log', 'a') as outfile:
            current_conversation = screen_controls.get_screen(screen_controls.current)
            message_log = current_conversation.ids['chat_log'].data
            entry = message_log[-1]['text']
            outfile.write(self.fernet.encrypt(str.encode(entry)).decode()+'\n')

    # Will create a converation log
    def create_conversation_log(self):
        """Create the local conversation log, first line will have some meta-data."""
        screen_controls = self.ids['screen_controls']
        dk = hashlib.pbkdf2_hmac('sha256', str.encode(screen_controls.current), self.salt, 100000)
        with open('archive/'+binascii.hexlify(dk).decode()+'_conversation.log', 'a') as outfile:
            outfile.write(self.fernet.encrypt(str.encode(screen_controls.current)).decode()+ '\n')

    # Will delete a conversation log
    def delete_conversation_log(self):
        """Delete the conversation log."""
        screen_controls = self.ids['screen_controls']
        dk = hashlib.pbkdf2_hmac('sha256', str.encode(screen_controls.current), self.salt, 100000)
        os.remove('archive/'+binascii.hexlify(dk).decode()+'_conversation.log')

    # Will create a contact file
    def create_a_contact_file(self, username):
        dk = hashlib.pbkdf2_hmac('sha256', str.encode(username), self.salt, 100000)
        with open('archive/'+binascii.hexlify(dk).decode()+'_contact.log', 'a') as outfile:
            outfile.write(self.fernet.encrypt(str.encode(username)).decode()+ '\n')

    # Will delete a contact file
    def delete_a_contact_file(self,username):
        dk = hashlib.pbkdf2_hmac('sha256', str.encode(username), self.salt, 100000)
        os.remove('archive/'+binascii.hexlify(dk).decode()+'_contact.log')

# APPLICATION
# contains everything else that is defined
class Messenger(App):
    """Messenger application."""
    connection = None

    def build(self):
        """Build the application."""
        self.connect_to_server()
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        return MainWindow()

    def build_config(self, config):
        """Set configuration."""
        config.setdefaults('example', {
            'boolexample': True,
            'numericexample':10,
            'optionsexample': 'option2',
            'stringexample': 'some_string',
            'pathexample': '/some/path'})

    def build_settings(self, settings):
        """Set settings."""
        settings.add_json_panel('Example Settings', self.config, data=settings_json)
        settings.add_json_panel('User Settings', self.config, data=settings_json)

    def connect_to_server(self):
        """Connect to an echo service."""
        reactor.connectTCP('localhost', 8000, EchoFactory(self)) #pylint: disable=E1101

    def on_config_change(self, config, section, key, value):
        """on a config change we report back information."""
        #print config, section, key, value

    def on_connection(self, connection):
        """on established connection set the connection variable."""
        self.connection = connection


# Connection
class EchoClient(protocol.Protocol): #pylint: disable=W0232
    """Handle recieved data."""
    def connectionMade(self):
        self.factory.app.on_connection(self.transport) #pylint: disable=E1101

    def dataReceived(self, data):
        self.factory.app.main_window.recieve_message(data) #pylint: disable=E1101

class EchoFactory(protocol.ClientFactory):
    """Echo Client-side Factory."""
    protocol = EchoClient

    def __init__(self, app):
        self.app = app

    def clientConnectionLost(self, conn, reason):
        pass

    def clientConnectionFailed(self, conn, reason):
        pass

if __name__ == "__main__":
    Messenger().run()
