# Hermes
A secure messaging system with a focus on usability and configurability developed by the UConn Cyber Security Club

## Summary:

Hermes is a system for secure messaging on computers and smartphones currently in development. As such it will include a server, protocol, and desktop and smartphone clients. While there are many secure messaging clients, Hermes aims to distinguish itself by focusing on security as well as ease of use and configurability to make it attractive to both advanced, enterprise, and casual users. Hermes is primarily a learning exercise, and in all honesty if it is ever in a state where people can use it, I will be very surprised, but we will take all input seriously and would love for it to become popular. We've taken a lot of inspiration from projects like Telegram, Signal, PGP/GPG, and others, but there are some critical differences: Hermes is comprised of a server client that will be developed using Twisted Python as well as several clients for GNU/Linux, Mac, Windows, Android, and hopefully iOS (depending on whether we can get it to the app store). All of the components will be published under GPLv3 including the server. This means that absolutely anyone will be able to run their own Hermes server for any purpose and the clients will be written to allow anyone to connect to any set of servers.

## Security:

Hermes will primarily secure communication using AES and RSA for identity confirmation. More specifically, communication between the clients and the server will be AES encrypted after an initial confirmation using RSA. Once a user has verified their identity, the server generates a key with which all further communication between it and the client will be encrypted. This is referred to as a session. On top of this, once a user verifies their identity to another, they can generate another key that will encrypt the conversation so that only the metadata is available to the server and all other communication between users is completely secret.

Obviously, the system is still being designed and developed, so we welcome all educated opinions on how certain aspects are to be constructed and handled. Security is a primary objective, but ease-of-use comes in at a close second as we believe in making good habits easy.

## Components:

### Server:

A key component to make this whole system function is of course the server that would relay messages from one user to the other. As of right now, the plan is to write the server in Python, using the Twisted, SQLAlchemy, PyCrypto and Python RSA libraries. The database will be PostGreSQL. A core idea is that anyone should be able to easily set up their own server or use one of the ones that we will be providing by default.

### Desktop Clients:

The first generation of desktop clients will likely be extremely simple, but contain all of the core functionality that we envision for Hermes Messenger. One of our first milestones is a desktop client for GNU/Linux written in Python. Similarly utilizing Twisted, SQLAlchemy, PyCrypto and Python RSA, as well as SQLite, and likely Tkinter, or some other extremely simple GUI program. There may even be a command-line version. Eventually, we plan to expand to Mac and Windows with an eye on integration into those unique desktop environments to make sure that Hermes takes advantage of the unqiue GUI elements offered by those platforms.

### Mobile Clients:

Similar to the desktop clients, the mobile clients will be developed quickly thereafter using the same protocol. Again there will be a heavy emphasis on using native UI elements accross UI platforms to make them as untuitive to users as possible. We are also looking into using APIs/Platforms that allow us to simultaneously develop for multiple platforms as well. Hermes will hopefully also have the apparently critical element to any messaging system: Stickers!

### Web Client:

As of right now, there are no concrete plans for a web client, but we do intend to make one eventually. This will require some serious planning as far as the security aspects of our messenger go.

## Contributing:

Hermes messenger was conceived in a discussion thread of the UConn Cyber Security Club. As of right now, we would prefer to keep the development to people who are part of that club - that way we can meet in person while integrating the development of the app into club activities. Once the program is more or less functional, we will be more than happy to include other developers if anyone is interested. We have no idea what kind of format any of this will be done in. On the other hand if you are an active member of the UConn Cyber Security Club you should follow this repo, and contact one of the developers to discuss what you can contribute.

All that being said, absolutely anyone is free to modify this code and we are always open to suggestions and improvements. We would love for Hermes to be a success and, even more importantly, we want it to be as secure as possible.
