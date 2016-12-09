"""Launcher for the Hermes Identity Server"""
from __future__ import print_function
from argparse import ArgumentParser

from hermes.server.identity.identity import run_identity_server

def main():
    '''Main function, parses arguments, handles bad ones, and launches the server process'''
    parser = ArgumentParser(prog='Hermes Identity Server',
                            description='Allows clients to register accounts, \
                                         get certificates, download their \
                                         information, and fetch the public \
                                         certificates of others.')
    parser.add_argument('-p', '--port', type=int, help='Port to listen on')
    parser.add_argument('-k', '--key-file', help='Path to server private key')
    parser.add_argument('-c', '--cert-file', help='Path to server certificate')
    parser.add_argument('-a', '--cert-auth', help='Path to server authority \
                                                   certificate')
    args = parser.parse_args()
    if not args.port:
        print('Port argument required')
        parser.print_help()
    elif not args.key_file:
        print('Server key file required')
        parser.print_help()
    elif not args.cert_file:
        print('Server certificate file required')
        parser.print_help()
    elif not args.cert_auth:
        print('Certificate authority file required')
        parser.print_help()
    else:
        run_identity_server(args.port,
                            args.key_file,
                            args.cert_file,
                            args.cert_auth)
    exit(int(any([args.port, args.key_file, args.cert_file, args.cert_auth])))

if __name__ == "__main__":
    main()
