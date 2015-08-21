from threading import Thread, Event

import interfaces
import logger
logger = logger.get().getLogger(__name__)


class CmdServer(Thread):
    def __init__(self, cmd_parser, interface, response_wait=.5):
        super(CmdServer, self).__init__()
        self._stopped = True
        self._stop = Event()
        self._cmd_parser = cmd_parser
        self._response_wait = response_wait
        self._interface = interface
        self._logger = logger.getChild(interface.NAME)

    def run(self):
        self._stopped = False
        self._logger.info('server thread start')
        while(not self._stop.is_set()):
            cmd_list = self._interface.polling_command()
            for submitter, cmd in cmd_list:
                worker = Thread(target=self._process_command, args=(cmd, submitter))
                worker.start()
            self._stop.wait(self._response_wait)

        # thread stop process
        self._stopped = True
        self._logger.info('Thread stop')

    def _process_command(self, cmd, sender):
        # this function is runned by a worker thread
        logger = self._logger.getChild('worker')
        try:
            arg_list = cmd.split()
            logger.debug('get cmd: ' + str(arg_list))
            args, unknown_args = self._cmd_parser.parse_known_args(arg_list)
            if len(unknown_args) > 0:
                logger.debug('unknown args: ' + str(unknown_args))  # pragma: no cover
            args.proc(args, sender)
        except SystemExit as e:
            # TODO maybe these processes could be hided in to cmd parser
            if e.code == 2:
                # reach here if no sub command is found in the cmd
                # direct command is processed here
                matched = self._cmd_parser.process_direct_commands(cmd, sender)
                if not matched:
                    # if no direct command is matching
                    # response to user that we cannot recognize the command
                    logger.debug('no known args found.')
                    sender.send_message('Unknown commands.')
            else:
                logger.exception('Unexpected SystemExit')  # pragma: no cover

    def async_stop(self):
        logger.debug('stop is called')
        self._stop.set()

    def stop(self):
        self.async_stop()
        logger.debug('waiting for thread end')
        self.join()

server_threads = []


def start(parser, iflist=interfaces.avail()):
    # starts one thread for each interface
    # CmdServer automatically starts a new server thread when received a new
    # command
    global server_threads
    server_threads = []  # if restarted, clear all old threads
    server_if_list = [x for x in iflist if interfaces.class_dict[x].SERVER]
    for interface in server_if_list:
        thread = CmdServer(parser, interfaces.get(interface))
        server_threads.append(thread)
        thread.start()


def stop():
    for thread in server_threads:
        thread.async_stop()

    for thread in server_threads:
        thread.join()
