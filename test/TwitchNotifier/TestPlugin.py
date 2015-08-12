from nose.tools import ok_
from linot.Plugins.TwitchNotifier.Plugin import Plugin
from linot.LinotArgParser import LinotArgParser
from linot.LinotConfig import LinotConfig as Config
import argparse
import inspect
import pickle
import threading
import os
from collections import defaultdict


class MockSender:
    def __init__(self, name):
        self.id = name


class MockLine:
    def __init__(self):
        self.msg_recv = []
        self.msg_text = []
        self.contatcs = {}

    def sendMessageToClient(self, recv, msg):
        self.msg_recv.append(recv)
        self.msg_text.append(msg)

    def getContactById(self, user_id):
        return self.contacts[user_id]

    def sendMessageToId(self, id, msg):
        client = self.getContactById(id)
        self.sendMessageToClient(client, msg)
        return


class MockTwitchEngine:
    def __init__(self):
        self.ch_list = []
        self.live_ch_list = {}

    def getLiveChannels(self):
        return self.live_ch_list

    def followChannel(self, ch):
        if ch in self.ch_list:
            return ch+'_disp_name', True
        else:
            return '', False

    def unfollowChannel(self, ch):
        try:
            self.ch_list.remove(ch.rstrip('_disp_name'))
        except ValueError as e:
            print ch
            print self.ch_list
            raise e


