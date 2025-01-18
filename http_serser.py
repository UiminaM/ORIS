from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

PORT = 8000

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open('index.html', 'rb') as f:
                self.wfile.write(f.read())
        elif self.path == '/about':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            response = '<h1>0 нac</h1>'
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        parsed_data = parse_qs(post_data.decode('utf-8'))

        response = ""
        for key, value in parsed_data.items():
            response += f"{key}: {', '.join(value)}<br>"

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

if __name__ == "__main__":
    httpd = HTTPServer(("", PORT), MyHandler)
    print(f"Сервер запущен на порту {PORT}")
    httpd.serve_forever()