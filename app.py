"""Launch opzi with Python; no network service or cloud account required."""
import argparse
import json
import logging
import os
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from scanner import Scanner

BASE = Path(__file__).parent
scanner = Scanner()
TOKEN = secrets.token_urlsafe(32)
window = None
APP_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else BASE


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, data, code=200, content_type='application/json; charset=utf-8'):
        body = json.dumps(data, ensure_ascii=False).encode() if not isinstance(data, bytes) else data
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        return self.headers.get('X-Opzi-Token') == TOKEN

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == '/':
            html = (BASE / 'ui/index.html').read_text(encoding='utf-8').replace('__TOKEN__', TOKEN)
            return self.respond(html.encode(), content_type='text/html; charset=utf-8')
        if url.path in ['/style.css', '/app.js']:
            kind = 'text/css' if url.path.endswith('css') else 'text/javascript'
            return self.respond((BASE / 'ui' / url.path[1:]).read_bytes(), content_type=kind + '; charset=utf-8')
        if not self.authorized():
            return self.respond({'error': '访问被拒绝'}, 403)
        args = parse_qs(url.query)
        try:
            if url.path == '/api/status':
                return self.respond(scanner.status())
            if url.path == '/api/node':
                return self.respond(scanner.node(args['id'][0]))
            if url.path == '/api/search':
                return self.respond(scanner.search(args.get('q', [''])[0]))
            return self.respond({'error': '未找到'}, 404)
        except (KeyError, ValueError) as exc:
            self.respond({'error': str(exc)}, 400)

    def do_POST(self):
        if not self.authorized():
            return self.respond({'error': '访问被拒绝'}, 403)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length > 16384:
                return self.respond({'error': '请求过大'}, 413)
            data = json.loads(self.rfile.read(length) or '{}')
            if self.path == '/api/scan':
                return self.respond(scanner.start(data['path']))
            if self.path == '/api/cancel':
                scanner.cancel_event.set()
                return self.respond({'ok': True})
            if self.path == '/api/open':
                with scanner.lock:
                    node = scanner.nodes[data['id']]
                    target = node['id'] if node['directory'] else node['parent']
                os.startfile(target)
                return self.respond({'ok': True})
            return self.respond({'error': '未找到'}, 404)
        except (OSError, ValueError, KeyError) as exc:
            self.respond({'error': str(exc)}, 400)


class Bridge:
    def choose_folder(self):
        import webview
        result = window.create_file_dialog(webview.FileDialog.FOLDER)
        return result[0] if result else None


def main():
    global window
    parser = argparse.ArgumentParser(description='opzi · 看见空间的脉络')
    parser.add_argument('--browser', action='store_true', help='在浏览器中打开')
    parser.add_argument('--root', help='启动时扫描的目录')
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    url = f'http://127.0.0.1:{server.server_port}'
    logging.info('opzi service: %s', url)
    if args.root:
        scanner.start(args.root)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f'opzi: {url}', flush=True)
    try:
        if not args.browser:
            try:
                import webview
                window = webview.create_window('opzi · 磁盘空间关系图', url, js_api=Bridge(), width=1440, height=900, min_size=(1080, 680), background_color='#111518')
                window.events.shown += lambda: logging.info('Desktop window shown')
                window.events.loaded += lambda: logging.info('Desktop content loaded')
                webview.start(gui='edgechromium', storage_path=str(APP_DIR / 'data'))
                return
            except Exception as exc:
                logging.exception('Native window failed')
                if getattr(sys, 'frozen', False):
                    import ctypes
                    ctypes.windll.user32.MessageBoxW(None, f'独立窗口启动失败：{exc}\n请查看软件目录中的 opzi.log。', 'opzi', 16)
                    return
                print(f'桌面窗口不可用，改用浏览器：{exc}', flush=True)
        webbrowser.open(url)
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        logging.info('Stopping opzi service')
        scanner.cancel_event.set()
        server.shutdown()


if __name__ == '__main__':
    logging.basicConfig(filename=APP_DIR / 'opzi.log', level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s', encoding='utf-8')
    main()
