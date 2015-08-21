from __future__ import print_function
import argparse
import io

import services
import config
import command_server
from arg_parser import LinotArgParser, LinotParser
import logger
logger = logger.get().getLogger(__name__)


service_instances = {}


def cmd_process(args, sender):
    if args.stopserver:
        if sender.code == config['interface'][sender.interface_name]['admin_id']:
            sender.send_message('Server is shutting down')
            logger.info('server is shutting down')
            for service in service_instances:
                logger.debug('stopping service: ' + service)
                service_instances[service].stop()
                logger.debug(service + ' is stopped')
            logger.debug('stopping command server')
            command_server.stop()
        return

    if args.listservices:
        msg = io.BytesIO()
        for service in service_instances:
            print(service_instances[service], file=msg)
        sender.send_message(msg.getvalue())
        return


def main():
    # Add common commands
    parser = LinotParser(usage=argparse.SUPPRESS, add_help=False)
    cmd_group = LinotArgParser('linot', parser, cmd_process)
    cmd_group.add_argument('-stopserver', action='store_true', help=argparse.SUPPRESS)
    cmd_group.add_argument('-listservices', action='store_true', help='Show installed services')
    # cmd_group.add_argument('-backup', action='store_true', help=argparse.SUPPRESS)
    # cmd_group.add_argument('-listbackups', action='store_true', help=argparse.SUPPRESS)
    # cmd_group.add_argument('-restore', help=argparse.SUPPRESS)

    # Load plugins
    for service in services.pkg_list:
        logger.info('Loading service: ' + service)
        service_instance = services.pkg_list[service].Service()
        service_instance.setup(parser)
        service_instances[service] = service_instance
        service_instance.start()

    command_server.start(parser)

if __name__ == '__main__':
    main()
