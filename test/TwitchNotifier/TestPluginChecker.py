import threading
from nose.tools import ok_
from linot.Plugins.TwitchNotifier.Plugin import Checker
from test.TwitchNotifier.TestPlugin import MockTwitchEngine
from test.TwitchNotifier.TestPlugin import MockLine
from test.TwitchNotifier.TestPlugin import MockSender


class TestChecker:
    def setUp(self):
        self.twitch = MockTwitchEngine()
        self.line = MockLine()
        self.checker = Checker(300, self.twitch, self.line, self.getSublist)
        self.sublist = {}

    def getSublist(self):
        return self.sublist

    def testStopOnProcessing(self):
        self.checker.start()
        threading.Event().wait(1)
        self.checker.refresh()

        def locker():
            locker.event.wait()
            return {}
        locker.event = threading.Event()
        self.checker._twitch.getLiveChannels = locker
        threading.Event().wait(2)  # expect checker wait on getLiveChannels
        locker.event.set()
        self.checker.async_stop()
        ok_(self.checker.is_stopped())
        self.checker.join(5)
        ok_(not self.checker.is_alive())

    def testSkipAlreadyLiveOnBoot(self):
        self.twitch.live_ch_list = {
            'testch1': {
                'status': 'test_status',
                'game': 'test_game',
                'url': 'test_url'
            }
        }
        self.sublist = {'fake_sender': ['testch1']}
        fake_sender = MockSender('fake_sender')
        self.line.contacts = {'fake_sender': fake_sender}
        self.checker.start()
        threading.Event().wait(1)
        self.checker.stop()
        ok_(len(self.line.msg_recv) == 0)
        ok_(len(self.line.msg_text) == 0)

    def testLiveNotification(self):
        self.sublist = {
            'fake_sender': ['testch1'],
            'fake_sender2': ['testch2'],
        }
        fake_sender = MockSender('fake_sender')
        fake_sender2 = MockSender('fake_sender2')
        self.line.contacts = {
            'fake_sender': fake_sender,
            'fake_sender2': fake_sender2
        }
        self.checker.start()
        threading.Event().wait(1)
        self.checker.refresh()
        threading.Event().wait(1)
        ok_(len(self.line.msg_recv) == 0)
        ok_(len(self.line.msg_text) == 0)
        self.twitch.live_ch_list = {
            'testch1': {
                'status': 'test_status',
                'game': 'test_game',
                'url': 'test_url'
            }
        }
        self.checker.refresh()
        threading.Event().wait(1)
        self.checker.stop()
        ok_(fake_sender in self.line.msg_recv)
        ok_(fake_sender2 not in self.line.msg_recv)
        ok_('testch1' in self.line.msg_text[0], self.line.msg_text)

    def testChannelDelOnOff(self):
        self.twitch.live_ch_list = {
            'testch1': {
                'status': 'test_status',
                'game': 'test_game',
                'url': 'test_url'
            }
        }
        self.sublist = {'fake_sender': ['testch1']}
        fake_sender = MockSender('fake_sender')
        self.line.contacts = {'fake_sender': fake_sender}
        self.checker.start()
        threading.Event().wait(1)
        self.twitch.live_ch_list = {}
        self.checker.refresh()
        threading.Event().wait(1)
        ok_(len(self.line.msg_recv) == 0)
        ok_(len(self.line.msg_text) == 0)
        self.twitch.live_ch_list = {
            'testch1': {
                'status': 'test_status',
                'game': 'test_game',
                'url': 'test_url'
            }
        }
        self.checker.refresh()
        threading.Event().wait(1)
        self.checker.stop()
        ok_(fake_sender in self.line.msg_recv)
        ok_('testch1' in self.line.msg_text[0], self.line.msg_text)
