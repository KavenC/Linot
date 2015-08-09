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
        logger.info('thread start')
        while(True):
            op_list = self._client.longPoll()
            for op in op_list:
                logger.debug('get line op: '+str(op))
                sender = op[0]
                message = op[2]
                msg = message.text
                try:
                    cmd_list = msg.split()
                    logger.debug('get cmd: '+str(cmd_list))
                    args, unknown_args = self._cmd_parser.parse_known_args(cmd_list)
                    if len(unknown_args) > 0:
                        logger.debug('unknown args: ' + str(unknown_args))
                    args.proc(args, sender)
                except SystemExit as e:
                    if e.code == 2:
                        logger.debug('no known args found.')
                        self._client.sendMessageToClient(sender, 'Unknown commands.')
                    else:
                        logger.exception('Unexpected SystemExit')

            if self._stop.wait(random.randint(0, self.MAX_RESP_TIME)):
                break

        # TODO thread stop process
        logger.info('Thread stop')

    def stop(self):
        logger.info('Stopping')
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()
