from threading import Thread, Event

from interface_list import interface_list
import linot.logger
logger = linot.logger.getLogger(__name__)


class CmdServer(Thread):
    def __init__(self, cmd_parser, interface, response_wait=.5):
        super(CmdServer, self).__init__()
        self._stopped = True
        self._stop = Event()
        self._cmd_parser = cmd_parser
        self._response_wait = response_wait
        self._interface = interface
        self._logger = logger.getChild(interface.name)

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
        try:
            arg_list = cmd.split()
            self._logger.debug('get cmd: ' + str(arg_list))
            args, unknown_args = self._cmd_parser.parse_known_args(arg_list)
            if len(unknown_args) > 0:
                self._logger.debug('unknown args: ' + str(unknown_args))  # pragma: no cover
            args.proc(args, sender)
        except SystemExit as e:
            if e.code == 2:
                matched = self._cmd_parser.process_direct_commands(cmd, sender)
                if not matched:
                    self._logger.debug('no known args found.')
                    self._interface.send_message(sender, 'Unknown commands.')
            else:
                self._logger.exception('Unexpected SystemExit')  # pragma: no cover

    def async_stop(self):
        logger.debug('stop is called')
        self._stop.set()

    def stop(self):
        self.async_stop()
        logger.debug('waiting for thread end')

    def stopped(self):
        return self._stopped


server_threads = []


def start(parser):
    # starts one thread for each interface
    # CmdServer automatically starts a new server thread when received a new
    # command
    for interface in interface_list:
        thread = CmdServer(parser, interface_list[interface])
        server_threads.append(thread)
        thread.start()


def stop():
    for thread in server_threads:
        thread.async_stop()

    for thread in server_threads:
        thread.join()
