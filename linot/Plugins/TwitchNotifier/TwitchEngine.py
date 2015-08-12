#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import json
import requests
from linot.LinotConfig import LinotConfig as Config
import sys
from linot.LinotLogger import logging
logger = logging.getLogger(__name__)


class TwitchRequests:  # pragma: no cover
    TWITCH_API_BASE = 'https://api.twitch.tv/kraken/'
    OAUTH_TOKEN = Config['twitch_oauth']
    IGNORE_STATUS = [
        204,
        422,
        404
    ]

    @classmethod
    def _twitchProcess(cls, action, url, pms, **kwargs):
        twitch_api_url = cls.TWITCH_API_BASE + url
        if pms is None:
            pms_a = {}
        else:
            pms_a = pms
        pms_a['oauth_token'] = cls.OAUTH_TOKEN
        logger.debug('[{}] Url = {}'.format(str(action.__name__), str(twitch_api_url)))
        ret = action(twitch_api_url, params=pms_a, **kwargs)
        logger.debug('Return Code = {}'.format(ret.status_code))
        if ret.status_code not in cls.IGNORE_STATUS:
            return ret.json()
        else:
            return {'code': ret.status_code}

    @classmethod
    def get(cls, url, params=None, **kwargs):
        return cls._twitchProcess(requests.get, url, params, **kwargs)

    @classmethod
    def multiGet(cls, url, params=None, per=25, **kwargs):
        if params is None:
            params = {
                'limit': per,
                'offset': 0
            }
        else:
            params['limit'] = per
            params['offset'] = 0
        json_streams = cls.get(url, params=params, **kwargs)
        resp_list = [json_streams]
        if '_total' in json_streams:
            total = json_streams['_total']
            for offset in range(per, total, per):
                params['offset'] = offset
                params['limit'] = offset + per
                json_streams = cls.get(url, params=params, **kwargs)
                resp_list.append(json_streams)
        return resp_list

    @classmethod
    def put(cls, url, params=None, **kwargs):
        return cls._twitchProcess(requests.put, url, params, **kwargs)

    @classmethod
    def delete(cls, url, params=None, **kwargs):
        return cls._twitchProcess(requests.delete, url, params, **kwargs)

    @classmethod
    def post(cls, url, params=None, **kwargs):
        return cls._twitchProcess(requests.post, url, params, **kwargs)


def JSONPrint(dic):  # pragma: no cover
    print(json.dumps(dic, indent=2, separators=(',', ':')), file=sys.stderr)


class TwitchEngine:

    USER = Config['twitch_user']

    def getChannels(self):
        json_channels_list = TwitchRequests.multiGet('/users/' + self.USER + '/follows/channels')
        channels = {}
        for json_channels in json_channels_list:
            for followed_channel in json_channels['follows']:
                name = followed_channel['channel']['display_name']
                channels[name] = followed_channel['channel']
        return channels

    def getLiveChannels(self):
        live_channel_json = TwitchRequests.multiGet('/streams/followed')
        ret_live_channels = {}
        for json_streams in live_channel_json:
            for stream in json_streams['streams']:
                name = stream['channel']['display_name']
                ret_live_channels[name] = stream['channel']
        return ret_live_channels

    def followChannel(self, channel_name):
        json_streams = TwitchRequests.put(
            '/users/'+self.USER+'/follows/channels/'+channel_name)
        if 'channel' not in json_streams:
            return channel_name, False
        else:
            return json_streams['channel']['display_name'], True

    def unfollowChannel(self, channel_name):
        json_streams = TwitchRequests.delete(
            '/users/'+self.USER+'/follows/channels/'+channel_name)
        if json_streams['code'] == 204:
            return True
        else:
            return False
