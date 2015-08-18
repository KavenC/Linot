class AttrEnforcer(type):
    def __init__(cls, name, bases, attrs):
        chk_list = ['NAME', 'SERVER']
        for attr in chk_list:
            if attr not in attrs:
                raise ValueError("Interface class: '{}' doesn't have {} attribute.".format(name, attr))
        type.__init__(cls, name, bases, attrs)


class BaseInterface:
    """Subclass must defined NAME class variable"""
    __metaclass__ = AttrEnforcer
    NAME = None
    SERVER = True

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
