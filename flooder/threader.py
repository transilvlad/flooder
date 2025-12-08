import logging
import os
import random
import threading
import time
from decimal import Decimal

import requests


class FloodThread(threading.Thread):
    def __init__(self, request_list, requests_per_thread, shuffle, log, timeout):
        super().__init__()
        self._list = list(request_list)
        self._requests = requests_per_thread
        self._shuffle = shuffle
        self._log = log
        self._timeout = timeout
        self.results = []
        self.errors = []
        self.count = 0
        if self._shuffle:
            random.shuffle(self._list)

    def run(self):
        i = 0
        while i < self._requests:
            for e in self._list:
                self.count += 1
                payload = {p['name']: p['value'] for p in e.get('params', [])}
                files = {}
                for f in e.get('files', []):
                    path, name = os.path.split(f['value'])
                    try:
                        files[f['name']] = (name, open(f['value'], 'rb'))
                    except IOError:
                        if self._log:
                            logging.error(f"Unable to read file: {f['value']}")
                microseconds = int(time.time() * 1000)
                req = None
                try:
                    method = e['type'].lower()
                    if method == "get":
                        req = requests.get(e['url'], timeout=self._timeout)
                    elif method == "delete":
                        req = requests.delete(e['url'], timeout=self._timeout)
                    elif method == "put":
                        req = requests.put(e['url'], data=payload, files=files, timeout=self._timeout)
                    elif method == "head":
                        req = requests.head(e['url'], timeout=self._timeout)
                    elif method == "options":
                        req = requests.options(e['url'], timeout=self._timeout)
                    else:
                        req = requests.post(e['url'], data=payload, files=files, timeout=self._timeout)
                    res = {'url': e['url'], 'data': payload, 'status': req.status_code,
                           'time': (Decimal(req.elapsed.microseconds) / 1000 / 1000), 'content': req.text}
                    if self._log:
                        logging.debug(res)
                except Exception as ex:
                    elapsed = Decimal(str(int(time.time() * 1000) - microseconds)) / 1000
                    if req is not None and hasattr(req, 'elapsed'):
                        elapsed = Decimal(req.elapsed.microseconds) / 1000 / 1000
                    res = {'url': e['url'], 'data': payload, 'status': 0, 'time': elapsed, 'error': str(ex)}
                    if self._log:
                        logging.error(res)
                self.results.append(res)
                i += 1
                if i == self._requests:
                    return
