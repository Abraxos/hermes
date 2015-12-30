# Developer Instructions for Hermes-API

In order to get Hermes running in a way to develop parts of it, there are several things that need to be done. This document both tracks what was done to set up Hermes as a package and what needs to be done to get Hermes running well enough to run the unit tests.

## Getting to a Point Where One Can Run Unit Tests

Assuming you have cloned the hermes git repo. Run the following code starting from the hermes directory (i.e. the top-level directory in git).

### Step 1: Setup VirtualEnv using VirtualEnvWrapper



## How We Set Up Hermes

This section serves as a kind of environment setup log to track exactly what we did and how we did it as we developed Hermes. One should read this section, but it is not necessary to do anything here to get Hermes up and running. There is a lot in common between this section and the one above.

### Step 1: Installing VirtualEnv and VirtualEnvWrapper

Hermes uses python 3.4. As such, the first step was to make a python 3.4 virtualenv. For this I used the virtualenvwrapper script that is available [here](https://virtualenvwrapper.readthedocs.org/en/latest/install.html). VirtualEnvWrapper is a very nice tool for managing various virtual environments without polluting any of the actual development directories.

To install virtualenv and virtualenvwrapper on a Debian-based system, the following commands should be used.

```
# apt-get install virtualenv
# apt-get install virtualenvwrapper
```

### Step 2: Setting Up a Virtual Environment

To setup the virtual environment, we simply need to execute the following commands:

```
$ mkvirtualenv --python=/usr/bin/python3.4 hermeslib
```

We can then enter the virtual environment by simply executing the command:

```
$ workon hermeslib
```

The cool part is that you can execute the `workon` command from any directory and get the hermeslib virtualenv.

### Step 3: Installing Required Python Packages

Hermes requires several python pacakges to function properly. The following should be installed inside the virtual env:

```
(hermeslib)$ pip install twisted
(hermeslib)$ pip install sqlalchemy
(hermeslib)$ pip install pycrypto
(hermeslib)$ pip install rsa
```

### Step 4: Setting Up the HermesLib Package

The next step is to make HermesLib into a package inside the virtual environment. For this, we are going to use a very nice tool called pastescript which generates all the metadata that we need to be included in the python package. So, assuming we executed step 2, we should now be in the hermeslib virtualenv and can execute the following:

```
(hermeslib)$ mkdir hermeslib
(hermeslib)$ pip install pastescript
```

Then we create the actual package which involves answering some questions for the script:

```
(hermeslib)$ paster create hermeslib
Selected and implied templates:
  PasteScript#basic_package  A basic setuptools-enabled package

Variables:
  egg:      hermeslib
  package:  hermeslib
  project:  hermeslib
Enter version (Version (like 0.1)) ['']: 0.0.1
Enter description (One-line description of the package) ['']: Library for servers and clients of the Hermes Secure Messaging Protocol
Enter long_description (Multi-line description (in reST)) ['']: Hermes is a protocol for secure chat messaging. This library defines the core of protocol as well as giving sample APIs that use it on both the server and the client sides.
Enter keywords (Space-separated keywords/tags) ['']: hermes cryptography chat messenger client server network twisted
Enter author (Author name) ['']: Eugene Kovalev
Enter author_email (Author email) ['']: euge.kovalev@gmail.com
Enter url (URL of homepage) ['']: eugene.kovalev.systems
Enter license_name (License name) ['']: GPLv3
Enter zip_safe (True/False: if the package can be distributed as a .zip file) [False]: False
Creating template basic_package
  Recursing into +package+
    Creating ./hermeslib/hermeslib/
    Copying __init__.py to ./hermeslib/hermeslib/__init__.py
    Recursing into __pycache__
      Creating ./hermeslib/hermeslib/__pycache__/
  Copying setup.cfg to ./hermeslib/setup.cfg
  Copying setup.py_tmpl to ./hermeslib/setup.py
Running /home/eugene/.virtualenvs/hermeslib/bin/python3.4 setup.py egg_info
```

### Step 5: Creating Package Components

By the time we did this step, we already had some of the source code (in fact this was meant to be a refactoring to get the imports to work properly). However, the general plan went something like this:

```
(hermeslib)$ cd hermeslib
(hermeslib)$ mkdir client
(hermeslib)$ touch client/__init__.py
(hermeslib)$ mkdir server
(hermeslib)$ touch server/__init__.py
(hermeslib)$ mkdir crypto
(hermeslib)$ touch crypto/__init__.py
(hermeslib)$ mkdir tests
(hermeslib)$ touch test/__init__.py
```

Then we can simply move/create the relevant files in their respective folders.

The final resulting `hermeslib` (corresponding to `./` in the example below) directory at the end of this process looked something like this (note that there is another `hermeslib` directory in there):
```
./
├── hermeslib
│   ├── client
│   │   ├── client_session.py
│   │   ├── hermes_client.py
│   │   └── __init__.py
│   ├── crypto
│   │   ├── crypto.py
│   │   ├── __init__.py
│   │   └── __pycache__
│   │       ├── crypto.cpython-34.pyc
│   │       └── __init__.cpython-34.pyc
│   ├── __init__.py
│   ├── __pycache__
│   ├── server
│   │   ├── hermes_server.py
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── hermes_server.cpython-34.pyc
│   │   │   ├── __init__.cpython-34.pyc
│   │   │   └── server_session.cpython-34.pyc
│   │   └── server_session.py
│   ├── tests
│   │   ├── hermes_server_tests.py
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   └── test_crypto.cpython-34.pyc
│   │   ├── test_crypto.py
│   │   └── testing_data
│   │       ├── client_test_key.pem
│   │       ├── client_test_key_pub.pem
│   │       ├── server_test_key.pem
│   │       └── server_test_key_pub.pem
│   └── utils
│       ├── __init__.py
│       ├── logging.py
│       └── __pycache__
│           ├── __init__.cpython-34.pyc
│           └── logging.cpython-34.pyc
├── hermeslib.egg-info
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── top_level.txt
│   └── zip-safe
├── setup.cfg
└── setup.py
```

### Step 6: Develop!

The final step is to simply execute the following command every time you want to work on hermeslib. Please note that this should be executed from top-level hermeslib directory. This will setup everything you need with the package paths to actually be able to run the code.

```
(hermeslib)$ python setup.py develop
```
