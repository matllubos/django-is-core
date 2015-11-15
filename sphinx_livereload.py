import livereload
from livereload import Server, shell

server = Server()
server.watch('docs/*.rst', shell('make html', cwd='docs'))
server.serve(root='docs/.build/html')
