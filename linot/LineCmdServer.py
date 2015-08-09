from __future__ import print_function
from threading import Thread, Event
import random
from linot.LinotLogger import logging
logger = logging.getLogger(__name__)


class LineCmdServer(Thread):
    MAX_RESP_TIME = 5

    def __init__(self, client, cmd_parser):
        super(LineCmdServer, self).__init__()
        self._stopped = True
        self._stop = Event()
        self._client = client
        self._cmd_parser = cmd_parser
        random.seed()

    def run(self):
        self._stop.clear()
        self._stopped = False
        logger.info('thread start')
        while(not self._stop.is_set()):
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
                        logger.debug('unknown args: ' + str(unknown_args))  #pragma: no cover
                    args.proc(args, sender)
                except SystemExit as e:
                    if e.code == 2:
                        logger.debug('no known args found.')
                        self._client.sendMessageToClient(sender, 'Unknown commands.')
                    else:
                        logger.exception('Unexpected SystemExit')  # pragma: no cover

            self._stop.wait(random.randint(0, self.MAX_RESP_TIME))

        # TODO thread stop process
        self._stopped = True
        logger.info('Thread stop')

    def stop(self):
        logger.info('Stopping')
        self._stop.set()

    def stopped(self):
        return self._stopped
