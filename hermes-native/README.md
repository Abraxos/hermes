<h1> Hermes-Native-UI</h1>
<p>The UI Component for the Hermes Messenger application. https://github.com/Abraxos/hermes. Currently a work in progess.</p>

<h2> Kivy Installation in Virtual Env (directly copied from their site)</h2>

<h3> Install necessary system packages </h3>

```
sudo apt-get install -y \
    python-pip \
    build-essential \
    git \
    python \
    python-dev \
    ffmpeg \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev
```
<p> <i> Note: Depending on your Linux version, you may receive error messages related to the “ffmpeg” package. In this scenario, use “libav-tools ” in place of “ffmpeg ” (above), or use a PPA (as shown below):</i></p>
```
- sudo add-apt-repository ppa:mc3man/trusty-media
- sudo apt-get update
- sudo apt-get install ffmpeg
```
<h3>Installation</h3>
<p>Make sure Pip, Virtualenv and Setuptools are updated</p>
```
sudo pip install --upgrade pip virtualenv setuptools
```
<p>Create a virtualenv</p>
```
virtualenv --no-site-packages kivyinstall
```
<p>Enter the virtualenv</p>
```
. kivyinstall/bin/activate
```
<p>Use correct Cython version here</p>
```
pip install Cython==0.23
```
<p>Install stable version of Kivy into the virtualenv</p>
```
pip install kivy
```
<p>For the development version of Kivy, use the following command instead</p>
```
pip install git+https://github.com/kivy/kivy.git@master
```
<h3>Running the Messanger</h3>
<p>Put messanger.kv and messanger.py in the same directory and run the line below whilst working on the virtualenv kivyinstall:</p>

```
python  messanger.py
```

<h2>Unit-Testing</h2>

<h6>KivyUnitTest</h6>
<p> Use the follow script to run tests: https://github.com/KeyWeeUsr/KivyUnitTest . </p>
```
pip install kivyunittest
```
<p> Add new tests to the test folder; The naming format for the test file is as followed. 'test_'+function_under_test+'.py'. Our functions should all be concise units, meaning don't have functions that do more than one thing. Also avoid testing wrappers, pipelines, or library codes. Unit test isn't mean't to be an integration test, tests aren't suppose to be dependent on a file system or database, use mocks and stubs where appropriate. Below I have included a general template for you to write tests.</p>

```python
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
        
        # Execute

        # Assert

        # Comment out if you are editing the test, it'll leave the
        # Window opened.
        app.stop()

    # same named function as the filename(!)
    def test_function(self):
        app = Messanger()
        p = partial(self.run_test, app)
        Clock.schedule_once(p, 0.000001)
        app.run()

if __name__ == '__main__':
    unittest.main()
```

<p> You should just need to fill Setup, Execute, Assert. If you want to test internals you will need to expose methods and functions, we will eventually wrap these codeblocks with if statement, so that it only runs in development or test environments.</p>

```python
app = App.get_running_app()
app.reference = what_I_want_to_test
```

<h6>Coverage</h6>
<p>Because KivyUnitTest is a testing suite that spawns subprocesses to do the actual tests you will need to set yourself up to be able to run coverage properly. I have outlined the steps on how to proceed below</p>

* <i>Create an environmental variable in your current shell, called COVERAGE_PROCESS_START, This variable will point to your coverage configuration file, which I have provided in the repository (.converagerc). To set it for current shell and all processes started from current shell, run:</i>
```shell
export COVERAGE_PROCESS_START="my value" 
```
* <i>To set it permanently for all future bash sessions add such line to your .bashrc file in your $HOME directory.</i>
* <i>Next you want make a change to sitecustomize.py, it will be in /etc/python2.7. Inside that file append:</i>
```python
# added to be able to do coverage in subprocess (for kivyunittest)
try:
	import coverage
except ImportError:
	pass
else:
	coverage.process_startup()
```
* <i>To run coverage and generate a report, run the following commands from inside the /hermes-native/ directory:</i>
```python
python -m kivyunittest --folder "/home/vanya/Repos/hermes/hermes-native/tests"
coverage combine
coverage report
```

<h2>Basic Styleguide</h2>

<p>Currently all our stuff is in the kivy and python files called messanger. The kv file is some declarative code that specifies how the application will look. Refer to the kivy documentation to learn more about it. The py file maintains all our runnable code. There are a couple regions to it (we'll break it up into multiple files at some point): Firstly, you have the view items/sub-components region. Define all new Kivy classes you need here. Secondly, you have the main window, This is the root component which will nest all the other stuff you have. Inside of here you will have initalize, user actions, and internals. At the bottom you have the App Class (Messanger) which runs the code to create the MainWindow.</p>

* <i>VIEW ITEMS/SUB-COMPONENTS</i>
* <i>MAIN WINDOW</i>
 * <i>INITIALIZE -> Globals and initializations code</i>
 * <i>USER ACTIONS -> Wrappers for calling internals</i>
 * <i>INTERNALS -> Guts of the application</i>
* <i>MESSANGER CLASS</i>

<p> Some general stuff, I use camelBack only for naming classes. For methods and variables I use no_capitals_with_spaces. Also tabs over spaces, always.</p>

<h2>Bugs, Complaints, and Questions</h2>
<p> Post them in the issues section, I will try and respond as soon as possible.</p>
