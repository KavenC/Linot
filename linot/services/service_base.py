import sys

from linot.arg_parser import LinotArgParser


class AttrEnforcer(type):
    def __init__(cls, name, bases, attrs):
        chk_list = ['CMD']
        for attr in chk_list:
            if attr not in attrs:
                raise ValueError("Interface class: '{}' doesn't have {} attribute.".format(name, attr))
        type.__init__(cls, name, bases, attrs)


class ServiceBase:
    __metaclass__ = AttrEnforcer
    CMD = 'test'

    def __init__(self):
        self._started = False

    def __str__(self):
        return '{} ({})'.format(sys.modules[self.__module__].__package__, self.CMD)

    def setup(self, parser):
        ap = LinotArgParser(self.CMD, parser, self._cmd_process)
        self._setup_argument(ap)

    def is_start(self):
        return self._started

    def start(self):
        if not self._started:
            self._start()
            self._started = True

    def stop(self):
        if self._started:
            self._stop()
            self._started = False

    # Plugin should be designed to be safely stopped and re-started at anytime
    def _start(self):
        # Plugin start working!
        raise NotImplementedError

    def _stop(self):
        # Plugin stops
        raise NotImplementedError

    def _setup_argument(self, cmd_group):
        # Add the plugin specific arguments
        raise NotImplementedError

    def _cmd_process(self, args, sender):
        # process argument input
        if args is None:
            # no known arguments
            sender.send_message('Unknown commands.')
        else:
            sender.send_message('Command is not implemented yet')
