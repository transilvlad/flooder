# Flooder
**HTTP flooding tool for load testing**

*usage: Flooder [-h] [-v] -j JSON [-t THREADS] [-r REQUESTS] [-ns] [-nl]*

**optional arguments:**
```
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -j JSON, --json JSON  requests list (required, json)
  -t THREADS, --threads THREADS
                        number of parallel threads to use (default: 10)
  -r REQUESTS, --requests REQUESTS
                        number of requests / thread (default: 10)
  -ns, --no-shuffle     disable shuffling of requests list
  -nl, --no-log         disable logging to file
```

**list example:**
```
  [
    {
      "url": "http://localhost:8000/api/url",
      "type": "POST",
      "params": [
        {
          "name": "test",
          "value": "something"
        }
      ]
    },
    ...
  ]
  ```
