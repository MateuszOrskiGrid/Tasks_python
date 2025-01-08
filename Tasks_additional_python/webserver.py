from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import cgi

tasklist = ['Task 1', 'Task 2', 'Task 3']

class requestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith('/tasklist'):
            self.send_response(200)
            self.send_header('content-type', 'text/html')
            self.end_headers()

            output = '<html><body>'
            output += '<h1>Task List</h1>'
            output += '<h3><a href="/tasklist/new">Add New Task</a></h3>'
            for task in tasklist:
                output += f"{task} <a href='/tasklist/{urllib.parse.quote(task)}/remove'>X</a><br>"
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/new'):
            self.send_response(200)
            self.send_header('content-type', 'text/html')
            self.end_headers()

            output = '<html><body>'
            output += '<h1>Add New Task</h1>'
            output += '<form method="POST" enctype="multipart/form-data" action="/tasklist/new">'
            output += '<input name="task" type="text" placeholder="Add new task">'
            output += '<input type="submit" value="Add">'
            output += '</form>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        if self.path.endswith('/remove'):
            listIDPath = self.path.split('/')[2]
            decoded_task = urllib.parse.unquote(listIDPath)
            self.send_response(200)
            self.send_header('content-type', 'text/html')
            self.end_headers()

            output = '<html><body>'
            output += f'<h1>Remove Task: {decoded_task}</h1>'
            output += f'<form method="POST" enctype="multipart/form-data" action="/tasklist/{urllib.parse.quote(decoded_task)}/remove">'
            output += '<input type="submit" value="Remove"></form>'
            output += '<a href="/tasklist">Cancel</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

    def do_POST(self):
        if self.path.endswith('/new'):
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                new_task = fields.get('task')
                if new_task:
                    tasklist.append(new_task[0])

            self.send_response(301)
            self.send_header('Location', '/tasklist')
            self.end_headers()

        if '/remove' in self.path:
            listIDPath = self.path.split('/')[2]
            decoded_task = urllib.parse.unquote(listIDPath)
            if decoded_task in tasklist:
                tasklist.remove(decoded_task)  # Remove only if task exists
                self.send_response(301)
                self.send_header('Location', '/tasklist')
                self.end_headers()
            else:
                self.send_response(404)
                self.send_header('content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Task not found</h1></body></html>")

def main():
    PORT = 9000
    server_address = ('localhost', PORT)
    server = HTTPServer(server_address, requestHandler)
    print(f'Server running on port {PORT}')
    server.serve_forever()

if __name__ == '__main__':
    main()
