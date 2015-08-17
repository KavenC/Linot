import argparse
import re

from nose.tools import assert_raises
from nose.tools import raises
from nose.tools import ok_
from nose.tools import eq_

from linot.arg_parser import LinotArgParser, LinotParser
import linot.interfaces as interfaces
from linot.command_submitter import CommandSubmitter


class TestLinotArgParser:
    def setUp(self):
        parser = LinotParser(usage=argparse.SUPPRESS, add_help=False)
        self.parser = parser

    def test_print_help(self):
        def cmd_process(args, sender):
            pass

        test_str = 'testtesttest'
        lap = LinotArgParser('testcmd', self.parser, cmd_process)
        lap.add_argument('-a', action='store_true', help=test_str)
        lap.add_argument('-noshow', action='store_true', help=argparse.SUPPRESS)
        lap.add_argument('-showme', action='store_true', help='')

        # test -h and --help goes to print_help
        args, unknown_args = self.parser.parse_known_args('testcmd -h'.split())
        eq_(len(unknown_args), 0)
        sender = CommandSubmitter('test', 'test_sender')
        args.proc(args, sender)
        msg_queue = interfaces.get('test').msg_queue
        ok_('command list' in ' '.join(msg_queue[sender.code]))
        args, unknown_args = self.parser.parse_known_args('testcmd --help'.split())
        eq_(len(unknown_args), 0)
        interfaces.get('test').reset()
        args.proc(args, sender)
        msg_queue = interfaces.get('test').msg_queue
        ok_('command list' in ' '.join(msg_queue[sender.code]))

        # add help
        args, unknown_args = self.parser.parse_known_args('testcmd -h'.split())
        interfaces.get('test').reset()
        args.proc(args, sender)
        msg_queue = interfaces.get('test').msg_queue
        msg = ' '.join(msg_queue[sender.code])
        ok_(test_str in msg, msg)
        ok_('-nowshow' not in msg)
        ok_('-showme' in msg)

        # Test help suppress if sender not found (for coverage)
        args, unknown_args = self.parser.parse_known_args('testcmd -h'.split())
        interfaces.get('test').reset()
        args.proc(args, None)
        msg_queue = interfaces.get('test').msg_queue
        msg = ' '.join(msg_queue[sender.code])
        ok_(msg is '', msg)

    def test_add_argument_exclusiveness(self):
        def cmd_process(args, sender):
            ok_((args.a and args.b) is False)
        lap = LinotArgParser('testcmd', self.parser, cmd_process)
        lap.add_argument('-a', action='store_true')
        lap.add_argument('-b', action='store_true')
        with assert_raises(SystemExit) as e:
            args, unknown_args = self.parser.parse_known_args('testcmd -a -b'.split())
            check_str = 'not allowed with'
            ok_(check_str in e.msg)

    def test_add_argument_dest_exception(self):
        def cmd_process(args, sender):
            pass
        lap = LinotArgParser('testcmd', self.parser, cmd_process)
        with assert_raises(ValueError):
            lap.add_argument('-a', dest='b', action='store_true')

    def test_add_argument_func(self):
        def cmd_process(args, sender):
            ok_(args.b and not sender)

        def cust_func(value, sender):
            ok_(value and sender)

        lap = LinotArgParser('testcmd', self.parser, cmd_process)
        lap.add_argument('-a', action='store_true', func=cust_func)
        lap.add_argument('-b', action='store_true')  # default proc
        args, unknown_args = self.parser.parse_known_args('testcmd -a'.split())
        args.proc(args, True)
        args, unknown_args = self.parser.parse_known_args('testcmd -b'.split())
        args.proc(args, False)

    def test_add_argument_multiargs(self):
        def cmd_process(args, sender):
            ok_(False)

        def cust_func(value, sender):
            ok_(value)
            cust_func.called += 1

        cust_func.called = 0
        lap = LinotArgParser('testcmd', self.parser, cmd_process)
        lap.add_argument('-a', '-b', '-c', action='store_true', func=cust_func)
        args, unkown_args = self.parser.parse_known_args('testcmd -a'.split())
        args.proc(args, None)
        args, unkown_args = self.parser.parse_known_args('testcmd -b'.split())
        args.proc(args, None)
        args, unkown_args = self.parser.parse_known_args('testcmd -c'.split())
        args.proc(args, None)
        ok_(cust_func.called == 3)

    @raises(ValueError)
    def test_add_argument_positional(self):
        def cmd_process(args, sender):
            ok_(False)

        lap = LinotArgParser('testcmd', self.parser, cmd_process)
        lap.add_argument('abc', action='store_true')

    def test_subcmd_default_process(self):
        def cmd_process(args, sender):
            cmd_process.called = True
            ok_(args is None)
            ok_(sender == 'test_sender')

        cmd_process.called = False
        LinotArgParser('testcmd', self.parser, cmd_process)
        args, unknown_args = self.parser.parse_known_args('testcmd'.split())
        args.proc(args, 'test_sender')

    def test_direct_command(self):
        def cmd_checker1(match_list, cmd, sender):
            cmd_checker1.runned = True
            cmd_checker1.cmd = cmd
            ok_('1234' in match_list)

        def cmd_checker2(match_list, cmd, sender):
            cmd_checker2.runned = True
            cmd_checker2.cmd = cmd
            ok_('1234' in match_list)

        # Here we only test the api correctness
        # the integration test will be in command_server test
        ap = LinotArgParser('testcmd', self.parser, None)
        ap.add_direct_command(cmd_checker1, '[cxyz]+([0-9]+)', re.IGNORECASE)
        ap = LinotArgParser('testcmd2', self.parser, None)
        ap.add_direct_command(cmd_checker2, '[abc]+([0-9]+)', re.IGNORECASE)
        cmd_checker1.runned = False
        cmd_checker2.runned = False
        self.parser.process_direct_commands('1234', None)
        ok_(cmd_checker1.runned is False)
        ok_(cmd_checker2.runned is False)
        self.parser.process_direct_commands('xyz1234', None)
        ok_(cmd_checker1.runned is True)
        ok_(cmd_checker2.runned is False)
        cmd_checker1.runned = False
        self.parser.process_direct_commands('ab1234', None)
        ok_(cmd_checker1.runned is False)
        ok_(cmd_checker2.runned is True)
        cmd_checker2.runned = False
        self.parser.process_direct_commands('c1234', None)
        ok_(cmd_checker1.runned is True)
        ok_(cmd_checker2.runned is True)
        ok_(cmd_checker1.cmd == 'c1234')
        ok_(cmd_checker2.cmd == 'c1234')
