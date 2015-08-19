from nose.tools import ok_, raises

from linot import config
from linot.interfaces.line_interface import LineClientP, LineInterface


class TestLineClientP:
    def setUp(self):
        self.line_cfg = config['interface']['line']
        self.lineclient = LineClientP(self.line_cfg['account'],
                                      self.line_cfg['password'])

    def test_find_contact_by_id(self):
        contact = self.lineclient.find_contact_by_id(self.line_cfg['admin_id'])
        ok_(contact.id == self.line_cfg['admin_id'])

    @raises(ValueError)
    def test_find_contact_by_id_exception(self):
        self.lineclient.find_contact_by_id(self.line_cfg['admin_id'][:-2])


class TestLineInterface:
    def setUp(self):
        self.line_interface = LineInterface()

    def test_polling_command(self):
        test_str = 'testing longPoll correctness'
        # first sends a message to myself..
        me = self.line_interface._client.getProfile()
        me.sendMessage(test_str)
        result = self.line_interface.polling_command()
        ok_(len(result) == 1, result)
        submitter, msg = result[0]
        ok_(submitter.code == me.id, submitter)
        ok_(msg == test_str,
            'Message context not match: {} <-> {}'.format(msg, test_str))

    def test_get_contact_by_id(self):
        me = self.line_interface._client.getProfile()
        contact = self.line_interface._get_contact_by_id(me.id)
        ok_(me.id == contact.id, '{} <-> {}'.format(me.id, contact.id))

    def test_send_message(self):
        # first sends a message to myself..
        test_str = 'testing send to client'
        me = self.line_interface._client.getProfile()
        me.sendMessage(test_str)
        result = self.line_interface.polling_command()
        me, msg = result[0]
        self.line_interface.send_message(me, test_str)
        result = self.line_interface.polling_command()
        me, msg = result[0]
        ok_(msg == test_str, 'message not match {} <-> {}'.format(msg, test_str))

    def test_send_message_to_id(self):
        # first sends a message to myself..
        test_str = 'testing send to id'
        me = self.line_interface._client.getProfile()
        me.sendMessage(test_str)
        result = self.line_interface.polling_command()
        me, msg = result[0]
        self.line_interface._send_message_to_id(me.code, test_str)
        result = self.line_interface.polling_command()
        me, msg = result[0]
        ok_(msg == test_str, 'message not match {} <-> {}'.format(msg, test_str))

    def test_get_display_name(self):
        # first sends a message to myself..
        test_str = 'testing send to id'
        me = self.line_interface._client.getProfile()
        me.sendMessage(test_str)
        result = self.line_interface.polling_command()
        me_submitter, msg = result[0]
        me_display_name = self.line_interface.get_display_name(me_submitter)
        ok_(me_display_name == me.name)
