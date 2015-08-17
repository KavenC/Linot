import threading
import re
import argparse

from nose.tools import ok_
from nose.tools import timed

from linot.arg_parser import LinotArgParser, LinotParser
from linot import command_server
import linot.interfaces as interfaces
from linot.command_submitter import CommandSubmitter


class fakeMessage:
    def __init__(self, msg):
        self.text = msg


class mock_engine:
    def __init__(self):
        self.test_list = []
        self.test_case_idx = 0
        self.test_case_lock = threading.Lock()
        self.test_finished = threading.Event()
        self.test_finished.clear()

    def _case_done(self):
        self.test_case_lock.acquire(True)
        self.test_case_idx += 1
        self.test_case_lock.release()

    def addTest(self, cmd_list, cmd_checker, msg_checker):
        self.test_list.append([cmd_list, cmd_checker, msg_checker])

    def longPoll(self):
        self.test_case_lock.acquire(True)
        if self.test_case_idx < len(self.test_list):
            ret = self.test_list[self.test_case_idx][0]
        else:
            self.test_finished.set()
            ret = []
        self.test_case_lock.release()
        return ret

    def sendMessageToClient(self, recv, msg):
        ok_(self.test_case_idx < len(self.test_list))
        callback = self.test_list[self.test_case_idx][2]
        if callback is not None:
            callback(recv, msg, self._case_done)

    def cmdProcess(self, args, sender):
        ok_(self.test_case_idx < len(self.test_list))
        callback = self.test_list[self.test_case_idx][1]
        if callback is not None:
            callback(args, sender, self._case_done)


class CmdTester:
    def __init__(self, test_if_name):
        self.if_name = test_if_name
        self.senders = []
        self.cmd_checkers = []
        self.msg_checkers = []
        self.total_test_count = 0

    def add_test(self, test_list):
        for sender_code, cmd, cmd_chk, msg_chk in test_list:
            sender = CommandSubmitter(sender_code, self.if_name)
            interfaces.get(self.in_name).add_command(sender, cmd)
            self.senders[self.total_test_count] = sender
            self.cmd_checkers[self.total_test_count] = cmd_chk
            self.msg_checkers[self.total_test_count] = msg_chk
            self.total_test_count += 1

    def cmd_process(self, args, sender):
        if self.cmd_checker is not None:
            self.cmd_checker(args, sender)


class TestCmdServer:
    def setUp(self):
        parser = LinotParser(usage=argparse.SUPPRESS, add_help=False)
        self.parser = parser

    def test_cmd_process(self):
        # test command server can properly handle 1 or multiple commands
        def default_process(args, sender):
            ok_(getattr(args, sender.code) is True)
            default_process.called += 1

        lap = LinotArgParser('testcmd', self.parser, default_process)
        lap.add_argument('-a', action='store_true')
        lap.add_argument('-b', action='store_true')
        lap.add_argument('-c', action='store_true')

        # Test 1 cmd return by polling_command
        # command = [(sender, cmd string), ...]
        sender = CommandSubmitter('test', 'a')
        fake_cmd = [(sender, 'testcmd -a')]
        interfaces.get('test').add_command_list(fake_cmd)
        default_process.called = 0
        command_server.start(self.parser, ['test'])
        threading.Event().wait(.5)
        command_server.stop()
        ok_(default_process.called == 1)

        # Test 3 cmds return by polling_command
        # command = [(sender, cmd string), ...]
        sender_a = CommandSubmitter('test', 'a')
        sender_b = CommandSubmitter('test', 'b')
        sender_c = CommandSubmitter('test', 'c')
        fake_cmd = [
            (sender_a, 'testcmd -a'),
            (sender_b, 'testcmd -b'),
            (sender_c, 'testcmd -c'),
        ]
        interfaces.get('test').add_command_list(fake_cmd)
        command_server.start(self.parser, ['test'])
        default_process.called = 0
        threading.Event().wait(.5)
        command_server.stop()
        ok_(default_process.called == 3)

    @timed(10)
    def test_unknown_commands(self):
        # test command server can properly handle 1 or multiple commands
        def default_process(args, sender):
            ok_(getattr(args, sender.code) is True)
            default_process.called += 1

        lap = LinotArgParser('testcmd', self.parser, default_process)
        lap.add_argument('-a', action='store_true')
        lap.add_argument('-b', action='store_true')
        lap.add_argument('-c', action='store_true')

        # Test 1 unknown command, command server respose to user
        sender_a = CommandSubmitter('test', 'a')
        fake_cmd = [
            (sender_a, 'some_unknown_words'),
        ]
        interfaces.get('test').reset()
        interfaces.get('test').add_command_list(fake_cmd)
        command_server.start(self.parser, ['test'])
        default_process.called = 0
        threading.Event().wait(.5)
        command_server.stop()
        ok_(default_process.called == 0)
        ok_('Unknown' in ' '.join(interfaces.get('test').msg_queue[sender_a.code]))

        # Test multiple unknown commands
        sender_a = CommandSubmitter('test', 'a')
        sender_u = CommandSubmitter('test', 'u')
        fake_cmd = [
            (sender_u, 'some_unknown_cmds'),
            (sender_a, 'testcmd -a'),
            (sender_u, 'some_unknown_cmds'),
        ]
        interfaces.get('test').reset()
        interfaces.get('test').add_command_list(fake_cmd)
        command_server.start(self.parser, ['test'])
        default_process.called = 0
        threading.Event().wait(.5)
        command_server.stop()
        unknown_response = ' '.join(interfaces.get('test').msg_queue[sender_u.code])
        ok_(unknown_response.count('Unknown') == 2)
        ok_(default_process.called == 1)

    def test_direct_command(self):
        def default_process(args, sender):
            ok_(False)  # should not reach here

        lap = LinotArgParser('testcmd', self.parser, default_process)

        def cmd_checker(match_list, cmd, sender):
            ok_('somechannel' in match_list)
            ok_(len(match_list) == 1)
            ok_(cmd == 'www.twitch.tv/somechannel')
            cmd_checker.runned = True
        lap.add_direct_command(cmd_checker, 'twitch\.tv/(\w+)[\s\t,]*', re.IGNORECASE)
        cmd_checker.runned = False

        sender = CommandSubmitter('test', 'sender')
        fake_cmd = [
            (sender, 'www.twitch.tv/somechannel')
        ]
        interfaces.get('test').add_command_list(fake_cmd)
        command_server.start(self.parser, ['test'])
        threading.Event().wait(.5)
        command_server.stop()
        ok_(cmd_checker.runned)

    def test_stop(self):
        command_server.start(self.parser)
        for server in command_server.server_threads:
            server.stop()
            ok_(server.is_alive() is not True)
