import logging
import logging.config
import yaml


def setup_logging():
    with open('app/settings/logging.yaml', 'r') as f:
        log_cfg = yaml.safe_load(f.read())
        logging.config.dictConfig(log_cfg)