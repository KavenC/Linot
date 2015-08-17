from linot.Plugins.PluginBase import PluginBase
from linot.LinotArgParser import LinotParser
from nose.tools import ok_
from nose.tools import raises


class MockLine:
    def __init__(self):
        self.msg_recv = []
        self.msg_text = []

    def sendMessageToClient(self, recv, msg):
        self.msg_recv.append(recv)
        self.msg_text.append(msg)


class TestPluginBase:
    def setUp(self):
        self.plugin = PluginBase('mock_line')

    def test_init(self):
        ok_(self.plugin._line == 'mock_line')

    @raises(NotImplementedError)
    def test_setup(self):
        parser = LinotParser()
        self.plugin.setup(parser)

    @raises(NotImplementedError)
    def test_start(self):
        ok_(self.plugin.is_start() is False)
        self.plugin.start()

    def test_start_normal(self):
        def mock_start():
            pass
        self.plugin._start = mock_start
        self.plugin.start()
        ok_(self.plugin.is_start() is True)
        self.plugin = PluginBase('dummy')
        self.plugin._started = True
        self.plugin.start()

    @raises(NotImplementedError)
    def test_stop(self):
        self.plugin._started = True
        self.plugin.stop()

    def test_stop_normal(self):
        def mock_stop():
            pass
        self.plugin.stop()
        self.plugin._started = True
        self.plugin._stop = mock_stop
        self.plugin.stop()
        ok_(self.plugin.is_start() is False)

    def test_cmd_process(self):
        self.plugin = PluginBase(MockLine())
        self.plugin._cmd_process(None, 'sender')
        ok_(self.plugin._line.msg_recv[0] == 'sender')
        ok_('Unknown' in self.plugin._line.msg_text[0], self.plugin._line.msg_text[0])
        self.plugin._cmd_process('test', 'sender')
        ok_(self.plugin._line.msg_recv[1] == 'sender')
        ok_('not implemented' in self.plugin._line.msg_text[1], self.plugin._line.msg_text[1])
