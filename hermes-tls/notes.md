# Setup Notes for TLS Fork of Hermes

## Pre-Requisites

Basic packages:

```
$ sudo apt install virtualenvwrapper python-dev build-essential
```

Python-specific packages (inside the virtual environment):

```
$ mkvirtualenv hermes
(hermes)$ pip install twisted cryptography pyopenssl attr msgpack-python bcrypt service_identity
(hermes)$ add2virtualenv /path/to/parent/folder/of/hermes/
```

## Testing

To run unit tests:

```
(hermes)$ trial hermes.test.test_identity_service
```

### Running The Example Client

To run the example client you first need to start up the hermes identity server in one terminal, with a port, private key, cert, and certificate authority cert:

```
(hermes)$ python hermes/server/identity/hermes_id_server.py 8000 hermes/test/testing_keys/server/server.key hermes/test/testing_keys/server/server.cert hermes/test/testing_keys/ca/ca.cert
```

Then you can run the example client which currently only supports identity server functionality (full functionality coming soon):

```
(hermes)$ python hermes/examples/simple_registration_client_example.py localhost 8000
```

## Setting Up Atom Development Environment

```
(hermes)$ pip install pylint
```

Then, in the pylint package settings in Atom, change the executable path to be the path for the pylint exectuable in your virtual env. For example:

```
/home/<username>/.virtualenvs/hermes/bin/pylint
```

## Task Tracking

+ Hermes Identity System
  + [ ] Write the Hermes Identity Server
    + [x] Write the identity server to handle CSRs and create certificates for users
      + [x] Test this functionality
    + [ ] Update the Hermes ID Server to use a database
    + [x] Write unit tests
    + [ ] Integrate the Hermes ID Server into a proper package and replace the existing Hermes code
  + [ ] Write the Hermes Identity Client functionality to connect with the server
    + [ ] Write a thread system that launches the reactor in a thread and provides convenient functionality for the UI
      + [ ] Design the API that should be accessible to the UI components
    + [ ] Write basic ID functionality and use it to test the server
+ Hermes Invite System
+ Hermes Relay System

## General Architecture Overview

Hermes Server is broken up into several independent microservices which work together to feed relevant information into the database and relay messages between clients. There are three primary services as of right now: the identity server, the invite server, and the relay server. Other services may be added later and they may eventually be packaged together somehow, but for the time being, the three will be developed as separate applications in order to make the process a little bit easier. The identity server is what allows people to create the credentials and passwords required to authenticate users to the other services. The invite server is how users create conversations and invite other users to join in on those conversations. The relay server is the one that sends messages from senders to all the recipients that are part of a particular conversation.

### Hermes Identity Server

An extremely basic server that handles username registration and fetching requests. The server does not authenticate users because this is the server that new users connect to. This is also the server that users contact when they want to add another device by fetching its key. This is done by first authenticating the user to ensure that they own their username and then sending them their private key encrypted with a password and AES256 (since the server cannot be allowed to possess the user's private key).

```
Protocol Tree:
└── Client establishes TLS connection without client-authentication (Note the
    client must already posess the CA, consider distribution with a server
    configuration)
    ├── Client sends the server a "register" request with their username,
    │   server-password and a CSR (note that there are two passwords, one to log
    │   in and one to decrypt your private key)
    │   ├── If the username already exists the server rejects the request and
    │   │   terminates the connection
    │   └── If the username doesn't already exist, the server registers the
    │       username to the database and returns a signed certificate based on
    │       the CSR
    ├── Client sends the server a "fetch" request with a username
    │   ├── if the username exists on the server, the server replies with that
    |   |   user's certificate
    |   └── if the username does not exist on the server, the server terminates
    |       the connection
    └── Client sends the server a "fetch my" request with a username and password
        ├── if the password is valid (hash and salt), the server responds with
        |   an encrypted private key (needs to be unlocked with another
        |   password)
        └── if the password is invalid the server terminates the connection
```

### Hermes Conversation Server

This is the service that handles creating conversations and adding users to them. The client must authenticate using TLS in order to connect to this service. The service has two primary functionalities: to create new conversations and to add new users to those conversations. To that end it is also capable of sending messages to connected users to invite them to new conversations as well as handling leave requests when a user wants to leave a conversation.

```
Protocol Tree
└── Client establishes a TLS connection in which both the client and server are
    authenticated.
    ├── Client sends the server a "create" request
    |   └── The Server replies with a UUID of the conversation once it has been
    |       created
    ├── Client sends the server an "invite" request with the username of the
    |   user to be invited as well as a symmetric key encrypted with their
    |   public key
    |   ├── If the username is valid and exists on the server, the server
    |   |   replies with an acknowledgement and adds the user to the
    |   |   conversation
    |   └── If the username does not exist, the server returns an error
    ├── Client sends the server a "leave" request with the UUID of the
    |   conversation that they want to leave. They are then removed from the
    |   conversation and messages are no longer sent to them.
    └── The server sends the client an "invite" message which includes the UUID of
        the conversation that they have been invited to as well as the symmetric
        key used to decrypt the conversation encrypted with their public key so
        that only they can decrypt it.
```

### Hermes Relay Server

This is the actual server that routs messages between clients and allows them to establish conversations

Protocol Tree

1.
  1. Client sends the server a "start" conversation request which includes the certificate of one or multiple other conversation participants
    1. The server generates a conversation UUID and returns it to the user
  2. Client sends the server an "invite" conversation request which includes the conversation UUID and a challenge (the sender must already have the recipient's certificate)
    1. The server relays the invitation to the recipient along with the sender's certificate
      1. The invite recipient sends (via the server) the signed challenge along with a challenge of his own
  3. Client sends the server a "leave" conversation request
