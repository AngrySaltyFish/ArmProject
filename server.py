from http.server import *
import socketserver
import ssl
import json
import sqlite3


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/datafromDB":
            self.wfile.write(database.getValues())

        elif len(self.path) > 1:
            with open(self.path[1:], "rb") as file:
                self.send_response(200)
                if "js" in self.path:
                    self.send_header("Content-type", "text/javascript")
                else:
                    self.send_header("Content-type", "text/css")
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
        with open("index.html", "rb") as file:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
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
        try:
            str = rawData.decode()
            data = json.loads(str[str.find("["):str.rfind("]") + 1])

            for item in data:
                self.c.execute("""
                INSERT INTO data VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )
                """, (item["location"][0],
                      item["location"][1],
                      item["C02"],
                      item["C0"]))
            self.conn.commit()

            self.c.execute("SELECT * FROM data")
            data = self.c.fetchall()
            for dataItem in range(len(data)):
                self.c.execute("SELECT * FROM data WHERE lat=%s AND lng=%s" % (data[dataItem][0], data[dataItem][1]))
                duplicates = self.c.fetchall()
                if len(duplicates) > 0:
                    self.c.execute("UPDATE data SET C0 = ? WHERE lat = ? AND lng = ?", (
                        (data[dataItem][2] / len(duplicates),
                         data[dataItem][0],
                         data[dataItem][1]
                    )))
                    self.c.execute("UPDATE data SET C02 = ? WHERE lat = ? AND lng = ?", (
                        (data[dataItem][2] / len(duplicates),
                         data[dataItem][0],
                         data[dataItem][1]
                    )))

        except Exception as e:
            print(e)

    def getValues(self):
        self.c.execute("SELECT * FROM data")
        return str(self.c.fetchall()).encode()


if __name__ == "__main__":
    database = CreateDatabase()
    server = socketserver.TCPServer(("", 80), Handler)
    server.socket = ssl.wrap_socket(
        server.socket,
        certfile="cert.pem",
        keyfile="key.pem",
        server_side=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(" Recieved Shutting Down")
