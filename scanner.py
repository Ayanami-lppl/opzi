"""opzi's read-only, cancellable directory index. Sizes are logical bytes."""
import os
import logging
import threading
import time
from pathlib import Path


class Scanner:
    def __init__(self):
        self.lock = threading.RLock()
        self.cancel_event = threading.Event()
        self.nodes = {}
        self.state = 'idle'
        self.errors = []
        self.skipped = 0
        self.files = 0
        self.folders = 0
        self.started = 0
        self.root = None

    def start(self, path):
        root = Path(path).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise ValueError('请选择文件夹或磁盘根目录')
        with self.lock:
            if self.state == 'scanning':
                raise ValueError('请先取消或等待当前扫描完成')
            self.nodes = {}
            self.errors = []
            self.skipped = self.files = 0
            self.folders = 0
            self.root = str(root)
            self.started = time.monotonic()
            self.finished = None
            self.cancel_event.clear()
            self.state = 'scanning'
            self._add(root, None, True)
        threading.Thread(target=self._run, daemon=True).start()
        return self.status()

    def _add(self, path, parent, directory, size=0, modified=0, hidden=False):
        key = str(path)
        if directory:
            self.folders += 1
        self.nodes[key] = dict(id=key, name=path.name or key, parent=parent,
                               directory=directory, size=size, modified=modified,
                               hidden=hidden, children=[], issues=0)
        if parent is not None:
            self.nodes[parent]['children'].append(key)
        return key

    def _run(self):
        stack = [self.root]
        try:
            while stack and not self.cancel_event.is_set():
                folder = stack.pop()
                try:
                    with os.scandir(folder) as entries:
                        for entry in entries:
                            if self.cancel_event.is_set():
                                break
                            try:
                                if entry.is_symlink() or (hasattr(os.path, 'isjunction') and os.path.isjunction(entry.path)):
                                    with self.lock:
                                        self.skipped += 1
                                    continue
                                st = entry.stat(follow_symlinks=False)
                                directory = entry.is_dir(follow_symlinks=False)
                                hidden = entry.name.startswith('.') or bool(getattr(st, 'st_file_attributes', 0) & 2)
                                with self.lock:
                                    key = self._add(Path(entry.path), folder, directory,
                                                    0 if directory else st.st_size, st.st_mtime, hidden)
                                    if not directory:
                                        self.files += 1
                                        ancestor = folder
                                        while ancestor is not None:
                                            self.nodes[ancestor]['size'] += st.st_size
                                            ancestor = self.nodes[ancestor]['parent']
                                if directory:
                                    stack.append(key)
                            except OSError as exc:
                                self._error(folder, entry.path, exc)
                except OSError as exc:
                    self._error(folder, folder, exc)
        finally:
            with self.lock:
                self.state = 'cancelled' if self.cancel_event.is_set() else 'complete'
                self.finished = time.monotonic()
                logging.info('Scan %s: %s, %d files, %d bytes', self.state, self.root, self.files, self.nodes[self.root]['size'])

    def _error(self, folder, path, exc):
        with self.lock:
            self.nodes[folder]['issues'] += 1
            if len(self.errors) < 200:
                self.errors.append(dict(path=path, message=str(exc)))

    def status(self):
        with self.lock:
            return dict(state=self.state, root=self.root, files=self.files,
                        folders=self.folders,
                        size=self.nodes[self.root]['size'] if self.root else 0,
                        skipped=self.skipped, errors=list(self.errors),
                        elapsed=round((getattr(self, 'finished', None) or time.monotonic()) - self.started, 1) if self.started else 0)

    def node(self, key):
        with self.lock:
            n = self.nodes[key]
            children = sorted((self.nodes[k] for k in n['children']), key=lambda x: (-x['size'], x['name'].casefold()))
            result = {**n, 'children': [{**c, 'children': len(c['children'])} for c in children[:500]]}
            result['total_children'] = len(children)
            result['parent_size'] = self.nodes[n['parent']]['size'] if n['parent'] else n['size']
            result['root_size'] = self.nodes[self.root]['size']
            crumbs = []
            current = n
            while current:
                crumbs.append(dict(id=current['id'], name=current['name']))
                current = self.nodes.get(current['parent'])
            result['breadcrumbs'] = crumbs[::-1]
            return result

    def search(self, query):
        with self.lock:
            hits = [n for n in self.nodes.values() if query.casefold() in n['name'].casefold()]
            return [{**n, 'children': len(n['children'])} for n in sorted(hits, key=lambda n: -n['size'])[:100]]
