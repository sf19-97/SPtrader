#!/usr/bin/env python3
"""
Simple CORS proxy for QuestDB
Allows the chart to connect to QuestDB without CORS issues
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import json
from urllib.parse import urlparse, parse_qs

class CORSProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Enable CORS
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        # Parse the URL
        parsed = urlparse(self.path)
        
        if parsed.path == '/exec':
            # Get query parameters
            params = parse_qs(parsed.query)
            
            if 'query' in params:
                sql_query = params['query'][0]
                
                try:
                    # Forward request to QuestDB
                    response = requests.get(
                        'http://localhost:9000/exec',
                        params={'query': sql_query},
                        timeout=10
                    )
                    
                    # Return QuestDB response
                    self.wfile.write(response.content)
                    
                except requests.RequestException as e:
                    # Return error response
                    error_response = {
                        'error': f'Failed to connect to QuestDB: {str(e)}',
                        'dataset': []
                    }
                    self.wfile.write(json.dumps(error_response).encode())
            else:
                # Return error for missing query
                error_response = {
                    'error': 'Missing query parameter',
                    'dataset': []
                }
                self.wfile.write(json.dumps(error_response).encode())
        else:
            # Return 404 for other paths
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        # Custom logging
        print(f"[PROXY] {format % args}")

def main():
    print("=== QuestDB CORS Proxy ===")
    print("Starting proxy server on http://localhost:8081")
    print("Forwarding requests to QuestDB on localhost:9000")
    print("Update your chart QuestDB URL to: http://localhost:8081")
    print("Press Ctrl+C to stop")
    
    server = HTTPServer(('localhost', 8081), CORSProxyHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping proxy server...")
        server.shutdown()

if __name__ == '__main__':
    main()
