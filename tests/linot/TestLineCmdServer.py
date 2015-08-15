from linot.LineCmdServer import LineCmdServer
from linot.LinotArgParser import LinotArgParser, LinotParser
import argparse
from nose.tools import ok_
from nose.tools import timed
import threading
import re


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


class TestLineCmdServer:
    def setUp(self):
        parser = LinotParser(usage=argparse.SUPPRESS, add_help=False)
        sub_cmd_parser = parser.get_sub_parser()
        self.sub_parser = sub_cmd_parser
        self.parser = parser

    def tearDown(self):
        self.cmd_server.stop()
        self.cmd_server = None

    @timed(10)
    def testCmdProcess_Normal(self):
        mock = mock_engine()
        lap = LinotArgParser('testcmd', self.parser, mock.cmdProcess, None)
        lap.add_argument('-a', action='store_true')
        lap.add_argument('-b', action='store_true')
        self.cmd_server = LineCmdServer(mock, self.parser)

        # Test 1 cmd in op_list
        fake_cmd = [
            [True, None, fakeMessage('testcmd -a')]
        ]

        def cmdChecker_1(args, sender, done):
            ok_(args.a)
            ok_(sender)
            done()
        mock.addTest(fake_cmd, cmdChecker_1, None)

        # Test 2 cmds in op_list
        fake_cmd = [
            [True, None, fakeMessage('testcmd -a')],
            [True, None, fakeMessage('testcmd -b')],
        ]

        def cmdChecker_2(args, sender, done):
            ok_(args.a or args.b)
            if args.a:
                cmdChecker_2.var += 'a'
            if args.b:
                cmdChecker_2.var += 'b'
            if cmdChecker_2.var == 'ab':
                done()
            elif len(cmdChecker_2.var) >= 2:
                ok_(False)
        cmdChecker_2.var = ''
        mock.addTest(fake_cmd, cmdChecker_2, None)
        self.cmd_server.start()
        mock.test_finished.wait(10)
        self.cmd_server.stop()
        self.cmd_server.join(10)
        ok_(not self.cmd_server.isAlive())

    @timed(10)
    def testCmdProcess_Unknown(self):
        mock = mock_engine()
        lap = LinotArgParser('testcmd', self.parser, mock.cmdProcess, None)
        lap.add_argument('-a', action='store_true')
        self.cmd_server = LineCmdServer(mock, self.parser)

        def cmdChecker(args, sender, done):
            ok_(sender)
            ok_(args.a)
            cmdChecker.testpass = True

        def msgChecker(recv, msg, done):
            ok_(recv == 'sender')
            ok_('Unknown' in msg)
            msgChecker.passtime += 1
            if msgChecker.passtime == 2:
                done()

        cmdChecker.testpass = False
        msgChecker.passtime = 0
        fake_cmd = [
            ['sender', None, fakeMessage('some_unknown_cmds')],
            [True, None, fakeMessage('testcmd -a')],
            ['sender', None, fakeMessage('some_unknown_cmds')],
        ]
        mock.addTest(fake_cmd, cmdChecker, msgChecker)
        self.cmd_server.start()
        mock.test_finished.wait(10)
        ok_(cmdChecker.testpass)
        self.cmd_server.stop()
        self.cmd_server.join(10)
        ok_(self.cmd_server.stopped())
        ok_(not self.cmd_server.isAlive())

    def test_direct_command(self):
        mock = mock_engine()
        lap = LinotArgParser('testcmd', self.parser, mock.cmdProcess, None)

        def cmd_checker(match_list, cmd, sender):
            ok_('somechannel' in match_list)
            ok_(len(match_list) == 1)
            ok_(cmd == 'www.twitch.tv/somechannel')
            cmd_checker.runned = True
        cmd_checker.runned = False
        lap.add_direct_command(cmd_checker, 'twitch\.tv/(\w+)[\s\t,]*', re.IGNORECASE)
        self.cmd_server = LineCmdServer(mock, self.parser)
        fake_cmd = [
            ['sender', None, fakeMessage('www.twitch.tv/somechannel')],
        ]
        mock.addTest(fake_cmd, None, None)
        self.cmd_server.start()
        mock.test_finished.wait(10)
        ok_(cmd_checker.runned)
        self.cmd_server.stop()
