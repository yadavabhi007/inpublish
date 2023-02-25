"""
Color:
'DEBUG': 'red',
'INFO': 'cyan',
'WARNING': 'yellow',
'ERROR': 'red',
'CRITICAL': 'bold_black,bg_white'
Usage:
    logger.log_debug(__name__, python_wiki_rss_url)
    logger.log_info(__name__, python_wiki_rss_url)
    logger.log_warn(__name__, python_wiki_rss_url)
    logger.log_error(__name__, python_wiki_rss_url)
    logger.log_critical(__name__, python_wiki_rss_url)
"""

import logging


LOG_INTRO = "INTERATTIVO-LOG ->"


def log_debug(name, message):
    logger = logging.getLogger(name)
    logger.debug(f"{LOG_INTRO} {message}")


def log_info(name, message):
    logger = logging.getLogger(name)
    logger.info(f"{LOG_INTRO} {message}")


def log_warn(name, message):
    logger = logging.getLogger(name)
    logger.warning(f"{LOG_INTRO} {message}")


def log_error(name, message):
    logger = logging.getLogger(name)
    logger.error(f"{LOG_INTRO} {message}")


def log_critical(name, message):
    logger = logging.getLogger(name)
    logger.critical(f"{LOG_INTRO} {message}")
