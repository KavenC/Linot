from linot.communicator.command_submitter import CommandSubmitter


class BaseInterface:
    def __init__(self, interface_name):
        self.name = interface_name

    def polling_command(self):
        """Blocking polling command input"""
        raise NotImplementedError
        submitter = CommandSubmitter(self.name, id)
        command = ''
        return [(submitter, command)]

    def send_message(self, receiver, msg):
        """Sends message to the receiver"""
        raise NotImplementedError
        return True

    def get_display_name(self, submitter):
        """Get submitter display name"""
        raise NotImplementedError
        return ''
