import argparse
import json
import random
import threading
import time
import sys
import signal
import logging
import requests
from decimal import Decimal as dec


class Flooder:
    threads = 10
    requests = 10
    shuffle = True
    log = True
    json = False
    help = "list example:\n" \
           "  [\n" \
           "    {\n" \
           "      \"url\": \"http://localhost:8000/api/url\",\n" \
           "      \"type\": \"POST\",\n" \
           "      \"params\": [\n" \
           "        {\n" \
           "          \"name\": \"test\",\n" \
           "          \"value\": \"something\"\n" \
           "        }\n" \
           "      ]\n" \
           "    },\n" \
           "    ...\n" \
           "  ]"

    _version = "1.0"
    _threads = []
    _start = 0
    _stop = 0
    _total = 0

    def __init__(self):
        self._config()
        self.json = json.load(self.json)

        if self.log:
            logformat = '%(asctime)-26s %(threadName)-12s %(message)s'
            logging.basicConfig(filename=time.strftime("Flooder_%H-%M-%S_%d-%m-%Y.log"), format=logformat, level=logging.DEBUG)
            logging.getLogger("requests").setLevel(logging.WARNING)

        if self._validate_list():
            self._start = time.time()
            for c in range(0, self.threads):
                t = Thread(args=(self.json, self.requests, self.shuffle, self.log,))
                self._threads.append(t)
                t.start()

            wait = True
            while wait:
                wait = False
                time.sleep(0.1)
                for t in self._threads:
                    if t.isAlive():
                        wait = True

            self._stop = time.time()
            self._total = self._stop - self._start
            self._report()
        return

    def _config(self):
        parser = argparse.ArgumentParser(prog="Flooder", description="HTTP flooding tool " + self._version,
                                         epilog=self.help, formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + self._version)
        parser.add_argument('-j', '--json', required=True, type=argparse.FileType('r'), help='requests list (required, json)')
        parser.add_argument('-t', '--threads', default=10, type=int, help='number of parallel threads to use (default: 10)')
        parser.add_argument('-r', '--requests', default=10, type=int, help='number of requests / thread (default: 10)')
        parser.add_argument('-ns', '--no-shuffle', default=False, action='store_true', help='disable shuffling of requests list')
        parser.add_argument('-nl', '--no-log', default=False, action='store_true', help='disable logging to file')

        args = parser.parse_args()
        self.json = args.json
        self.threads = args.threads
        self.requests = args.requests
        if args.no_shuffle:
            self.shuffle = False
        if args.no_log:
            self.log = False
        return

    def _validate_list(self):
        try:
            if type(self.json) is not list:
                raise Exception("List is not a list")

            if len(self.json) == 0:
                raise Exception("List is empty")

            i = 0
            for r in self.json:
                if type(r) is not dict:
                    raise Exception("List entry [" + str(i) + "] is not a dict")

                if 'url' not in r:
                    raise Exception("List entry [" + str(i) + "] has no 'url' property")

                if type(r['url']) not in [str, unicode]:
                    raise Exception("List entry [" + str(i) + "] 'url' property is not a string")

                if 'type' not in r:
                    raise Exception("List entry [" + str(i) + "] has no 'type' property")

                if type(r['type']) not in [str, unicode]:
                    raise Exception("List entry [" + str(i) + "] 'type' property is not a string")

                if r['type'].lower() not in ['get', 'post', 'put', 'delete']:
                    raise Exception("List entry [" + str(i) + "] 'type' property should be: get, post, put, delete")

                if 'params' in r:
                    if type(r['params']) is not list:
                        raise Exception("List entry [" + str(i) + "] 'params' property is not a list")

                    j = 0
                    for e in r['params']:
                        if type(e) is not dict:
                            raise Exception("List entry [" + str(i) + "] 'params' entry [" + str(j) + "] is not a dict")

                        if 'name' not in e:
                            raise Exception("List entry [" + str(i) + "] 'params' entry  [" + str(j) + "]has no 'name' property")

                        if type(e['name']) not in [str, unicode]:
                            raise Exception("List entry [" + str(i) + "] 'params' entry [" + str(j) + "] 'name' property is not a string")

                        if 'value' not in e:
                            raise Exception("List entry [" + str(i) + "] 'params' entry [" + str(j) + "] has no 'value' property")

                        if type(e['value']) not in [str, unicode]:
                            raise Exception("List entry [" + str(i) + "] 'params' entry [" + str(j) + "] 'value' property is not a string")
                        j += 1
                i += 1
            return True
        except Exception as e:
            print e.args[0]
            return False

    def _report(self):
        requests_total = 0
        requests_successful = 0
        requests_failed = 0
        requests_not = 0

        time_total = 0
        time_successful = 0
        time_failed = 0

        successful_average = 0
        successful_fastest = 0
        successful_slowest = 0

        for t in self._threads:
            requests_total += len(t.results)
            for r in t.results:
                time_total += r['time']

                if r['status'] == 200:
                    requests_successful += 1
                    time_successful += r['time']

                    if successful_fastest == 0:
                        successful_fastest = r['time']

                    if successful_fastest > r['time']:
                        successful_fastest = r['time']

                    if successful_slowest < r['time']:
                        successful_slowest = r['time']
                elif r['status'] > 0:
                    requests_failed += 1
                    time_failed += r['time']

        requests_not = requests_total - requests_successful - requests_failed
        successful_average = time_successful / (self.requests * self.threads)

        if self.log:
            logging.info("Threads:" + str(self.threads))
            logging.info("Requests:" + str(self.requests))
            logging.info("Execution time:" + str(self._total))

            logging.info("Requests total: " + str(requests_total))
            logging.info("Requests successful: " + str(requests_successful))
            logging.info("Requests failed: " + str(requests_failed))
            logging.info("Requests not: " + str(requests_not))

            logging.info("Successful fastest: " + str(successful_fastest))
            logging.info("Successful slowest: " + str(successful_slowest))
            logging.info("Successful average: " + str(successful_average))

            logging.info("Time total: " + str(time_total))
            logging.info("Time successful: " + str(time_successful))
            logging.info("Time failed: " + str(time_failed))

        print "Threads:", self.threads
        print "Requests:", self.requests
        print "Execution time:", self._total

        print "Requests total:", requests_total
        print "Requests successful:", requests_successful
        print "Requests failed:", requests_failed
        print "Requests not:", requests_not

        print "Successful fastest", successful_fastest
        print "Successful slowest", successful_slowest
        print "Successful average", successful_average

        print "Time total:", time_total
        print "Time successful:", time_successful
        print "Time failed:", time_failed
        return


