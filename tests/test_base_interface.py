from nose.tools import ok_
from nose.tools import raises

from linot.base_interface import BaseInterface


class TestBaseInterface:
    def setUp(self):
        self.interface = BaseInterface()

    def test_name(self):
        ok_(self.interface.NAME is None)

    @raises(NotImplementedError)
    def test_polling_command(self):
        self.interface.polling_command()

    @raises(NotImplementedError)
    def test_send_message(self):
        self.interface.send_message(None, 'test')

    @raises(NotImplementedError)
    def test_get_display_name(self):
        self.interface.get_display_name(None)

    @raises(ValueError)
    def test_sublcass_no_name(self):
        class ErrorSubClass(BaseInterface):
            pass
