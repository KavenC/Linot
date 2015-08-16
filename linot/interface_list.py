import logger
logger = logger.getLogger(__name__)
interface_list = {}  # interface instances


def register(if_cls):
    interface = if_cls()
    if interface.NAME in interface_list:
        logger.critical('interface name conflict: ' + interface.NAME)
        logger.critical('New: {} <-> Old: {}'.format(interface, interface_list[interface.NAME]))
        raise NameError
    interface_list[interface.NAME] = interface


def unregister(if_cls):
    for interface in interface_list:
        if isinstance(interface_list[interface], if_cls):
            del interface_list[interface]
            return
    logger.warn('interface not found on unrgister: {}'.format(if_cls))
