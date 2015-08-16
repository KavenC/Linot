from nose.tools import ok_, raises

import linot.interface_list as interface
from linot.base_interface import BaseInterface


class SampleInterface(BaseInterface):
    def __init__(self):
        BaseInterface.__init__(self, 'sample')


class TestInterfaceList:
    def test_register_normal(self):
        interface.unregister(SampleInterface)
        interface.register(SampleInterface)
        ok_('sample' in interface.interface_list)
        ok_(isinstance(interface.interface_list['sample'], SampleInterface))

    @raises(NameError)
    def test_duplicated_name(self):
        interface.unregister(SampleInterface)
        interface.register(SampleInterface)
        interface.register(SampleInterface)
