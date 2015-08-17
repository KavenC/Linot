from linot.Plugins.TwitchNotifier.TwitchEngine import TwitchEngine
from nose.tools import ok_
import requests

TWITCH_REST = 'https://api.twitch.tv/kraken'


class TestTwitchEngine:
    def setUp(self):
        self.twitch = TwitchEngine()

    def testGetChannels(self):
        followed_channels = self.twitch.getChannels()
        ok_(len(followed_channels) > 25)  # to make sure we have tested multiget
        ok_(len(set(followed_channels)) == len(followed_channels))
        for ch in followed_channels:
            expect_url = 'http://www.twitch.tv/'+ch.lower()
            ok_(followed_channels[ch]['url'] == expect_url,
                '{} <-> {}'.format(followed_channels[ch]['url'], expect_url))

    def testGetLiveChannels(self):
        # This is a tricky one, not sure how to properly test it..
        testChannelCount = 10
        live_channels = self.twitch.getLiveChannels()
        error_count = 0
        test_count = 0
        for ch in live_channels:
            ret_json = requests.get(TWITCH_REST+'/streams/'+ch).json()
            try:
                ok_(ret_json['stream']['channel']['display_name'] == ch)
            except KeyError:
                error_count += 1
            test_count += 1
            if test_count >= testChannelCount:
                break
        ok_((float(error_count) / test_count) < 0.20, 'test:{}, error:{}'.format(test_count, error_count))

    def testFollowUnfollowChannel(self):
        self.twitch.unfollowChannel('kaydada')
        followed_channels = self.twitch.getChannels()
        ok_('KayDaDa' not in followed_channels)
        self.twitch.followChannel('kaydada')
        followed_channels = self.twitch.getChannels()
        ok_('KayDaDa' in followed_channels)
        ret = self.twitch.unfollowChannel('kaydada')
        ok_(ret is True)
        followed_channels = self.twitch.getChannels()
        ok_('KayDaDa' not in followed_channels)
        name, ret = self.twitch.followChannel('kaydada2')
        ok_(ret is False)
        ret = self.twitch.unfollowChannel('kaydada2')
        ok_(ret is False)
        name, ret = self.twitch.followChannel('kaydada')
        ok_(ret is True)
