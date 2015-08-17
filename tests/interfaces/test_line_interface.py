from nose.tools import ok_

from linot.interface_list import interface_list as interfaces


class TestLineInterface:
    def test_name(self):
        line = interfaces['line']
        ok_(line.NAME == 'line')
        ok_(isinstance(line, LineInterface))