class Thread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, verbose=None, args=()):
        threading.Thread.__init__(self, group=group, target=target, name=name, verbose=verbose)
        self._list = args[0]
        self._requests = args[1]
        self._shuffle = args[2]
        self._log = args[3]
        self.results = []

        if self._shuffle:
            random.shuffle(self._list)
        return

    def run(self):
        i = 0
        while i < self._requests:
            for e in self._list:
                payload = {}
                for p in e['params']:
                    payload.update({p['name']: p['value']})

                try:
                    if e['type'] == "get":
                        req = requests.get(e['url'])
                    elif e['type'] == "delete":
                        req = requests.delete(e['url'])
                    elif e['type'] == "put":
                        req = requests.put(e['url'], data=payload)
                    else:
                        req = requests.post(e['url'], data=payload)
                    res = {'url': e['url'], 'data': payload, 'status': req.status_code, 'content': req.text, 'time': (dec(req.elapsed.microseconds) / 1000 / 1000)}
                except Exception:
                    res = {'url': e['url'], 'data': payload, 'status': 0, 'content': '', 'time': dec(0)}

                if self._log:
                    logging.debug(res)
                self.results.append(res)
                i += 1
                if i == self._requests:
                    return
        return


def catch_interrupt():
    print ""
    sys.exit(0)
signal.signal(signal.SIGINT, catch_interrupt)


if __name__ == '__main__':
    Flooder()
