from nose.tools import assert_equal
from nose.tools import assert_raises
from nose.tools import raises
from nose.tools import ok_
from nose.tools import eq_
from linot.LinotArgParser import LinotArgParser
import argparse


class MockLine:
    def __init__(self):
        self.recv = None
        self.msg = None

    def sendMessageToClient(self, recv, msg):
        self.recv = recv
        self.msg = msg


class TestLinotArgParser:
    def setUp(self):
        parser = argparse.ArgumentParser(usage=argparse.SUPPRESS, add_help=False)
        sub_cmd_parser = parser.add_subparsers()
        self.sub_parser = sub_cmd_parser
        self.parser = parser

    def testInit(self):
        def cmdProcess(args, sender):
            pass
        line = MockLine()
        LinotArgParser('testcmd', self.sub_parser, cmdProcess, line)
        # test -h and --help goes to print_help
        args, unknown_args = self.parser.parse_known_args('testcmd -h'.split())
        eq_(len(unknown_args), 0)
        args.proc(args, 'test_sender')
        ok_('command list' in line.msg)
        ok_('test_sender' == line.recv)
        args, unknown_args = self.parser.parse_known_args('testcmd --help'.split())
        eq_(len(unknown_args), 0)
        line.msg = ''
        line.recv = ''
        args.proc(args, 'test_sender')
        ok_('command list' in line.msg)
        ok_('test_sender' == line.recv)

    def testAddArgument_Exclusiveness(self):
        def cmdProcess(args, sender):
            assert_equal(args.a is True and args.b is True, False)
        lap = LinotArgParser('testcmd', self.sub_parser, cmdProcess, None)
        lap.add_argument('-a', action='store_true')
        lap.add_argument('-b', action='store_true')
        with assert_raises(SystemExit) as e:
            args, unknown_args = self.parser.parse_known_args('testcmd -a -b'.split())
            check_str = 'not allowed with'
            ok_(check_str in e.msg)

    def testAddArgument_DestException(self):
        def cmdProcess(args, sender):
            pass
        lap = LinotArgParser('testcmd', self.sub_parser, cmdProcess, None)
        with assert_raises(ValueError):
            lap.add_argument('-a', dest='b', action='store_true')

    def testAddArgument_Func(self):
        def cmdProcess(args, sender):
            if args.b:
                ok_(True)
            else:
                ok_(False)

        def custFunc(value, sender):
            ok_(value and sender)

        lap = LinotArgParser('testcmd', self.sub_parser, cmdProcess, None)
        lap.add_argument('-a', action='store_true', func=custFunc)
        lap.add_argument('-b', action='store_true')  # default proc
        args, unknown_args = self.parser.parse_known_args('testcmd -a'.split())
        args.proc(args, True)
        args, unknown_args = self.parser.parse_known_args('testcmd -b'.split())
        args.proc(args, False)

    def testAddArgument_MultiArgs(self):
        def cmdProcess(args, sender):
            ok_(False)

        def custFunc(value, sender):
            ok_(value)
        lap = LinotArgParser('testcmd', self.sub_parser, cmdProcess, None)
        lap.add_argument('-a', '-b', '-c', action='store_true', func=custFunc)
        args, unkown_args = self.parser.parse_known_args('testcmd -a'.split())
        args, unkown_args = self.parser.parse_known_args('testcmd -b'.split())
        args, unkown_args = self.parser.parse_known_args('testcmd -c'.split())

    @raises(ValueError)
    def testAddArgument_PositionalArgs(self):

        def cmdProcess(args, sender):
            ok_(False)

        lap = LinotArgParser('testcmd', self.sub_parser, cmdProcess, None)
        lap.add_argument('abc', action='store_true')

    def testPrintHelp(self):
        def cmdProcess(args, sender):
            ok_(False)

        test_str = 'testtesttest'
        line = MockLine()
        lap = LinotArgParser('testcmd', self.sub_parser, cmdProcess, line)
        lap.add_argument('-a', action='store_true', help=test_str)
        lap.add_argument('-noshow', action='store_true', help=argparse.SUPPRESS)
        lap.add_argument('-showme', action='store_true', help='')
        args, unknown_args = self.parser.parse_known_args('testcmd -h'.split())
        args.proc(args, 'test_sender')
        cap_text = line.msg
        ok_(test_str in cap_text, True)
        ok_('-nowshow' not in cap_text, True)
        ok_('-showme' in cap_text, True)
        ok_('test_sender' == line.recv)

        # Test help suppress if sender not found (for coverage)
        args, unknown_args = self.parser.parse_known_args('testcmd -h'.split())
        line.msg = None
        line.recv = None
        args.proc(args, None)
        ok_(line.msg is None)
        ok_(line.recv is None)

    def testSubcmdDefault(self):
        def cmdProcess(args, sender):
            if args is None:
                ok_(True)
                return
            ok_(False)

        LinotArgParser('testcmd', self.sub_parser, cmdProcess, None)
        args, unknown_args = self.parser.parse_known_args('testcmd'.split())
        args.proc(args, None)
