from nose.tools import assert_equal
from nose.tools import raises
from linot.LinotConfig import LinotConfig as Config
from linot.LineEngine import LineClientP


class TestLineClientP:

    def setUp(self):
        self.lineclient = LineClientP(Config['line_account'],
                                      Config['line_password'])

    def testFindContactById(self):
        contact = self.lineclient.findContactById(Config['admin_id'])
        assert_equal(contact.id, Config['admin_id'])

    @raises(Exception)
    def testFindContactById_exception(self):
        self.lineclient.findContactById(Config['admin_id'][:-2])


from linot.LineEngine import LineEngine


class TestLineEngine:

    def setUp(self):
        self.line_engine = LineEngine()

    def testLongPoll(self):
        test_str = 'testing longPoll correctness'
        # first sends a message to myself..
        me = self.line_engine._client.getProfile()
        me.sendMessage(test_str)
        result = self.line_engine.longPoll()
        assert_equal(len(result), 1, 'Got unexpected operations')
        assert_equal(result[0][0].id, me.id, 'Unexpected sender')
        recv_text = result[0][2].text
        assert_equal(
            recv_text, test_str,
            'Message context not match: {} <-> {}'.format(recv_text, test_str))

    def testGetContactById(self):
        me = self.line_engine._client.getProfile()
        contact = self.line_engine.getContactById(me.id)
        assert_equal(me.id, contact.id, 'id not match')

    def testSendMessageToClient(self):
        test_str = 'testing send to client'
        me = self.line_engine._client.getProfile()
        self.line_engine.sendMessageToClient(me, test_str)
        result = self.line_engine.longPoll()
        recv_text = result[0][2].text
        assert_equal(recv_text, test_str, 'message not match')

    def testSendMessageToId(self):
        test_str = 'testing send to id'
        me = self.line_engine._client.getProfile()
        self.line_engine.sendMessageToId(me.id, test_str)
        result = self.line_engine.longPoll()
        recv_text = result[0][2].text
        assert_equal(recv_text, test_str, 'message not match')
