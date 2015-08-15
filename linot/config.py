import sys
import cPickle


class _Config(object):
    def __init__(self, config_file):
        self._config_dist = cPickle.load(open(config_file, 'rb'))

    def __getitem__(self, key):
        return self._config_dist[key]

    __getattr__ = __getitem__

__config = _Config('config.p')
sys.modules[__name__] = __config