class TestPlugin:
    def setUp(self):
        self.line = MockLine()
        self.twitch_engine = MockTwitchEngine()
        self.plugin = Plugin(self.line)
        self.plugin._twitch = self.twitch_engine
        self.parser = argparse.ArgumentParser(usage=argparse.SUPPRESS, add_help=False)
        sub_cmd_parser = self.parser.add_subparsers()
        self.cmd_group = LinotArgParser('testcmd', sub_cmd_parser, None, self.line)

    def testSetupArgument(self):
        # TODO Any bettery ways?
        def setMatching1(val, sender):
            setMatching1.ret = (set(val) == set(['test1']))

        def setMatching2(val, sender):
            setMatching2.ret = (set(val) == set(['test1', 'test2']))

        def retVal(val, sender):
            retVal.ret = val

        # test argument and function relation
        test_list = [
            # -subscribe
            ['-subscribe test1', '_subscribe', setMatching1],
            ['-subscribe test1 test2', '_subscribe', setMatching2],
            # -unsubscribe
            ['-unsubscribe test1', '_unsubscribe', setMatching1],
            ['-unsubscribe test1 test2', '_unsubscribe', setMatching2],
            # -listchannel
            ['-listchannel', '_listChannel', retVal],
            ['-listchannel abc', '_listChannel', retVal],
            # -refresh
            ['-refresh', '_refresh', retVal],
            ['-refresh abc', '_refresh', retVal],
            # -listUsers
            ['-listusers', '_listUsers', retVal],
            ['-listusers abc', '_listUsers', retVal],
        ]

        for test in test_list:
            self.setUp()
            method_bak = None
            for name, method in inspect.getmembers(self.plugin, predicate=inspect.ismethod):
                if name == test[1]:
                    method_bak = method
                    setattr(self.plugin, name, test[2])
            ok_(method_bak is not None, test[0] + ' case method not found')
            self.plugin._setup_argument(self.cmd_group)
            cmd = 'testcmd ' + test[0]
            args, unknowns = self.parser.parse_known_args(cmd.split())
            # ok_(len(unknowns) == 0, 'test: '+test[0]+'\nunknowns: '+str(unknowns))
            test[2].ret = False
            args.proc(args, None)
            ok_(test[2].ret, 'test: '+test[0])

    def testStart_SublistExists(self):
        fake_sublist = {
            'testid1': ['testch1', 'testch2', 'testch3'],
            'testid2': ['testch2'],
            'testid3': ['testch1', 'testch3'],
            'testid4': ['testch2'],
        }
        pickle.dump(fake_sublist, open(self.plugin.SUB_FILE, 'wb+'))
        self.plugin._start()
        while(True):
            threading.Event().wait(1)
            try:
                if self.plugin._check_thread.is_alive():
                    self.plugin._stop()
                else:
                    break
            except AttributeError as e:
                print e
        ok_(self.plugin._channel_sub_count['testch1'] == 2, 'count =' + str(self.plugin._channel_sub_count['testch1']))
        ok_(self.plugin._channel_sub_count['testch2'] == 3, 'count =' + str(self.plugin._channel_sub_count['testch2']))
        ok_(self.plugin._channel_sub_count['testch3'] == 2, 'count =' + str(self.plugin._channel_sub_count['testch3']))
        ok_(self.plugin._channel_sub_count['testch4'] == 0, 'count =' + str(self.plugin._channel_sub_count['testch4']))

    def testStart_SublistNotFound(self):
        try:
            os.remove(self.plugin.SUB_FILE)
        except OSError:
            pass
        self.plugin._start()
        while(True):
            threading.Event().wait(1)
            try:
                if self.plugin._check_thread.is_alive():
                    self.plugin._stop()
                else:
                    break
            except AttributeError as e:
                print e
        ok_(set(self.plugin._sublist['testid1']) == set([]))
        ok_(set(self.plugin._sublist['testid2']) == set([]))
        ok_(self.plugin._channel_sub_count['testch1'] == 0, 'count =' + str(self.plugin._channel_sub_count['testch1']))
        ok_(self.plugin._channel_sub_count['testch2'] == 0, 'count =' + str(self.plugin._channel_sub_count['testch2']))

    def testGetSubList(self):
        fake_sublist = {
            'testid1': ['testch1', 'testch2', 'testch3'],
            'testid2': ['testch2'],
            'testid3': ['testch1', 'testch3'],
        }
        pickle.dump(fake_sublist, open(self.plugin.SUB_FILE, 'wb+'))
        self.plugin.start()
        while(True):
            threading.Event().wait(.1)
            try:
                if self.plugin._check_thread.is_alive():
                    self.plugin.stop()
                else:
                    break
            except AttributeError as e:
                print e
        sublist = self.plugin.getSublist()
        ok_(len(fake_sublist.viewkeys() ^ sublist.viewkeys()) == 0)
        for key in fake_sublist:
            ok_(set(fake_sublist[key]) == set(sublist[key]))

    def testCalculateChannelSubCount(self):
        self.plugin._sublist = {
            'testid1': ['testch1', 'testch2', 'testch3'],
            'testid2': ['testch2'],
            'testid3': ['testch1', 'testch3', 'testch2'],
        }
        self.plugin._calculateChannelSubCount()
        ok_(self.plugin._channel_sub_count['testch1'] == 2)
        ok_(self.plugin._channel_sub_count['testch2'] == 3)
        ok_(self.plugin._channel_sub_count['testch3'] == 2)
        ok_(self.plugin._channel_sub_count['testch4'] == 0)
        self.plugin._sublist = defaultdict(list)
        self.plugin._calculateChannelSubCount()
        ok_(self.plugin._channel_sub_count['testch1'] == 0)
        ok_(self.plugin._channel_sub_count['testch2'] == 0)
        ok_(self.plugin._channel_sub_count['testch3'] == 0)
        ok_(self.plugin._channel_sub_count['testch4'] == 0)

    def testSubscribe_One(self):
        try:
            os.remove(self.plugin.SUB_FILE)
        except OSError:
            pass
        self.plugin.start()
        while(True):
            threading.Event().wait(.1)
            try:
                if self.plugin._check_thread.is_alive():
                    self.plugin.stop()
                else:
                    break
            except AttributeError as e:
                print e
        self.plugin._twitch.ch_list = ['testch1', 'testch2']
        fake_sender = MockSender('fake_sender')
        self.plugin._subscribe(['testch1'], fake_sender)
        ok_('testch1_disp_name' in self.plugin._sublist[fake_sender.id],
            'sublist = '+str(self.plugin._sublist[fake_sender.id]))
        ok_('not found' not in ' '.join(self.plugin._line.msg_text))
        ok_(self.plugin._channel_sub_count['testch1_disp_name'] == 1)
        fake_sender2 = MockSender('fake_sender2')
        self.plugin._subscribe(['testch1'], fake_sender2)
        ok_(self.plugin._channel_sub_count['testch1_disp_name'] == 2)

    def testSubscribe_OneAlready(self):
        try:
            os.remove(self.plugin.SUB_FILE)
        except OSError:
            pass
        self.plugin.start()
        while(True):
            threading.Event().wait(.1)
            try:
                if self.plugin._check_thread.is_alive():
                    self.plugin.stop()
                else:
                    break
            except AttributeError as e:
                print e
        self.plugin._twitch.ch_list = ['testch1', 'testch2']
        fake_sender = MockSender('fake_sender')
        self.plugin._sublist[fake_sender.id] = ['testch1_disp_name']
        self.plugin._subscribe(['testch1'], fake_sender)
        ok_(self.plugin._sublist[fake_sender.id].count('testch1_disp_name') == 1,
            'sublist = '+str(self.plugin._sublist[fake_sender.id]))
        ok_('not found' not in ' '.join(self.plugin._line.msg_text))

    def testSubscribe_OneNotFound(self):
        try:
            os.remove(self.plugin.SUB_FILE)
        except OSError:
            pass
        self.plugin.start()
        while(True):
            threading.Event().wait(.1)
            try:
                if self.plugin._check_thread.is_alive():
                    self.plugin.stop()
                else:
                    break
            except AttributeError as e:
                print e
        self.plugin._twitch.ch_list = ['testch2', 'testch3']
        fake_sender = MockSender('fake_sender')
        self.plugin._subscribe(['testch1'], fake_sender)
        ok_('testch1_disp_name' not in self.plugin._sublist[fake_sender.id],
            'sublist = '+str(self.plugin._sublist[fake_sender.id]))
        ok_('not found' in ' '.join(self.plugin._line.msg_text))

    def testSubscribe_Multi(self):
        try:
            os.remove(self.plugin.SUB_FILE)
        except OSError:
            pass
        self.plugin.start()
        while(True):
            threading.Event().wait(.1)
            try:
                if self.plugin._check_thread.is_alive():
                    self.plugin.stop()
                else:
                    break
            except AttributeError as e:
                print e
        self.plugin._twitch.ch_list = ['testch1', 'testch2']
        fake_sender = MockSender('fake_sender')
        self.plugin._subscribe(['testch1', 'testch2'], fake_sender)
        ok_('testch1_disp_name' in self.plugin._sublist[fake_sender.id],
            'sublist = '+str(self.plugin._sublist[fake_sender.id]))
        ok_('testch2_disp_name' in self.plugin._sublist[fake_sender.id],
            'sublist = '+str(self.plugin._sublist[fake_sender.id]))
        ok_('not found' not in ' '.join(self.plugin._line.msg_text))

    def testUnsubscribe_One(self):
        self.testSubscribe_One()
        fake_sender = MockSender('fake_sender')
        fake_sender2 = MockSender('fake_sender2')
        self.plugin._subscribe(['testch2'], fake_sender)
        self.plugin._unsubscribe(['testch1_disp_name'], fake_sender)
        ok_('testch1_disp_name' not in self.plugin._sublist[fake_sender.id],
            'sublist = '+str(self.plugin._sublist[fake_sender.id]))
        ok_('not found' not in ' '.join(self.plugin._line.msg_text))
        ok_(self.plugin._channel_sub_count['testch1_disp_name'] == 1)
        self.plugin._unsubscribe(['testch1_disp_name'], fake_sender2)
        ok_('testch1_disp_name' not in self.plugin._sublist[fake_sender2.id],
            'sublist = '+str(self.plugin._sublist[fake_sender2.id]))
        ok_(self.plugin._channel_sub_count['testch1_disp_name'] == 0)

    def testUnsubscribe_OneNotFound(self):
        self.testSubscribe_One()
        fake_sender = MockSender('fake_sender')
        self.plugin._subscribe(['testch2'], fake_sender)
        self.plugin._unsubscribe(['testch3_disp_name'], fake_sender)
        ok_('testch1_disp_name' in self.plugin._sublist[fake_sender.id],
            'sublist = '+str(self.plugin._sublist[fake_sender.id]))
        ok_('testch2_disp_name' in self.plugin._sublist[fake_sender.id],
            'sublist = '+str(self.plugin._sublist[fake_sender.id]))
        ok_('not found' in ' '.join(self.plugin._line.msg_text))
        ok_(self.plugin._channel_sub_count['testch1_disp_name'] == 2)

    def testUnsubscribe_MultiNotFound(self):
        self.testSubscribe_One()
        fake_sender = MockSender('fake_sender')
        self.plugin._subscribe(['testch2'], fake_sender)
        self.plugin._unsubscribe(['testch3_disp_name', 'testch1_disp_name', 'testch2_disp_name'], fake_sender)
        ok_('testch1_disp_name' not in self.plugin._sublist[fake_sender.id],
            'sublist = '+str(self.plugin._sublist[fake_sender.id]))
        ok_('testch2_disp_name' not in self.plugin._sublist[fake_sender.id],
            'sublist = '+str(self.plugin._sublist[fake_sender.id]))
        ok_('not found' in ' '.join(self.plugin._line.msg_text))
        ok_(self.plugin._channel_sub_count['testch1_disp_name'] == 1)

    def testListChannel(self):
        self.plugin._twitch.live_ch_list = {'testch2_disp_name': None}
        self.testSubscribe_Multi()
        fake_sender = MockSender('fake_sender')
        self.plugin._listChannel(True, fake_sender)
        ok_(' '.join(self.plugin._line.msg_text).count('LIVE') == 1)
        ok_('testch2_disp_name' in ' '.join(self.plugin._line.msg_text))
        ok_('testch1_disp_name' in ' '.join(self.plugin._line.msg_text))

    def testRefresh(self):
        # check admin only
        self.plugin.start()
        while(True):
            threading.Event().wait(.1)
            try:
                if self.plugin._check_thread.is_alive():
                    self.plugin.stop()
                else:
                    break
            except AttributeError as e:
                print e

        def selfRet():
            selfRet.val = True
        selfRet.val = False
        self.plugin._check_thread.refresh = selfRet
        fake_sender = MockSender('fake_sender')
        self.plugin._refresh(True, fake_sender)
        ok_(selfRet.val is not True)
        self.plugin._refresh(True, MockSender(Config['admin_id']))
        ok_(selfRet.val is True)

    def testListUsers(self):
        self.testSubscribe_One()
        self.plugin._subscribe(['testch2'], MockSender('fake_sender2'))
        # check admin only
        self.plugin._listUsers(True, MockSender('fake_sender'))
        ok_('Channels' not in ''.join(self.plugin._line.msg_text))

        class MockContact:
            def __init__(self, name):
                self.name = name
        self.plugin._line.contacts = {
            'fake_sender': MockContact('fake_sender'),
            'fake_sender2': MockContact('fake_sender2'),
        }
        self.plugin._listUsers(True, MockSender(Config['admin_id']))
        # check msg response
        ok_('fake_sender' in ''.join(self.plugin._line.msg_text))
        ok_('fake_sender2' in ''.join(self.plugin._line.msg_text))
        for idx, msg in enumerate(self.plugin._line.msg_text):
            if 'fake_sender' in msg:
                ok_('testch1' in msg)
            if 'fake_sender1' in msg:
                ok_('testch2' in msg)
                ok_('testch1' in msg)
