from nose.tools import ok_
from nose.tools import raises

from linot import interfaces
from linot.services.service_base import ServiceBase
from linot.command_submitter import CommandSubmitter
from linot.arg_parser import LinotParser


class TestServiceBase:
    def setUp(self):
        self.service = ServiceBase()

    def test_init(self):
        ok_(not self.service.is_start())

    @raises(NotImplementedError)
    def test_setup(self):
        parser = LinotParser()
        self.service.setup(parser)

    @raises(NotImplementedError)
    def test_start(self):
        ok_(self.service.is_start() is False)
        self.service.start()

    def test_start_normal(self):
        def mock_start():
            pass
        self.service._start = mock_start
        self.service.start()
        ok_(self.service.is_start() is True)
        self.service = ServiceBase()
        self.service._started = True
        self.service.start()  # should not have exception

    @raises(NotImplementedError)
    def test_stop(self):
        self.service._started = True
        self.service.stop()

    def test_stop_normal(self):
        def mock_stop():
            pass
        self.service.stop()
        self.service._started = True
        self.service._stop = mock_stop
        self.service.stop()
        ok_(self.service.is_start() is False)

    def test_cmd_process(self):
        test_sender = CommandSubmitter('test', 'mock')
        self.service._cmd_process(None, test_sender)
        test_if = interfaces.get('test')
        # cmd_process arg=None indicates the msg contains no recognized command
        # we should return something to let user know
        ok_('Unknown' in test_if.msg_queue[test_sender.code][0])
        test_if.reset()
        self.service._cmd_process('test', test_sender)
        ok_('not implemented' in test_if.msg_queue[test_sender.code][0])

    def test_str(self):
        str_trans = str(self.service)
        ok_(self.service.CMD in str_trans)

    @raises(ValueError)
    def test_attr_enforce(self):
        class ErrorService(ServiceBase):
            pass
