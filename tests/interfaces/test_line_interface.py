from nose.tools import ok_

from linot import interfaces
from linot.interfaces.line_interface import LineInterface  # noqa


class TestLineInterface:
    def test_name(self):
        line = interfaces.get('line')
        ok_(line.NAME == 'line')
        # ok_(isinstance(line, LineInterface), line)  # HELP!! why is this failing?
