#!/usr/bin/python
import argparse
import json
import random
import threading
import time
import os
import sys
import signal
import logging
import requests
import commands
from decimal import Decimal as dec


class Flooder:
    threads = 10
    requests = 10
    pid = 0
    cpu = []
    mem = []
    shuffle = True
    log = True
    json = False
    help = "supported methods: GET, POST, PUT, DELETE\n" \
           "\n" \
           "config example:\n" \
           "  [\n" \
           "    {\n" \
           "      \"url\": \"http://localhost:8000/api/url\",\n" \
           "      \"type\": \"POST\",\n" \
           "      \"params\": [\n" \
           "        {\n" \
           "          \"name\": \"monkey\",\n" \
           "          \"value\": \"nuts\"\n" \
           "        },\n" \
           "        ...\n" \
           "      ],\n" \
           "      \"files\": [\n" \
           "        {\n" \
           "          \"name\": \"weasel\",\n" \
           "          \"value\": \"/users/dragon/archive.zip\"\n" \
           "        },\n" \
           "        ...\n" \
           "      ]\n" \
           "    },\n" \
           "    ...\n" \
           "  ]\n"

    _version = "1.02"
    _start = 0
    _stop = 0
    _total = 0

    thread_list = []

    def __init__(self):
        self._config()
        self.json = json.load(self.json)

        if self.log:
            logformat = '%(asctime)-26s %(threadName)-12s %(message)s'
            logging.basicConfig(filename=time.strftime("Flooder_%d-%m-%Y_%H-%M-%S.log"), format=logformat, level=logging.DEBUG)
            logging.getLogger("requests").setLevel(logging.WARNING)

        if self._validate_list():
            self._start = time.time()

            print "[" + format_seconds(int(time.time())) + "] Flood gates opening.."
            for c in range(0, self.threads):
                t = Thread(args=(self.json, self.requests, self.shuffle, self.log,))
                self.thread_list.append(t)
                t.daemon = False
                t.start()

            print "[" + format_seconds(int(time.time())) + "] Flood gates open."

            print "[" + format_seconds(int(time.time())) + "] Flooding with " + str(self.requests * self.threads) + " requests via " + str(self.threads) + " threads (" + str(self.requests) + " per thread)"

            if self.pid > 0 and check_pid(self.pid):
                print "[" + format_seconds(int(time.time())) + "] Monitoring PID " + str(self.pid)
            else:
                self.pid = 0

            if self.pid > 0:
                time.sleep(0.2)
                usage = get_cpumem(self.pid)
                self.cpu.append(usage[0])
                self.mem.append(usage[1])

            wait = True
            loop = 0
            while wait:
                wait = False
                time.sleep(0.1)
                loop += 1

                if loop == 300:
                    total = 0
                    for t in self.thread_list:
                        total += t.count

                    if self.pid > 0:
                        usage = get_cpumem(self.pid)
                        self.cpu.append(usage[0])
                        self.mem.append(usage[1])
                        print "[" + format_seconds(int(time.time())) + "] PID " + str(self.pid) + " usage: CPU: " + str(usage[0]) + "%   MEM: " + str(usage[1]) + "M"

                    print "[" + format_seconds(int(time.time())) + "] Progress: " + str(total) + " requests of " + str(self.threads * self.requests)
                    loop = 0

                for t in self.thread_list:
                    if t.isAlive():
                        wait = True

            if self.pid > 0:
                usage = get_cpumem(self.pid)
                self.cpu.append(usage[0])
                self.mem.append(usage[1])

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
        parser.add_argument('-p', '--pid', type=int, help='PID for usage monitoring (handy when flooding local services)')
        parser.add_argument('-ns', '--no-shuffle', default=False, action='store_true', help='disable shuffling of requests list')
        parser.add_argument('-nl', '--no-log', default=False, action='store_true', help='disable logging to file')

        args = parser.parse_args()
        self.json = args.json
        self.threads = args.threads
        self.requests = args.requests
        self.pid = args.pid
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
        self.requests_total = 0
        self.requests_successful = 0
        self.requests_error = 0
        self.requests_failed = 0

        self.time_total = 0
        self.time_successful = 0
        self.time_error = 0
        self.time_failed = 0

        self.successful_average = 0
        self.successful_fastest = 0
        self.successful_slowest = 0

        self.error_average = 0
        self.error_fastest = 0
        self.error_slowest = 0

        self.failed_average = 0
        self.failed_fastest = 0
        self.failed_slowest = 0

        self.cpu_sum = 0
        self.cpu_average = 0
        self.cpu_ceil = 0
        self.cpu_floor = 0

        self.mem_sum = 0
        self.mem_average = 0
        self.mem_ceil = 0
        self.mem_floor = 0

        self.errors = []

        for t in self.thread_list:
            self.requests_total += len(t.results)
            for r in t.results:
                self.time_total += r['time']

                if r['status'] == 200:
                    self.requests_successful += 1
                    self.time_successful += r['time']

                    if self.successful_fastest == 0:
                        self.successful_fastest = r['time']

                    if self.successful_fastest > r['time']:
                        self.successful_fastest = r['time']

                    if self.successful_slowest < r['time']:
                        self.successful_slowest = r['time']

                elif r['status'] > 0:
                    self.requests_error += 1
                    self.time_error += r['time']

                    if self.error_fastest == 0:
                        self.error_fastest = r['time']

                    if self.error_fastest > r['time']:
                        self.error_fastest = r['time']

                    if self.error_slowest < r['time']:
                        self.error_slowest = r['time']

                elif r['status'] == 0:
                    self.requests_failed += 1
                    self.time_failed += r['time']

                    if self.failed_fastest == 0:
                        self.failed_fastest = r['time']

                    if self.failed_fastest > r['time']:
                        self.failed_fastest = r['time']

                    if self.failed_slowest < r['time']:
                        self.failed_slowest = r['time']

            for error in t.errors:
                if error not in self.errors:
                    self.errors.append(error)

        if self.pid > 0:
            for p in self.cpu:
                self.cpu_sum += p

                if self.cpu_floor == 0:
                    self.cpu_floor = p

                if self.cpu_floor > p:
                    self.cpu_floor = p

                if self.cpu_ceil < p:
                    self.cpu_ceil = p

            for v in self.mem:
                self.mem_sum += dec(v)

                if self.mem_floor == 0:
                    self.mem_floor = v

                if self.mem_floor > v:
                    self.mem_floor = v

                if self.mem_ceil < v:
                    self.mem_ceil = v

            self.cpu_ceil = round(self.cpu_ceil, 1)
            self.cpu_floor = round(self.cpu_floor, 1)
            self.cpu_average = round(self.cpu_sum / len(self.cpu), 1)

            self.mem_ceil = round(self.mem_ceil, 1)
            self.mem_floor = round(self.mem_floor, 1)
            self.mem_average = round(self.mem_sum / len(self.mem), 1)

        self.successful_fastest = '%.06f' % float(self.successful_fastest)
        self.successful_slowest = '%.06f' % float(self.successful_slowest)
        self.successful_average = '%.06f' % float(self.time_successful / (self.requests_successful * self.threads))

        if self.requests_error > 0:
            self.error_fastest = '%.06f' % float(self.error_fastest)
            self.error_slowest = '%.06f' % float(self.error_slowest)
            self.error_average = '%.06f' % float(self.time_error / (self.requests_error * self.threads))

        if self.requests_failed > 0:
            self.failed_fastest = '%.06f' % float(self.failed_fastest)
            self.failed_slowest = '%.06f' % float(self.failed_slowest)
            self.failed_average = '%.06f' % float(self.time_failed / (self.requests_failed * self.threads))

        self._out()
        return

    def _out(self):
        sep = "-" * 35
        out = []
        out.append(sep)
        out.append("Threads:              " + str(self.threads).rjust(13))
        out.append("Requests:             " + str(self.requests).rjust(13))
        out.append(sep)
        out.append("Requests total:       " + str(self.requests_total).rjust(13))
        out.append("Requests successful:  " + str(self.requests_successful).rjust(13))
        if self.requests_error > 0:
            out.append("Requests error:       " + str(self.requests_error).rjust(13))
        if self.requests_failed > 0:
            out.append("Requests failed:      " + str(self.requests_failed).rjust(13))
        out.append(sep)
        out.append("Successful fastest:   " + str(self.successful_fastest).rjust(13))
        out.append("Successful slowest:   " + str(self.successful_slowest).rjust(13))
        out.append("Successful average:   " + str(self.successful_average).rjust(13))
        if self.requests_error > 0:
            out.append(sep)
            out.append("Error fastest:        " + str(self.error_fastest).rjust(13))
            out.append("Error slowest:        " + str(self.error_slowest).rjust(13))
            out.append("Error average:        " + str(self.error_average).rjust(13))
        if self.requests_failed > 0:
            out.append(sep)
            out.append("Failed fastest:       " + str(self.failed_fastest).rjust(13))
            out.append("Failed slowest:       " + str(self.failed_slowest).rjust(13))
            out.append("Failed average:       " + str(self.failed_average).rjust(13))
        if self.pid > 0:
            out.append(sep)
            out.append("CPU:        " + str(self.cpu_ceil).rjust(6) + "% " + str(self.cpu_average).rjust(6) + "% " + str(self.cpu_floor).rjust(6) + "%")
            out.append("MEM:        " + str(self.mem_ceil).rjust(6) + "M " + str(self.mem_average).rjust(6) + "M " + str(self.mem_floor).rjust(6) + "M")
        out.append(sep)
        out.append("Execution time:       " + format_seconds(self._total).rjust(13))
        out.append("Time total:           " + format_seconds(self.time_total).rjust(13))
        out.append("Time successful:      " + format_seconds(self.time_successful).rjust(13))
        if self.requests_error > 0:
            out.append("Time error:           " + format_seconds(self.time_error).rjust(13))
        if self.requests_failed > 0:
            out.append("Time failed:          " + format_seconds(self.time_failed).rjust(13))

        if len(self.errors) > 0:
            out.append(sep)

        for error in self.errors:
            out.append(error)

        for line in out:
            print line
            if self.log:
                logging.info(line)
        return


