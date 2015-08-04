from __future__ import print_function
import TwitchEngine
from linot.Plugins.PluginBase import PluginBase
from linot.LinotConfig import LinotConfig as Config
import pickle
from collections import defaultdict
from threading import Thread, Event, Lock
import copy
from linot.LinotLogger import logging
logger = logging.getLogger(__name__)


class Checker(Thread):
    _status_lock = Lock()

    def __init__(self, period, twitch, line, sublist):
        super(Checker, self).__init__()
        self._stop = Event()
        self._polling = Event()
        self._period = period
        self._twitch = twitch
        self._line = line
        self._sublist = sublist

    def run(self):
        self._stop.clear()
        logger.info('Twitch Checker thread started')
        # Skip 1st notify if channels are already live before plugin load
        self._setLiveChannels(self._twitch.getLiveChannels())
        while(True):
            logger.debug('Wait polling {} sec.'.format(self._period))
            self._polling.wait(self._period)
            logger.debug('Polling event is triggered.')
            self._polling.clear()
            if self._stop.isSet():
                break
            current_live_channels = self._twitch.getLiveChannels()
            logger.debug('Live Channels: '+str(current_live_channels.viewkeys()))
            local_live_channels = self.getLiveChannels()
            off_channels = local_live_channels.viewkeys() - current_live_channels.viewkeys()
            for ch in off_channels:
                # TODO do we have to notify user the channel went off?
                del local_live_channels[ch]
            new_live_channels = current_live_channels.viewkeys() - local_live_channels.viewkeys()
            # Send live notifications to subcribers
            for ch in new_live_channels:
                local_live_channels[ch] = current_live_channels[ch]
                local_sublist = self._sublist()
                for user_id in local_sublist:
                    if ch in local_sublist[user_id]:
                        msg = """{channel_name} is now streamming!!
[Title]\t{channel_title}
[Playing]\t{channel_playing}
{channel_url}""".format(
                            channel_name=ch,
                            channel_title=current_live_channels[ch]['status'],
                            channel_playing=current_live_channels[ch]['game'],
                            channel_url=current_live_channels[ch]['url'])
                        self._line.sendMessageToId(user_id, msg)
            self._setLiveChannels(local_live_channels)

        # TODO thread stop process
        logger.info('Twitch Checker thread stopped')

    def _setLiveChannels(self, ch_list):
        self._status_lock.acquire(True)
        self._live_channels = ch_list
        self._status_lock.release()

    def refresh(self):
        logger.debug('Trigger refresh')
        self._polling.set()

    def getLiveChannels(self):
        self._status_lock.acquire(True)
        ch_stat = copy.copy(self._live_channels)
        self._status_lock.release()
        return ch_stat

    def stop(self):
        self._polling.set()
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


class Plugin(PluginBase):
    CMD_PREFIX = 'twitch'
    SUB_FILE = 'twitch_sublist.p'
    CHECK_PERIOD = 300
    _sublist_lock = Lock()

    def __init__(self, line):
        PluginBase.__init__(self, line)
        self._twitch = TwitchEngine.TwitchEngine()

    def _setup_argument(self, cmd_group):
        import argparse
        cmd_group.add_argument('-subscribe', nargs='+', func=self._subscribe,
                               help='Subscribe channels')
        cmd_group.add_argument('-unsubscribe', nargs='+', func=self._unsubscribe,
                               help='Unsubscribe channels')
        cmd_group.add_argument('-listchannel', action='store_true', func=self._listChannel,
                               help='List channels you\'ve subscribed')
        cmd_group.add_argument('-refresh', action='store_true', func=self._refresh,
                               help=argparse.SUPPRESS)
        cmd_group.add_argument('-listusers', action='store_true', func=self._listUsers,
                               help=argparse.SUPPRESS)

    def _start(self):
        # Load subscribe list
        try:
            logger.debug('Loading subscribe list from file')
            self._sublist = pickle.load(open(self.SUB_FILE, 'rb'))
            self._calculateChannelSubCount()
        except IOError:
            logger.debug('Subscribe list file not found, create empty.')
            self._sublist = defaultdict(list)
            self._channel_sub_count = defaultdict(int)
        self._check_thread = Checker(
            self.CHECK_PERIOD, self._twitch, self._line, self.getSublist)
        self._check_thread.start()

    def _stop(self):
        self._check_thread.stop()

    def getSublist(self):
        self._sublist_lock.acquire(True)
        local_sublist = copy.copy(self._sublist)
        self._sublist_lock.release()
        return local_sublist

    def _calculateChannelSubCount(self):
        self._channel_sub_count = defaultdict(int)
        for subr in self._sublist:
            for ch in self._sublist[subr]:
                self._channel_sub_count[ch] += 1

    def _subscribe(self, chs, sender):
        # Handles user request for subscribing channels
        # We actually let the LinotServant to follow these channels
        # so that we can check if they are online use streams/followed API
        not_found = []
        for ch in chs:
            # reduce api invocation
            if ch in self._sublist[sender.id]:
                continue
            ch_disp_name, stat = self._twitch.followChannel(ch)
            if stat is False:
                not_found.append(ch)
            else:
                self._sublist_lock.acquire(True)
                self._sublist[sender.id].append(ch_disp_name)
                self._sublist_lock.release()
                self._channel_sub_count[ch_disp_name] += 1
                pickle.dump(self._sublist, open(self.SUB_FILE, 'wb+'))

        if len(not_found) > 0:
            print('Channel not found: '+' '.join(not_found))
        print('Done')
        return

    def _unsubscribe(self, chs, sender):
        # Handles user request for unsubscribing channels
        not_found = []
        for ch in chs:
            self._sublist_lock.acquire(True)
            try:
                self._sublist[sender.id].remove(ch)
            except ValueError:
                not_found.append(ch)
                self._sublist_lock.release()
                continue
            self._sublist_lock.release()
            self._channel_sub_count[ch] -= 1
            pickle.dump(self._sublist, open(self.SUB_FILE, 'wb+'))
            if self._channel_sub_count[ch] <= 0:
                self._twitch.unfollowChannel(ch)
                self._channel_sub_count.pop(ch, None)

        if len(not_found) > 0:
            print('Channel not found: '+' '.join(not_found))
        print('Done')
        return

    def _listChannel(self, value, sender):
        print('Your subscribed channels:')
        live_channels = self._check_thread.getLiveChannels()
        for ch in self._sublist[sender.id]:
            if ch in live_channels:
                stat = '[LIVE]'
            else:
                stat = '[OFF]'
            print('{}\t{}'.format(stat, ch))

    def _refresh(self, value, sender):
        if sender.id == Config['admin_id']:
            self._check_thread.refresh()
            print('Done')

    def _listUsers(self, args, sender):
        # List all user who has subscription
        # <Admin only>
        if sender.id == Config['admin_id']:
            for user in self._sublist:
                contact = self._line.getContactById(user)
                print(contact.name)
                print('> ', end='')
                for ch in self._sublist[user]:
                    print(ch, end=', ')
        return
