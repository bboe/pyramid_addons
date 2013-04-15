#!/usr/bin/env python
import json
import requests
import sys


def main():
    if not 1 < len(sys.argv) < 4:
        print('Usage: {0} name [value]'.format(sys.argv[0]))
        return 1
    data = {'name': sys.argv[1]}
    if len(sys.argv) == 3:
        data['value'] = sys.argv[2]
    response = requests.put('http://127.0.0.1:8080/item',
                            data=json.dumps(data))
    if response.status_code == 400:
        data = response.json()
        print(data['error'])
        for message in data['messages']:
            print(message)
        return 1
    elif response.status_code != 301:
        print(response.status_code)
        print(response.content)
        return 1



if __name__ == '__main__':
    sys.exit(main())
