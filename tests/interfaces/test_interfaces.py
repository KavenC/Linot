from __future__ import print_function
import os
import sys

from nose.tools import ok_

from linot import interfaces


def create_dummy_interface(file_name, interface_name='delme', server=True):
    path = os.path.dirname(interfaces.__file__)
    with open(os.path.join(path, file_name), 'w+') as f:
        print('from linot.base_interface import BaseInterface', file=f)
        print('class DelMeInterface(BaseInterface):', file=f)
        print("    NAME='{}'".format(interface_name), file=f)
        print('    SERVER={}'.format(server), file=f)
        f.flush()


class TestIntrefaces:
    def test_import_only_ends_with_interface(self):
        path = os.path.dirname(interfaces.__file__)
        with open(os.path.join(path, 'del_me.py'), 'w+') as f:
            print('from nose.tools import ok_', file=f)
            print('ok_(False)', file=f)
            f.flush()
        reload(interfaces)
        ok_('interfaces.del_me' not in sys.modules)
        try:
            os.remove(os.path.join(path, 'del_me.py'))
            os.remove(os.path.join(path, 'del_me.pyc'))
        except OSError:
            pass

        create_dummy_interface(file_name='del_me_interface.py')
        loaded = False
        try:
            reload(interfaces)
        except ValueError:
            loaded = True
        os.remove(os.path.join(path, 'del_me_interface.py'))
        os.remove(os.path.join(path, 'del_me_interface.pyc'))
        if 'del_me_interface' in sys.modules:
            loaded = True
        ok_(loaded)

    def test_name_conflict(self):
        path = os.path.dirname(interfaces.__file__)
        create_dummy_interface(file_name='del_me_interface.py',
                               interface_name='test')

        error = False
        try:
            reload(interfaces)
        except NameError:
            error = True
        os.remove(os.path.join(path, 'del_me_interface.py'))
        os.remove(os.path.join(path, 'del_me_interface.pyc'))
        ok_(error)
        reload(interfaces)  # clean up mess
