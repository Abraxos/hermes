from twisted.internet import reactor
from twisted.internet.stdio import StandardIO
from twisted.protocols import basic
from twisted.web import client

from hermes.client.hermes_identity_client import HermesIdentityClientFactory

class CommandProtocol(basic.LineReceiver):
    delimiter = '\n' # unix terminal style newlines. remove this line
                     # for use with Telnet

    def __init__(self, id_factory):
        self.id_factory = id_factory

    def connectionMade(self):
        self.sendLine("Hermes simple client console. Type 'help' for help.")

    def lineReceived(self, line):
        if not line: return

        # if there is a connection, get the protocol object
        if not self.id_factory.protocols:
            self.sendLine("No connection to id server...")
            return
        else:
            id_protocol = self.id_factory[0]

        # Parse the command
        command_parts = line.split()
        cmd = command_parts[0].lower()
        args = command_parts[1:]

        if cmd is "fetch":
            self.do_fetch(id_protocol, args[0])
        elif cmd is "fetchmy":
            pass
        elif cmd is "register":
            pass
        elif cmd is "quit":
            self.do_quit()
        elif cmd is "help":
            self.do_help()
        else:
            self.sendLine("Unknown command...")
            self.print_help()
        # try:
        #     method = getattr(self, 'do_' + command)
        # except AttributeError as e:
        #     self.sendLine('Error: no such command.')
        # else:
        #     try:
        #         method(*args)
        #     except Exception as e:
        #         self.sendLine('Error: ' + str(e))

    def do_fetch(self, id_protocol, username):
        def fetch_success(cert):
            self.sendLine("Fetched certificate for: " + username)
            self.sendLine(cert)
        fetch_success(id_protocol.fetch(username))

    def do_fetch_my(self, id_protocol, username, acct_password):
        pass

    def register(self, id_protocol, username, acct_password, key, key_password):
        pass

    def print_help(self):
        self.sendLine("The following commands are accepted: fetch fetchmy register quit help")

    def do_help(self, command=None):
        """help [command]: List commands, or show help on the given command"""
        if command:
            if command is "fetch":
                self.sendLine("Retrieves the public key information for a given username")
                self.sendLine("\tfetch <username>")
            elif command is "fetchmy":
                self.sendLine("Retrieves your (encrypted) private key information")
                self.sendLine("\tfetchmy <account password>")
            elif command is "register":
                self.sendLine("Registers a new account on the server")
                self.sendLine("\tregister <username> <account password>")
            elif command is "quit":
                self.sendLine("Quits the client")
                self.sendLine("\tquit")
            else:
                self.print_help()
        else:
            self.print_help()

    def do_quit(self):
        """quit: Quit this session"""
        self.sendLine('Goodbye.')
        self.transport.loseConnection()

    # def do_check(self, url):
    #     """check <url>: Attempt to download the given web page"""
    #     client.getPage(url).addCallback(
    #         self.__checkSuccess).addErrback(
    #         self.__checkFailure)
    #
    # def __checkSuccess(self, pageData):
    #     self.sendLine("Success: got %i bytes." % len(pageData))
    #
    # def __checkFailure(self, failure):
    #     self.sendLine("Failure: " + failure.getErrorMessage())

    def connectionLost(self, reason):
        reactor.stop()

def main():
    f = HermesIdentityClientFactory()
    cmd_protocol = CommandProtocol(f)
    StandardIO(cmd_protocol)
    # TODO: Get SSL working here
    reactor.connectTCP("localhost", 8000, f)
    reactor.run()

if __name__ == "__main__":
    main()
