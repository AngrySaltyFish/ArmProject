from http.server import *
import socketserver
import ssl
import json
import sqlite3

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/jsonDataFile.json':
            with open('jsonDataFile.json', 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'json')
                self.end_headers()
                self.wfile.write(file.read())
        else:
            self.homepage()

    def do_POST(self):
        self.send_response(200)
        length = int(self.headers["content-length"])
        data = self.rfile.read(length)
        database.insertValues(data)

        self.homepage()

    def homepage(self):
        with open('index.html', 'rb') as file:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(file.read())

class CreateDatabase():
    def __init__(self):
        self.dbinit()

    def dbinit(self):
        self.conn = sqlite3.connect("database.db")
        self.c = self.conn.cursor()

        self.c.execute("""
        CREATE TABLE IF NOT EXISTS data (
            lat int(4),
            lng int(4),
            C02 int(1),
            C0 int(1)
        )
        """)

    def insertValues(self, rawData):
        #data = json.dumps(rawData)

        try:
            str = rawData.decode()
            data = json.loads(str[str.find("["):str.rfind("]")+1])

            for item in data:
                self.c.execute("""
                INSERT INTO data VALUES (
                    ?,
                    ?,
                    ?,
                    ?
                )
                """, (item["location"][0], item["location"][1], item["C02"], item["C0"]))
            self.conn.commit()

        except Exception as e:
            print(e)

if __name__ == "__main__":
    database = CreateDatabase()
    server = socketserver.TCPServer(('', 80), Handler)
    server.socket = ssl.wrap_socket (server.socket, certfile='cert.pem', keyfile='key.pem', server_side=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(' Recieved Shutting Down')
