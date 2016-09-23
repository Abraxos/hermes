# Setup Notes for TLS Fork of Hermes

```
$ pip install twisted cryptography pyopenssl attr msgpack-python bcrypt
```

## Hermes Identity Server

An extremely basic server that handles username registration and fetching requests.

Sequence of Operations Tree:

1. Client establishes TLS connection without client-authentication (Note the client must already posess the CA, consider distribution with a server configuration)
  1. Client sends the server a "register" request with their username, server-password and a CSR (note that there are two passwords, one to log in and one to decrypt your private key)
    1. If the username already exists the server rejects the request and terminates the connection
    2. If the username doesn't already exist, the server registers the username to the database and returns a signed certificate based on the CSR
  2. Client sends the server a "fetch" request with a username
    1. if the username exists on the server, the server replies with that user's certificate
    2. if the username does not exist on the server, the server terminates the connection
  3. Client sends the server a "fetch my" request with a username and password
    1. if the password is valid (hash and salt), the server responds with an encrypted private key (needs to be unlocked with another password)
    2. if the password is invalid the server terminates the connection