class Thread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, verbose=None, args=()):
        threading.Thread.__init__(self, group=group, target=target, name=name, verbose=verbose)
        self._stop = False
        self._list = args[0]
        self._requests = args[1]
        self._shuffle = args[2]
        self._log = args[3]
        self.results = []
        self.errors = []
        self.count = 0

        if self._shuffle:
            random.shuffle(self._list)
        return

    def run(self):
        i = 0
        while i < self._requests:
            for e in self._list:
                if self._stop:
                    return

                self.count += 1

                payload = {}
                if 'params' in e:
                    for p in e['params']:
                        payload.update({p['name']: p['value']})

                files = {}
                if 'files' in e:
                    for f in e['files']:
                        path, name = os.path.split(f['value'])
                        try:
                            files[f['name']] = (name, open(f['value'], 'rb'))
                        except:
                            if self._log:
                                logging.error("Unable to read file: " + f['value'])

                try:
                    if e['type'] == "get":
                        req = requests.get(e['url'])
                    elif e['type'] == "delete":
                        req = requests.delete(e['url'])
                    elif e['type'] == "put":
                        req = requests.put(e['url'], data=payload, files=files)
                    else:
                        req = requests.post(e['url'], data=payload, files=files)
                    res = {'url': e['url'], 'data': payload, 'status': req.status_code, 'content': req.text, 'time': (dec(req.elapsed.microseconds) / 1000 / 1000)}
                    if self._log:
                        logging.debug(res)
                except Exception as ex:
                    try:
                        elapsed = dec(req.elapsed.microseconds) / 1000 / 1000
                    except NameError:
                        elapsed = dec(0)

                    if str(ex.message.reason) not in self.errors:
                        self.errors.append(str(ex.message.reason))

                    res = {'url': e['url'], 'data': payload, 'status': 0, 'error': str(ex.message.reason), 'time': elapsed}
                    if self._log:
                        logging.error(res)

                self.results.append(res)
                i += 1
                if i == self._requests:
                    return
        return

    def stop(self):
        self._stop = True


def format_seconds(val):
    return time.strftime("%H:%M:%S", time.gmtime(dec(val)))


def check_pid(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def get_cpumem(pid):
    us = commands.getoutput("ps -p " + str(pid) + " -o pcpu= -o rss=").split()
    us[0] = round(dec(us[0]), 1)
    us[1] = round(dec(us[1]) / 1024, 1)
    return us


def stop_app(s, f):
    for t in Flooder.thread_list:
        t.stop()
    print ""
    sys.exit()
signal.signal(signal.SIGINT, stop_app)
signal.signal(signal.SIGTERM, stop_app)


if __name__ == '__main__':
    flooder = Flooder()
