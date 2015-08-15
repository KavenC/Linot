import sys
import logging
import logging.config

config = {
    'version': 1,
    'handlers': {
        'console': {
            'level': logging.DEBUG,
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose',
        },
        'file': {
            'level': logging.DEBUG,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'linot.log',
            'maxBytes': 32 * 1024,
            'backupCount': 2,
            'formatter': 'verbose',
            'mode': 'w+',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s|[%(levelname)s][%(name)s]: %(message)s',
            'datefmt': '%Y-%m-%d|%H:%M:%S',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': logging.NOTSET
        },
    },

}
logging.config.dictConfig(config)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
sys.modules[__name__] = logging
