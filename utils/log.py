import logging

def log_init(args):
    level = [logging.INFO, logging.DEBUG][args.debug and args.proc == 1]
    logging.basicConfig(format='[%(process)d|%(asctime)s] %(message)s', level=level)

def log_debug(message):
    logging.debug(message)

def log_info(message):
    logging.info(message)
