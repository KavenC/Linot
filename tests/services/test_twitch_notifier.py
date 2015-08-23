import argparse
import inspect
import pickle
import threading
import os
import requests
from collections import defaultdict

from nose.tools import ok_

from linot import interfaces
from linot.command_submitter import CommandSubmitter
from linot.services.twitch_notifier.service import Service, Checker
from linot.services.twitch_notifier.twitch_engine import TwitchEngine
from linot.arg_parser import LinotParser
from linot import config


class MockTwitchEngine:
    def __init__(self):
        self.exists_ch_list = []
        self.live_ch_list = {}
        self.followed_ch_list = {}

    def get_followed_channels(self, user):
        if user not in self.followed_ch_list:
            return None
        else:
            return self.followed_ch_list[user]

    def get_live_channels(self):
        return self.live_ch_list

    def follow_channel(self, ch):
        for exch in self.exists_ch_list:
            if exch.lower() == ch.lower():
                return exch, True
        return '', False

    def unfollow_channel(self, ch):
        pass

    def get_channel_info(self, ch):
        for exch in self.exists_ch_list:
            if exch.lower() == ch.lower():
                return {'display_name': exch}
        return None

    def set_exists_channel_list(self, ch_list):
        # swapcase to simulate display name does not necessary have the same
        # case as input
        self.exists_ch_list = [x.swapcase() for x in ch_list]

    def set_live_channel_list(self, ch_list):
        # swapcase to simulate display name does not necessary have the same
        # case as input
        for ch in ch_list:
            self.live_ch_list[ch.swapcase()] = ch_list[ch]


class TestTwitchEngine:
    TWITCH_REST = 'https://api.twitch.tv/kraken'

    def setUp(self):
        self.twitch = TwitchEngine()

    def test_get_followed_channels(self):
        # twitch user should be following more than 25 users before this test
        followed_channels = self.twitch.get_followed_channels(self.twitch.USER)
        ok_(len(followed_channels) > 25,
            'twitch user should be following more than'
            '25 users before running this test')  # to make sure we have tested multiget
        ok_(len(set(followed_channels)) == len(followed_channels))
        for ch in followed_channels:
            expect_url = 'http://www.twitch.tv/'+ch.lower()
            ok_(followed_channels[ch]['url'] == expect_url,
                '{} <-> {}'.format(followed_channels[ch]['url'], expect_url))

        # test user not found returns None
        followed_channels = self.twitch.get_followed_channels(self.twitch.USER[:-2])
        ok_(followed_channels is None)

    def test_get_live_channels(self):
        # This is a tricky one, not sure how to properly test it..
        test_channel_count = 10
        live_channels = self.twitch.get_live_channels()
        error_count = 0
        test_count = 0
        for ch in live_channels:
            ret_json = requests.get(self.TWITCH_REST+'/streams/'+ch).json()
            try:
                ok_(ret_json['stream']['channel']['display_name'] == ch)
            except KeyError:
                error_count += 1
            test_count += 1
            if test_count >= test_channel_count:
                break
        # there is time difference between get live and check live
        # it is possible that channel went offline between these 2 api calls
        # so we just expect 80% of tested channels are really live on the
        # 2nd api call
        ok_((float(error_count) / test_count) < 0.20, 'test:{}, error:{}'.format(test_count, error_count))

    def test_follow_unfollow_channel(self):
        self.twitch.unfollow_channel('kaydada')
        followed_channels = self.twitch.get_followed_channels(self.twitch.USER)
        ok_('KayDaDa' not in followed_channels)
        self.twitch.follow_channel('kaydada')
        followed_channels = self.twitch.get_followed_channels(self.twitch.USER)
        ok_('KayDaDa' in followed_channels)
        ret = self.twitch.unfollow_channel('kaydada')
        ok_(ret is True)
        followed_channels = self.twitch.get_followed_channels(self.twitch.USER)
        ok_('KayDaDa' not in followed_channels)
        name, ret = self.twitch.follow_channel('kaydada2')
        ok_(ret is False)
        ret = self.twitch.unfollow_channel('kaydada2')
        ok_(ret is False)
        name, ret = self.twitch.follow_channel('kaydada')
        ok_(ret is True)

    def test_get_channel_info(self):
        info = self.twitch.get_channel_info('kaydada')
        ok_(info['display_name'] == 'KayDaDa')

        info = self.twitch.get_channel_info('kaydada_no_this_guy')
        ok_(info is None, info)


