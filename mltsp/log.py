__all__ = ['log']

from colorlog import ColoredFormatter
from logging import StreamHandler, getLogger, DEBUG

formatter = ColoredFormatter(
    "{log_color}{levelname[0]} {asctime} {name}: {reset}{white}{message}",
    datefmt='%d %b %Y %H:%M:%S',
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    },
    style='{',
)

stream = StreamHandler()
stream.setLevel(DEBUG)
stream.setFormatter(formatter)


def get_log(name='mltsp'):
    log = getLogger(name)
    log.setLevel(DEBUG)
    log.addHandler(stream)
    return log


if __name__ == "__main__":
    log = get_log('log')
    log.debug('This is debugging info')
    log.info('This is information')
    log.warning('This is a warning')
    log.error('This is an error')
    log.critical('This is bad news')
