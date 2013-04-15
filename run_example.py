#!/usr/bin/env python
import example
import sys
from wsgiref.simple_server import make_server


def main():
    server = make_server('127.0.0.1', 8080, example.main())
    print('http://127.0.0.1:8080')
    server.serve_forever()


if __name__ == '__main__':
    sys.exit(main())