class TestChecker:
    def setUp(self):
        self.twitch = MockTwitchEngine()
        self.checker = Checker(300, self.twitch, self.get_sublist)
        self.sublist = {}
        interfaces.get('test').reset()

    def get_sublist(self):
        return self.sublist

    def test_stop_on_processing(self):
        self.checker.start()
        threading.Event().wait(1)
        self.checker.refresh()

        def locker():
            locker.event.wait()
            return {}
        locker.event = threading.Event()
        self.checker._twitch.get_live_channels = locker
        threading.Event().wait(2)  # expect checker wait on getLiveChannels
        locker.event.set()

        self.checker.async_stop()
        ok_(self.checker.is_stopped())
        self.checker.join(5)
        ok_(not self.checker.is_alive())

    def test_skip_already_lived_on_boot(self):
        self.twitch.live_ch_list = {
            'testch1': {
                'status': 'test_status',
                'game': 'test_game',
                'url': 'test_url'
            }
        }
        fake_sender = CommandSubmitter('test', 'fake_sender')
        self.sublist = {fake_sender: ['testch1']}

        self.checker.start()
        threading.Event().wait(1)
        self.checker.stop()
        ok_(len(interfaces.get('test').msg_queue[fake_sender]) == 0)

    def test_live_notification(self):
        fake_sender = CommandSubmitter('test', 'fake_sender')
        fake_sender2 = CommandSubmitter('test', 'fake_sender2')
        self.sublist = {
            fake_sender: ['testch1'],
            fake_sender2: ['testch2'],
        }

        self.checker.start()
        threading.Event().wait(1)
        self.checker.refresh()
        threading.Event().wait(1)
        ok_(len(interfaces.get('test').msg_queue[fake_sender]) == 0)
        ok_(len(interfaces.get('test').msg_queue[fake_sender2]) == 0)

        self.twitch.live_ch_list = {
            'TESTCH1': {
                'status': u'test_status',
                'game': u'test_game',
                'url': u'test_url'
            }
        }
        self.checker.refresh()
        threading.Event().wait(1)
        self.checker.stop()
        ok_('TESTCH1' in ' '.join(interfaces.get('test').msg_queue[fake_sender]),
            interfaces.get('test').msg_queue[fake_sender])
        ok_('TESTCH1' not in ' '.join(interfaces.get('test').msg_queue[fake_sender2]),
            interfaces.get('test').msg_queue[fake_sender2])

    def test_channel_offline(self):
        self.twitch.live_ch_list = {
            'testch1': {
                'status': u'test_status',
                'game': u'test_game',
                'url': u'test_url'
            }
        }
        fake_sender = CommandSubmitter('test', 'fake_sender')
        self.sublist = {fake_sender: ['testch1']}
        self.checker.start()
        threading.Event().wait(1)
        self.twitch.live_ch_list = {}
        self.checker.refresh()
        threading.Event().wait(1)
        # no message should be sent
        ok_(len(interfaces.get('test').msg_queue[fake_sender]) == 0)

        # simulate channel goes live
        self.twitch.live_ch_list = {
            'testch1': {
                'status': u'test_status',
                'game': u'test_game',
                'url': u'test_url'
            }
        }
        self.checker.refresh()
        threading.Event().wait(1)
        self.checker.stop()
        ok_('testch1' in ' '.join(interfaces.get('test').msg_queue[fake_sender]),
            interfaces.get('test').msg_queue[fake_sender])


