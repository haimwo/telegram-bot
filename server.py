from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

port = int(os.getenv("PORT", 8080))

def run_server():
    server = HTTPServer(('', port), SimpleHTTPRequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    run_server()
