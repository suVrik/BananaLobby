from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import sys
import re

LobbyLifetime = 20
LobbyList = {}

SecretRegexp = re.compile(r'^[A-Za-z0-9]+$')
AddressRegexp = re.compile(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$')

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/GetLobbies':
            self.GetLobbies()
        elif self.path == '/CreateLobby':
            self.CreateLobby()
        elif self.path == '/DestroyLobby':
            self.DestroyLobby()
        else:
            self.InvalidRequest()

    def GetLobbies(self):
        print('Get lobbies requrest', flush = True)

        self.SuccessHeader()
        self.CleanUpLobbies()

        for Secret, Value in LobbyList.items():
            self.wfile.write(f'{Value["Name"]},{Value["Address"]}\n'.encode('utf-8'))

    def CreateLobby(self):
        print('Create lobby requrest', flush = True)

        ContentLength = int(self.headers['Content-Length'])
        if ContentLength < 256:
            DataItems = self.rfile.read(ContentLength).decode('utf-8').split(',')
            if len(DataItems) == 3:
                Secret = DataItems[0]
                Name = DataItems[1]
                Address = DataItems[2]
                if re.fullmatch(SecretRegexp, Secret):
                    if re.fullmatch(AddressRegexp, Address):
                        LobbyList[Secret] = {
                            'Name': Name,
                            'Address': Address,
                            'LastUpdateTime': time.time()
                        }
                        print(f'Successful create lobby requrest: "{Secret}" "{Name}" "{Address}"', flush = True)
                        self.SuccessHeader()
                    else:
                        print(f'Invalid address {Address} in create lobby request', flush = True)
                        self.ErrorHeader()
                else:
                    print(f'Invalid secret {Secret} in create lobby request', flush = True)
                    self.ErrorHeader()
            else:
                print(f'Expected 3 items in create lobby request, got {len(DataItems)}', flush = True)
                self.ErrorHeader()
        else:
            print(f'Create lobby request is too long: {ContentLength} symbols', flush = True)
            self.ErrorHeader()

        self.CleanUpLobbies()

    def DestroyLobby(self):
        print('Destroy lobby requrest', flush = True)

        ContentLength = int(self.headers['Content-Length'])
        if ContentLength < 256:
            Secret = self.rfile.read(ContentLength).decode('utf-8')
            if re.fullmatch(SecretRegexp, Secret):
                if Secret in LobbyList:
                    del LobbyList[Secret]
                    print(f'Successful destroy lobby requrest: "{Secret}"', flush = True)
                    self.SuccessHeader()
                else:
                    print(f'Lobby with secret {Secret} is not in the lobby list', flush = True)
                    self.ErrorHeader()
            else:
                print(f'Invalid secret {Secret} in destroy lobby request', flush = True)
                self.ErrorHeader()
        else:
            print(f'Destroy lobby request is too long: {ContentLength} symbols', flush = True)
            self.ErrorHeader()

        self.CleanUpLobbies()

    def InvalidRequest(self):
        print('Invalid request', flush = True)

        self.ErrorHeader()
        self.CleanUpLobbies()

    def CleanUpLobbies(self):
        CurrentTime = time.time()

        for Secret, Value in list(LobbyList.items()):
            if CurrentTime - Value['LastUpdateTime'] > LobbyLifetime:
                print(f'Lobby with secret {Secret} timed out', flush = True)
                del LobbyList[Secret]

    def ErrorHeader(self):
        self.send_response(502)
        self.send_header('Content-type', 'text/csv')
        self.end_headers()

    def SuccessHeader(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/csv')
        self.end_headers()

if __name__ == '__main__':
    print('Initializing lobby server', flush = True)

    Server = HTTPServer(('', 80), RequestHandler)
    try:
        Server.serve_forever()
    except KeyboardInterrupt:
        pass
    Server.server_close()

    print('Shutting down lobby server', flush = True)
