#!/usr/bin/env python3
'''
Script to add / remove AAP controller node from rotation for mainantance
'''

import time
import json
import sys
import configparser
from argparse import ArgumentParser
from requests.auth import HTTPBasicAuth
import urllib3
import requests

config = configparser.ConfigParser()
config.read('.platform.conf')

url = config.get('general', 'url')
basic = HTTPBasicAuth(config.get('general', 'username'), config.get('general', 'password'))
headers = {'Content-type': 'application/json'}
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def args():
    '''
    Function for the command line arguments of node and state
    '''
    parser = ArgumentParser(description=\
            "Removes instances from cluster and waits for them to drain or adds them back")
    parser.add_argument('-n', '--node', action="store", dest='node', required=True)
    parser.add_argument('-e', '--enabled', action="store", dest='state',\
            required=True, choices=['true', 'false'])
    return parser.parse_args()

def check_host():
    '''
    Function to check if host is a valid host in AAP
    '''
    hosts = []
    response = requests.get(url, auth=basic, headers=headers, verify=False, timeout=120)
    instance = response.json()
    for result in instance['results']:
        hosts.append(result['hostname'])
    if args.node in hosts:
        pass
    else:
        raise SystemExit("Error: Node not found, Please check that you have a valid node")

def get_id():
    '''
    Function to get the id assoscated with the node in AAP
    '''
    response = requests.get(url, auth=basic, headers=headers, verify=False, timeout=120)
    instance = response.json()
    for result in instance['results']:
        if args.node in result["hostname"]:
            return result["id"]

def set_state():
    '''
    Set the state of the node based on the command line peramaters passed
    '''
    requests.put(url + str(get_id()) + '/', auth=basic, headers=headers, verify=False, \
            timeout=120,
            json={'hostname': args.node,
            "capacity_adjustment": "1.00",
            'enabled': args.state,
            "managed_by_policy": 'true',
            "node_type": "control",
            "node_state": "ready",
            "listener_port": 27199})

def loop():
    '''
    Checks if any jobs are running on the node and waits for all to complete
    before finishing
    '''
    drained = False
    while not drained:
        try:
            response = requests.get(url + str(get_id()) + '/', auth=basic, headers=headers, \
                    verify=False, timeout=120)
            instance = response.json()
            if instance['consumed_capacity'] == 0:
                drained = True
                sys.exit(0)
        except KeyboardInterrupt:
            print("Exiting...")
            sys.exit(0)
    time.sleep(30)

if __name__ == "__main__":
    args = args()
    check_host()
    set_state()
    if args.state == 'true':
        sys.exit(0)
    else:
        loop()
