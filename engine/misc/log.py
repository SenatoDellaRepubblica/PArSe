

import logging
import traceback
import logging.handlers

from config import LOG_PATH
from engine.misc.output import print_out_and_log


def set_log(level_log, log_filename = 'log.txt', noterminal = True):
    """
    Imposta le caratteristiche del log
    :return:
    """

    # TODO: rivedere gestione del Log: invia sia in output che su console
    logging.getLogger().setLevel(level_log)
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    #datefmt = '%m/%d/%Y %I:%M:%S %p'
    #logging.basicConfig(datefmt=datefmt, format=format, level=level_log)
    formatter = logging.Formatter(log_format)

    if not noterminal:
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level_log)
        # set a format which is simpler for console use
        console_handler.setFormatter(formatter)
        # add the handler to the root logger
        logging.getLogger().addHandler(console_handler)

    # File Handler
    filehandler = logging.handlers.RotatingFileHandler(filename=f'{LOG_PATH}/{log_filename}', maxBytes=1024 * 1024 * 20, backupCount=5)
    filehandler.setFormatter(formatter)
    filehandler.setLevel(level_log)
    # Memory Handler
    memoryhandler = logging.handlers.MemoryHandler(1024 * 10, level_log, filehandler)
    logging.getLogger().addHandler(memoryhandler)

    return memoryhandler


def log_uncaught_exceptions(ex_cls, ex, tb):
    join = ''.join(traceback.format_tb(tb))
    s = '{0}: {1}'.format(ex_cls, ex)
    logging.critical(join)
    print_out_and_log(join)
    logging.critical(s)
    print_out_and_log(s)