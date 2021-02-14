import logging
import os
import whendo.core.util as util

logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default_handler': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'filename': os.path.join(util.Dirs.log_dir(), 'job.log'),
            'encoding': 'utf8'
        },
    },
    'loggers': {
        '': {
            'handlers': ['default_handler'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}
logging.config.dictConfig(logging_config)