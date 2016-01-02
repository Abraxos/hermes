# Session-Level Protocol Summary - Hermes

Session-level communication in Hermes takes place over an encrypted channel that uses a symmetric AES256 cipher secured with a key that is generated once a client has confirmed their identity. A session is a series of messages exclusively between the client and server devices which take the form of function calls by the client to the server and vice versa. Please note that a session can exist between a client device and a server without that device being logged in (associated with a specific user account).

## Session Message Format

The general format of a session-level message is that they must begin with an all-capital-letter command (the list of which is specified below), followed by a set of specified parameters, and the final component of the message is typically the large payload, whatever that may be for the type of message, assuming that one is specified. All of these elements: the command, the parameters, and the payload are sparated by colons `:`. The reason for putting the payload last is that if it contains colons of its own, they would not interfere with the interpretation of the message as each command has a specified number of parameters and therefore each command inherently indicates the number of colons that ought to follow it, and all other colons are part of the payload.

```
COMMAND:PARAM1:PARAM2:PARAM3:Payload
```

Aside from simple commands, there are also several special commands, like the `LOGIN` command for example, that enter the session into a special state. Once entered, the command must be resolved by a series of sequential messages conforming to the protocol specification. The login command, for example, requires the server to challenge the client to prove their identity. During this exchange, all other session-level messages will be ignored and should be queued up by the client/server for delivery afterwards.

## Session-Message Command Specifications

### Login

```
LOGIN:<user public key>
```

The login command does not have any parameters other than the payload and can therefore be interpreted by splitting on the `:` one time.

The login command is special. Once a login command is sent, the session enters into a series of login states. For a high-level explanation for the reason behind this, please check out the High-Level Hermes Protocol Security Scheme document. The server responds with a message: `LOGIN_CHALLENGE:<challenge>` and the user must sign the challenge with their user private key (as opposed to the device private key that was used to establish the session). The client signs the challenge and sends a message of the format: `LOGIN_RESPONSE:<challenge signature>`. Assuming that the client's signature is valid, the server then replies with a `LOGIN_CHALLENGE_ACK` followed by the client sending a `LOGIN_USERNAME:<username>` message. If the username is valid, the server replies with `LOGIN_USERNAME_ACCEPT`, otherwise `LOGIN_USERNAME_REJECT`.

The following is an example login session between the server and client:

TODO: Write code that would generate such a valid conversation and then paste it here.
```

```

### Start Conversation

Starting a conversation with another user is a command that begins an exchange between two users, however, unlike the login command, other messages can be sent between the client and server. There are several commands that comprise starting a conversation and they must be sequential for a specific conversation. The critical element of starting a conversation is that it may come from either the client or the server as the server relays messages from one user to another. Therefore, all messages for starting a conversation are associated with either client A, the server, or client B where client A is the client initializing a conversation with client B. The server relays messages, and whenever there is a parameter that indicates a destination value, it is changed to represent the source before being delivered. At the end of this exchange, two users are supposed to generate a key to be used for symmatric encryption without the server ever knowing this key.

#### Start Conversation

##### Client A to Server:

```
START_CONVERSATION:<client B public key>
```

##### Server to Client B:

```
START_CONVERSATION:<client A public key>
```

#### Challenge User

##### Client B to Server:

```
START_CONVERSATION_CHALLENGE:<client A public key>:<challenge signature (by client B)>:<challenge>
```

##### Server to Client A:

```
START_CONVERSATION_CHALLENGE:<client B public key>:<challenge signature (by client B)>:<challenge>
```

#### Respond to Challenge

##### Client A to Server

```
START_CONVERSATION_RESPONSE:<client B public key>:<challenge signature (by client A)>:<key signature (with A's private key) and key encrypted with B's public key>
```

##### Server to Client B

```
START_CONVERSATION_RESPONSE:<client A public key>:<challenge signature (by client A)>:<conversation id>:<key signature (with A's private key) and key encrypted with B's public key>
```

### Converse

```
CONVERSE:<conversation id>:
```