#!/usr/bin/env python3
# Simple HTTP server that serves a file and then exits
import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse, parse_qs

PORT = 8000
DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

class OneTimeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
        
    def do_GET(self):
        print(f"Serving: {self.path}")
        super().do_GET()
        # Exit after serving any file
        sys.exit(0)

with socketserver.TCPServer(("", PORT), OneTimeHandler) as httpd:
    print(f"Server started at http://localhost:{PORT}")
    print(f"Serving from directory: {DIRECTORY}")
    print(f"Open http://localhost:{PORT}/basic_test.html in your browser")
    print("Server will exit after serving one request")
    httpd.serve_forever()