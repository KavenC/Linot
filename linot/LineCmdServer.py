from __future__ import print_function
from threading import Thread, Event
import random
import sys
import StringIO
from linot.LinotLogger import logging
logger = logging.getLogger(__name__)


class LineCmdServer(Thread):
    MAX_RESP_TIME = 5

    def __init__(self, client, cmd_parser):
        super(LineCmdServer, self).__init__()
        self._stop = Event()
        self._client = client
        self._cmd_parser = cmd_parser
        random.seed()

    def run(self):
        self._stop.clear()
        logger.info('Thread start')
        while(True):
            op_list = self._client.longPoll()
            for op in op_list:
                logger.debug('Get op: '+str(op))
                sender = op[0]
                message = op[2]
                msg = message.text
                org_stdout = sys.stdout
                sys.stdout = cap_stdout = StringIO.StringIO()
                try:
                    cmd_list = msg.split()
                    logger.debug('Get Cmd: '+str(cmd_list))
                    args, unknown_args = self._cmd_parser.parse_known_args(cmd_list)
                    if len(unknown_args) > 0:
                        logger.debug('Get unknown args: ' + str(unknown_args))
                    args.proc(args, sender)
                except SystemExit as e:
                    if e.code == 2:
                        logger.debug('Unable to parse args')
                    else:
                        logger.exception('Unexpected SystemExit')
                send_msg = cap_stdout.getvalue()
                sys.stdout = org_stdout
                if len(send_msg) > 0:
                    self._client.sendMessageToClient(sender, send_msg)
                else:
                    self._client.sendMessageToClient(sender, 'Unknown commands.')

            if self._stop.wait(random.randint(0, self.MAX_RESP_TIME)):
                break

        # TODO thread stop process
        logger.info('Thread stop')

    def stop(self):
        logger.info('Stopping')
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()
