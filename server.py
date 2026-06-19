import json
import sqlite3
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

DATABASE = 'games.db'

def init_db():
    """Создает базу данных и таблицу, если их нет"""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                genre TEXT,
                poster TEXT,
                description TEXT
            )
        ''')
        cursor.execute("SELECT COUNT(*) FROM games")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO games (title, genre, poster, description) 
                VALUES ('The Witcher 3', 'RPG', 'https://via.placeholder.com/250x350/ff7b00/ffffff?text=Witcher+3', 'Культовая игра про Ведьмака.')
            """)
        conn.commit()

class GameRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', content_type)
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            if os.path.exists('index.html'):
                self._set_headers(200, 'text/html; charset=utf-8')
                with open('index.html', 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self._set_headers(404, 'text/plain; charset=utf-8')
                self.wfile.write("Файл index.html не найден!".encode('utf-8'))
        
        elif self.path == '/api/games':
            self._set_headers()
            with sqlite3.connect(DATABASE) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM games")
                games = [dict(row) for row in cursor.fetchall()]
            self.wfile.write(json.dumps(games).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode('utf-8'))

    def do_POST(self):
        if self.path == '/api/games':
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO games (title, genre, poster, description) VALUES (?, ?, ?, ?)",
                    (post_data['title'], post_data['genre'], post_data['poster'], post_data.get('description', ''))
                )
                conn.commit()
                new_id = cursor.lastrowid
            
            self._set_headers(201)
            self.wfile.write(json.dumps({"success": True, "id": new_id}).encode('utf-8'))

    def do_PUT(self):
        if self.path.startswith('/api/games/'):
            game_id = int(self.path.split('/')[-1])
            content_length = int(self.headers['Content-Length'])
            put_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE games SET title = ?, genre = ?, poster = ?, description = ? WHERE id = ?",
                    (put_data['title'], put_data['genre'], put_data['poster'], put_data.get('description', ''), game_id)
                )
                conn.commit()
            
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))

    # НОВЫЙ МЕТОД: Обработка запроса на удаление
    def do_DELETE(self):
        if self.path.startswith('/api/games/'):
            game_id = int(self.path.split('/')[-1])
            
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM games WHERE id = ?", (game_id,))
                conn.commit()
            
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))

def run(port=8000):
    init_db()
    server_address = ('', port)
    httpd = HTTPServer(server_address, GameRequestHandler)
    print(f"Сервер успешно запущен! Открой в браузере: http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")

if __name__ == '__main__':
    run()