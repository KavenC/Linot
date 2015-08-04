import logging
import logging.config
import sys

config = {
    'version': 1,
    'handlers': {
        'console': {
            'level': logging.DEBUG,
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
            'formatter': 'verbose',
        },
        'file': {
            'level': logging.DEBUG,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'linot.log',
            'maxBytes': 256 * 1024,
            'backupCount': 2,
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s|[%(levelname)s][%(name)s] %(message)s',
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
