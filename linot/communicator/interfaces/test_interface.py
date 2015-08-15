from linot.communicator.base_interface import BaseInterface
from linot.communicator import interface_list as interfaces


class TestInterface(BaseInterface):
    def __init__(self):
        BaseInterface.__init__(self, 'test')

    def polling_command(self):
        return []

    def send_message(self, receiver, msg):
        return False

    def get_display_name(self, submitter):
        return ''

interfaces.register(TestInterface)
