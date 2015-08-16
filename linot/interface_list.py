import logger
logger = logger.getLogger(__name__)
interface_list = {}  # interface instances


def register(if_cls):
    interface = if_cls()
    if interface.name in interface_list:
        logger.critical('interface name conflict: ' + interface.name)
        logger.critical('New: {} <-> Old: {}'.format(interface, interface_list[interface.name]))
        raise NameError
    interface_list[interface.name] = interface