class TestService:
    def setUp(self):
        self.service = Service()
        self.service._twitch = MockTwitchEngine()
        self.parser = LinotParser(usage=argparse.SUPPRESS, add_help=False)
        interfaces.get('test').reset()

    def tearDown(self):
        try:
            os.remove(self.service.SUB_FILE)
        except OSError:
            pass

    def test_init(self):
        # some basic tests
        ok_(self.service.is_start() is False)
        ok_(self.service.CMD == 'twitch')

    def test_setup_argument(self):
        def set_matching_0(val, sender):
            set_matching_0.ret = (len(val) == 0)

        def set_matching_1(val, sender):
            set_matching_1.ret = (set(val) == set(['test1']))

        def set_matching_2(val, sender):
            set_matching_2.ret = (set(val) == set(['test1', 'test2']))

        def ret_val(val, sender):
            ret_val.ret = val

        def direct_cmd_set_match(match, cmd, sender):
            direct_cmd_set_match.ret = (set(match) == set(['kaydada']))

        # test argument and function relation
        test_list = [
            # -subscribe +
            ['-subscribe test1', '_subscribe', set_matching_1],
            ['-subscribe test1 test2', '_subscribe', set_matching_2],
            # -unsubscribe +
            ['-unsubscribe test1', '_unsubscribe', set_matching_1],
            ['-unsubscribe test1 test2', '_unsubscribe', set_matching_2],
            # -unsuball
            ['-unsuball', '_unsub_all', ret_val],
            ['-unsuball abc', '_unsub_all', ret_val],
            # -import
            ['-import test1', '_import', set_matching_1],
            # -listchannel
            ['-listchannel', '_list_channel', ret_val],
            ['-listchannel abc', '_list_channel', ret_val],
            # -refresh
            ['-refresh', '_refresh', ret_val],
            ['-refresh abc', '_refresh', ret_val],
            # -listusers *
            ['-listusers', '_list_users', set_matching_0],
            ['-listusers test1', '_list_users', set_matching_1],
            ['-listusers test1 test2', '_list_users', set_matching_2],
        ]

        for test in test_list:
            self.setUp()
            method_bak = None
            for name, method in inspect.getmembers(self.service, predicate=inspect.ismethod):
                if name == test[1]:
                    method_bak = method
                    setattr(self.service, name, test[2])
            ok_(method_bak is not None, test[0] + ' case method not found')
            self.service.setup(self.parser)  # setup calls _setup_arguments
            cmd = self.service.CMD + ' ' + test[0]
            args, unknowns = self.parser.parse_known_args(cmd.split())
            test[2].ret = False
            args.proc(args, None)
            ok_(test[2].ret, 'failed: '+test[0])

        # test direct command
        test_list = [
            # direct command: sub by url
            ['www.twitch.tv/kaydada', '_sub_by_url', direct_cmd_set_match],
        ]

        for test in test_list:
            self.setUp()
            method_bak = None
            for name, method in inspect.getmembers(self.service, predicate=inspect.ismethod):
                if name == test[1]:
                    method_bak = method
                    setattr(self.service, name, test[2])
            ok_(method_bak is not None, test[0] + ' case method not found')
            self.service.setup(self.parser)  # setup calls _setup_arguments
            cmd = test[0]
            self.parser.process_direct_commands(cmd, None)
            ok_(test[2].ret, 'failed: '+test[0])

    def test_start_subfile_exists(self):
        fake_sublist = {
            'testid1': ['testch1', 'testch2', 'testch3'],
            'testid2': ['testch2'],
            'testid3': ['testch1', 'testch3'],
            'testid4': ['testch2'],
        }
        pickle.dump(fake_sublist, open(self.service.SUB_FILE, 'wb+'))
        self.service.start()
        threading.Event().wait(.1)
        self.service.stop()
        ok_(self.service._channel_sub_count['testch1'] == 2, 'count =' + str(self.service._channel_sub_count['testch1']))
        ok_(self.service._channel_sub_count['testch2'] == 3, 'count =' + str(self.service._channel_sub_count['testch2']))
        ok_(self.service._channel_sub_count['testch3'] == 2, 'count =' + str(self.service._channel_sub_count['testch3']))
        ok_(self.service._channel_sub_count['testch4'] == 0, 'count =' + str(self.service._channel_sub_count['testch4']))

    def test_start_subfile_not_found(self):
        self.service.start()
        threading.Event().wait(.1)
        self.service.stop()
        ok_(set(self.service._sublist['testid1']) == set([]))
        ok_(set(self.service._sublist['testid2']) == set([]))
        ok_(self.service._channel_sub_count['testch1'] == 0, 'count =' + str(self.service._channel_sub_count['testch1']))
        ok_(self.service._channel_sub_count['testch2'] == 0, 'count =' + str(self.service._channel_sub_count['testch2']))

    def test_get_sublist(self):
        fake_sublist = {
            'testid1': ['testch1', 'testch2', 'testch3'],
            'testid2': ['testch2'],
            'testid3': ['testch1', 'testch3'],
        }
        pickle.dump(fake_sublist, open(self.service.SUB_FILE, 'wb+'))
        self.service.start()
        threading.Event().wait(.1)
        self.service.stop()
        sublist = self.service.get_sublist()
        ok_(len(fake_sublist.viewkeys() ^ sublist.viewkeys()) == 0)
        for key in fake_sublist:
            ok_(set(fake_sublist[key]) == set(sublist[key]))

    def test_calculate_channel_count(self):
        self.service._sublist = {
            'testid1': ['testch1', 'testch2', 'testch3'],
            'testid2': ['testch2'],
            'testid3': ['testch1', 'testch3', 'testch2'],
        }
        self.service._calculate_channel_sub_count()
        ok_(self.service._channel_sub_count['testch1'] == 2)
        ok_(self.service._channel_sub_count['testch2'] == 3)
        ok_(self.service._channel_sub_count['testch3'] == 2)
        ok_(self.service._channel_sub_count['testch4'] == 0)
        self.service._sublist = defaultdict(list)
        self.service._calculate_channel_sub_count()
        ok_(self.service._channel_sub_count['testch1'] == 0)
        ok_(self.service._channel_sub_count['testch2'] == 0)
        ok_(self.service._channel_sub_count['testch3'] == 0)
        ok_(self.service._channel_sub_count['testch4'] == 0)

    def test_subscribe_one(self):
        try:
            os.remove(self.service.SUB_FILE)
        except OSError:
            pass

        self.service.start()
        threading.Event().wait(.1)
        self.service.stop()

        self.service._twitch.set_exists_channel_list(['testch1', 'testch2'])
        fake_sender = CommandSubmitter('test', 'fake_sender')
        self.service._subscribe(['testch1'], fake_sender)

        ok_('testch1' in [x.lower() for x in self.service._sublist[fake_sender]],
            'sublist = '+str(self.service._sublist[fake_sender]))
        ok_('not found' not in ' '.join(interfaces.get('test').msg_queue[fake_sender]))
        ok_(self.service._channel_sub_count['testch1'] == 1)

        fake_sender2 = CommandSubmitter('test', 'fake_sender2')
        self.service._subscribe(['testch1'], fake_sender2)

        ok_(self.service._channel_sub_count['testch1'] == 2)

    def test_subscribe_one_exists(self):
        try:
            os.remove(self.service.SUB_FILE)
        except OSError:
            pass
        self.service.start()
        threading.Event().wait(.1)
        self.service.stop()

        self.service._twitch.set_exists_channel_list(['testch1', 'testch2'])
        fake_sender = CommandSubmitter('test', 'fake_sender')
        self.service._sublist[fake_sender] = ['testch1']
        self.service._subscribe(['testch1'], fake_sender)

        ok_(self.service._sublist[fake_sender].count('testch1') == 1,
            'sublist = '+str(self.service._sublist[fake_sender]))
        ok_('not found' not in ' '.join(interfaces.get('test').msg_queue[fake_sender]))

    def test_subscribe_one_not_found(self):
        self.service.start()
        threading.Event().wait(.1)
        self.service.stop()

        self.service._twitch.set_exists_channel_list(['testch2', 'testch3'])
        fake_sender = CommandSubmitter('test', 'fake_sender')
        self.service._subscribe(['testch1'], fake_sender)

        ok_('testch1' not in self.service._sublist[fake_sender],
            'sublist = '+str(self.service._sublist[fake_sender]))
        ok_('not found' in ' '.join(interfaces.get('test').msg_queue[fake_sender]))

    def test_subscribe_multi(self):
        try:
            os.remove(self.service.SUB_FILE)
        except OSError:
            pass
        self.service.start()
        threading.Event().wait(.1)
        self.service.stop()

        self.service._twitch.set_exists_channel_list(['testch1', 'testch2'])
        fake_sender = CommandSubmitter('test', 'fake_sender')
        self.service._subscribe(['testch1', 'testch2'], fake_sender)
        ok_('testch1' in self.service._sublist[fake_sender],
            'sublist = '+str(self.service._sublist[fake_sender]))
        ok_('testch2' in self.service._sublist[fake_sender],
            'sublist = '+str(self.service._sublist[fake_sender]))
        ok_('not found' not in ' '.join(interfaces.get('test').msg_queue[fake_sender]))

    def test_unsubscribe_one(self):
        self.test_subscribe_one()

        fake_sender = CommandSubmitter('test', 'fake_sender')
        fake_sender2 = CommandSubmitter('test', 'fake_sender2')
        self.service._subscribe(['testch2'], fake_sender)
        self.service._unsubscribe(['testch1'], fake_sender)

        ok_('testch1' not in self.service._sublist[fake_sender],
            'sublist = '+str(self.service._sublist[fake_sender]))
        ok_('not found' not in ' '.join(interfaces.get('test').msg_queue[fake_sender]))
        ok_(self.service._channel_sub_count['testch1'] == 1)

        self.service._unsubscribe(['testch1'], fake_sender2)

        ok_('testch1' not in self.service._sublist[fake_sender2],
            'sublist = '+str(self.service._sublist[fake_sender2]))
        ok_(self.service._channel_sub_count['testch1'] == 0)

    def test_unsubscribe_one_not_found(self):
        self.test_subscribe_one()

        fake_sender = CommandSubmitter('test', 'fake_sender')
        self.service._subscribe(['testch2'], fake_sender)
        self.service._unsubscribe(['testch3'], fake_sender)

        ok_('testch1' in self.service._sublist[fake_sender],
            'sublist = '+str(self.service._sublist[fake_sender]))
        ok_('testch2' in self.service._sublist[fake_sender],
            'sublist = '+str(self.service._sublist[fake_sender]))
        ok_('not found' in ' '.join(interfaces.get('test').msg_queue[fake_sender]))
        ok_(self.service._channel_sub_count['testch1'] == 2)

    def test_unsubscribe_multi_not_found(self):
        self.test_subscribe_one()

        fake_sender = CommandSubmitter('test', 'fake_sender')
        self.service._subscribe(['testch2'], fake_sender)
        self.service._unsubscribe(['testch3', 'testch1', 'testch2'], fake_sender)

        ok_('testch1' not in self.service._sublist[fake_sender],
            'sublist = '+str(self.service._sublist[fake_sender]))
        ok_('testch2' not in self.service._sublist[fake_sender],
            'sublist = '+str(self.service._sublist[fake_sender]))
        ok_('not found' in ' '.join(interfaces.get('test').msg_queue[fake_sender]))
        ok_(self.service._channel_sub_count['testch1'] == 1)

    def test_list_channel(self):
        self.service._twitch.set_live_channel_list({'testch2': {'display_name': 'TESTCH2'}})
        self.test_subscribe_multi()

        fake_sender = CommandSubmitter('test', 'fake_sender')
        self.service._list_channel(True, fake_sender)
        ok_(' '.join(interfaces.get('test').msg_queue[fake_sender]).count('LIVE') == 1)

        check_msg = ' '.join(interfaces.get('test').msg_queue[fake_sender])
        ok_('testch2' in check_msg.lower())
        ok_('testch1' in check_msg.lower())

    def test_list_channel_invalidate_cache(self):
        self.service._twitch.set_live_channel_list({'testch2': {'display_name': 'TESTCH2'}})
        self.test_subscribe_multi()
        self.service._channel_name_cache.clear()

        fake_sender = CommandSubmitter('test', 'fake_sender')
        self.service._list_channel(True, fake_sender)
        ok_(' '.join(interfaces.get('test').msg_queue[fake_sender]).count('LIVE') == 1)

        check_msg = ' '.join(interfaces.get('test').msg_queue[fake_sender])
        ok_('testch2' in check_msg.lower())
        ok_('testch1' in check_msg.lower())

    def test_refresh(self):
        # check admin only
        self.service.start()
        threading.Event().wait(.1)
        self.service.stop()

        def self_ret():
            self_ret.val = True
        self_ret.val = False

        self.service._check_thread.refresh = self_ret

        config['interface']['test'] = {'admin_id': 'test_admin'}
        fake_sender = CommandSubmitter('test', 'fake_sender')
        self.service._refresh(True, fake_sender)

        ok_(self_ret.val is not True)

        self.service._refresh(True, CommandSubmitter('test', 'test_admin'))
        ok_(self_ret.val is True)

    def test_list_users_no_user(self):
        # issue #10, list user hit exception while there is no user
        config['interface']['test'] = {'admin_id': 'test_admin'}
        try:
            os.remove(self.service.SUB_FILE)
        except OSError:
            pass

        self.service.start()
        threading.Event().wait(.1)
        self.service.stop()

        fake_sender = CommandSubmitter('test', 'test_admin')
        self.service._list_users([], fake_sender)

        # check there is a response to user
        ok_(len(''.join(interfaces.get('test').msg_queue[fake_sender])) > 0)

    def test_list_users(self):
        self.test_subscribe_one()
        self.service._subscribe(['testch2'], CommandSubmitter('test', 'fake_sender2'))
        config['interface']['test'] = {'admin_id': 'test_admin'}

        # check admin only
        fake_sender = CommandSubmitter('test', 'fake_sender')
        self.service._list_users([], fake_sender)
        ok_('Channels' not in ''.join(interfaces.get('test').msg_queue[fake_sender]))

        fake_sender = CommandSubmitter('test', 'test_admin')
        self.service._list_users([], fake_sender)

        # check msg response
        ok_('fake_sender' in ''.join(interfaces.get('test').msg_queue[fake_sender]))
        ok_('fake_sender2' in ''.join(interfaces.get('test').msg_queue[fake_sender]))
        ok_('testch1' not in ''.join(interfaces.get('test').msg_queue[fake_sender]))
        ok_('testch2' not in ''.join(interfaces.get('test').msg_queue[fake_sender]))

        # test list single user, channels
        interfaces.get('test').reset()
        for index in range(2):
            self.service._list_users([index], fake_sender)
            msg = ' '.join(interfaces.get('test').msg_queue[fake_sender])

            if 'fake_sender' in msg:
                ok_('testch1' in msg)
            elif 'fake_sender2' in msg:
                ok_('testch2' in msg)
                ok_('testch1' in msg)

        # test list multiple user channels
        interfaces.get('test').reset()
        self.service._list_users(range(2), fake_sender)
        ok_('fake_sender' in ''.join(interfaces.get('test').msg_queue[fake_sender]))
        ok_('fake_sender2' in ''.join(interfaces.get('test').msg_queue[fake_sender]))
        ok_('testch1' in ''.join(interfaces.get('test').msg_queue[fake_sender]))
        ok_('testch2' in ''.join(interfaces.get('test').msg_queue[fake_sender]))

    def test_sub_by_url(self):
        sender = CommandSubmitter('test', 'sender')
        self.service._twitch.exists_ch_list = ['KayDaDa', 'LinotServant']
        self.service.setup(self.parser)
        self.service.start()
        threading.Event().wait(1)
        self.service.stop()
        self.service._sub_by_url(['KayDaDa', 'LinotServant'], 'dummy', sender)
        ok_('KayDaDa'.lower() in self.service._sublist[sender],
            'sublist = '+str(self.service._sublist[sender]))
        ok_('LinotServant'.lower() in self.service._sublist[sender],
            'sublist = '+str(self.service._sublist[sender]))

        self.service._unsubscribe(['KayDaDa', 'LinotServant'], sender)
        ok_('KayDaDa'.lower() not in self.service._sublist[sender],
            'sublist = '+str(self.service._sublist[sender]))
        ok_('LinotServant'.lower() not in self.service._sublist[sender],
            'sublist = '+str(self.service._sublist[sender]))

        # Integration test
        self.parser.process_direct_commands('www.twitch.tv/KayDaDa twitch.tv/LinotServant', sender)
        ok_('KayDaDa'.lower() in self.service._sublist[sender],
            'sublist = '+str(self.service._sublist[sender]))
        ok_('LinotServant'.lower() in self.service._sublist[sender],
            'sublist = '+str(self.service._sublist[sender]))

    def test_unsub_all(self):
        sender = CommandSubmitter('test', 'sender')
        test_channels = ['testch1', 'testch2', 'testch3']
        self.service._twitch.set_exists_channel_list(test_channels)

        self.service.setup(self.parser)
        self.service.start()
        threading.Event().wait(1)
        self.service.stop()

        self.service._subscribe(test_channels, sender)
        self.service._list_channel(True, sender)
        # make sure subscribe success
        for ch in test_channels:
            ok_(ch.lower() in ' '.join(interfaces.get('test').msg_queue[sender]).lower())

        interfaces.get('test').reset()

        self.service._unsub_all(True, sender)
        self.service._list_channel(True, sender)
        for ch in test_channels:
            ok_(ch.lower() not in ' '.join(interfaces.get('test').msg_queue[sender]).lower())

    def test_import(self):
        sender = CommandSubmitter('test', 'tester')
        short_test_channels = ['testch'+str(x) for x in range(3)]
        long_test_channels = ['testch'+str(x) for x in range(10)]

        self.service.setup(self.parser)
        self.service.start()
        threading.Event().wait(1)
        self.service.stop()

        # test small amount of followed channel
        self.service._twitch.followed_ch_list = {'some_twitch_user': short_test_channels}
        self.service._import(['some_twitch_user'], sender)
        self.service._list_channel(True, sender)
        for ch in short_test_channels:
            ok_(ch.lower() in ' '.join(interfaces.get('test').msg_queue[sender]).lower())
        interfaces.get('test').reset()
        self.service._unsub_all(True, sender)

        # test large amount of followed channel
        self.service._twitch.followed_ch_list = {'some_twitch_user': long_test_channels}
        self.service._import(['some_twitch_user'], sender)
        self.service._list_channel(True, sender)
        for ch in long_test_channels:
            ok_(ch.lower() in ' '.join(interfaces.get('test').msg_queue[sender]).lower())
        ok_('a while' in ' '.join(interfaces.get('test').msg_queue[sender]).lower())
        interfaces.get('test').reset()
        self.service._unsub_all(True, sender)

        # test not found
        self.service._twitch.followed_ch_list = {'some_twitch_user': long_test_channels}
        self.service._import(['some_twitch_user2'], sender)
        self.service._list_channel(True, sender)
        for ch in long_test_channels:
            ok_(ch.lower() not in ' '.join(interfaces.get('test').msg_queue[sender]).lower())
        ok_('not found' in ' '.join(interfaces.get('test').msg_queue[sender]).lower())
        interfaces.get('test').reset()
        self.service._unsub_all(True, sender)
