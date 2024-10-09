from logger_config import get_logger

xlink_services = {
    "DEV6": {"host": "dev6-xlink.globetools.com:",
             "port": 444,
             },
    "DEV9": {"host": "dev6-xlink.globetools.com:",
             "port": 444,
             },
}


class XlinkClient:
    def __init__(self, env, logger=get_logger(__name__)):
        if logger:
            self.logger = logger

        xlink_service = xlink_services[env]["host"]



