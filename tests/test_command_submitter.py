from collections import defaultdict

from nose.tools import ok_

from linot.command_submitter import CommandSubmitter
import linot.interfaces as interfaces


class TestCommandSubmitter:
    def setUp(self):
        self.sender = CommandSubmitter('test', 'sender')
        interfaces.get('test').reset()
        self.interface = interfaces.get('test')

    def test_code(self):
        ok_(self.sender.code == 'sender')

    def test_send_message(self):
        test_msg = 'test message'
        self.sender.send_message(test_msg)
        ok_(len(self.interface.msg_queue[self.sender.code]) == 1)
        ok_(self.interface.msg_queue[self.sender.code][0] == test_msg,
            self.interface.msg_queue)

    def test_get_display_name(self):
        disp_name = self.sender.get_display_name()
        ok_(disp_name == self.interface.get_display_name(self.sender))

    def test_unicode(self):
        u_name = unicode(self.sender)
        ok_(u_name == unicode(self.sender.get_display_name()))

    def test_dict_hashable(self):
        sender_2 = CommandSubmitter('test', 'sender2')
        sender_3 = CommandSubmitter('some', 'sender')
        sender_same = CommandSubmitter('test', 'sender')
        some_dict = defaultdict(lambda: False)
        some_dict[self.sender] = True
        ok_(some_dict[self.sender] is True)
        ok_(some_dict[sender_2] is False)
        ok_(some_dict[sender_3] is False)
        ok_(some_dict[sender_same] is True)
