# -*- coding: utf-8 -*-
import sys
import argparse
import logging
from .manager import Manager

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

try:
    import yaml
except ImportError:
    yaml = None


def main(argv=None):
    parser = argparse.ArgumentParser()
    if yaml is None:
        parser.error('You must install pyaml')
    parser.add_argument('-c', '--config',
                        type=argparse.FileType('r'),
                        required=True,
                        help='Config ini file')
    parser.add_argument('-i', '--input',
                        type=argparse.FileType('r'),
                        help='Input yaml file')
    parser.add_argument('-o', '--output',
                        type=argparse.FileType('w'),
                        default='-',
                        help='Stream output file (Default to STDOUT)')
    args = parser.parse_args(argv or sys.argv[1:])
    config = ConfigParser()
    config.readfp(args.config)
    config = dict(config.items('asterisk'))
    config['save_stream'] = args.output
    manager = Manager(**config)
    task = manager.connect()

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    logging.getLogger('asyncio').setLevel(logging.ERROR)
    log = logging.getLogger('panoramisk')

    def done(future):
        result = future.result()
        log.info('Got result: %r\n', result)

    def send_action(f):
        if args.input:
            action = yaml.load(args.input)
            if action.get('Action').lower() == 'agi':
                future = manager.send_agi_command(action)
            if 'commandid' in [k.lower() for k in action.keys()]:
                future = manager.send_command(action)
            else:
                future = manager.send_action(action)
            log.info('Action %r sent', action)
            future.add_done_callback(done)

    def connected(f):
        if manager.authenticated_future is not None:
            manager.authenticated_future.add_done_callback(send_action)
        else:
            send_action(f)

    task.add_done_callback(connected)

    try:
        manager.loop.run_forever()
    except KeyboardInterrupt:
        args.output.close()
