class NameAttrEnforcer(type):
    def __init__(cls, name, bases, attrs):
        if 'NAME' not in attrs:
            raise ValueError("Interface class: '{}' doesn't have NAME attribute.".format(name))
        type.__init__(cls, name, bases, attrs)


class BaseInterface:
    """Subclass must defined NAME class variable"""
    __metaclass__ = NameAttrEnforcer
    NAME = None

    def polling_command(self):
        """Blocking polling command input"""
        raise NotImplementedError
        # submitter = CommandSubmitter(self.name, id)
        # command = ''
        # return [(submitter, command)]

    def send_message(self, receiver, msg):
        """Sends message to the receiver"""
        raise NotImplementedError
        # return True

    def get_display_name(self, submitter):
        """Get submitter display name"""
        raise NotImplementedError
        # return ''
