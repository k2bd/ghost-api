import logging


def get_logger() -> logging.Logger:
    """
    Get a logger that's configured appropriately in local or Lambda
    environments.
    """
    # See https://stackoverflow.com/a/56579088
    logger = logging.getLogger()
    if len(logger.handlers) > 0:
        # The Lambda environment pre-configures a handler logging to stderr.
        # If a handler is already configured, `.basicConfig` does not execute.
        # Thus we set the level directly.
        logger.setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)

    return logger
