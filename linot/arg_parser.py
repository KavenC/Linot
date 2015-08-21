# -*- coding: utf-8 -*-
"""Argument Parser for Linot input commands

This modules rewrites or extends functions of `argparse` in the Python
Starndard Library. It simplifies the command interface so that services
can be developed without worrying about the complexity of user inputs

"""

from __future__ import print_function
from argparse import SUPPRESS, ArgumentParser
import re
from io import BytesIO

import logger
logger = logger.get().getLogger(__name__)


class LinotParser(ArgumentParser):
    """Extends the usibility of ArgumentParser

    Attributes:
        (same with ArgumentParser in standard library)

    """
    def __init__(self, *args, **kwargs):
        ArgumentParser.__init__(self, *args, **kwargs)
        self._sub_parser = None
        self._direct_commands = []

    def get_sub_parser(self):
        if self._sub_parser is None:
            self._sub_parser = self.add_subparsers()
        return self._sub_parser

    def add_direct_command(self, func, pattern, flags=0):
        self._direct_commands.append([func, pattern, flags])

    def process_direct_commands(self, cmd, sender):
        matched = False
        for direct_command in self._direct_commands:
            match_list = re.findall(direct_command[1], cmd, direct_command[2])
            if len(match_list) > 0:
                matched = True
                direct_command[0](match_list, cmd, sender)
        return matched


class LinotArgParser:
    def __init__(self, subcmd, parser, default_process):
        self._parser = parser
        sub_cmd_parser = parser.get_sub_parser()
        ap = sub_cmd_parser.add_parser(subcmd, add_help=False)
        self._sub_parser = ap.add_mutually_exclusive_group()
        self._subcmd = subcmd
        self._default_process = default_process
        self._arg_list = {}
        self._sub_parser.set_defaults(proc=self._process_args)
        self.add_argument('-h', '--help',  action='store_true', func=self.print_help, help='show command list')

    def add_direct_command(self, func, pattern, flags=0):
        # Add direct command parsing rule (re) and the callback function
        # if parser cannot find any known command in the input string
        # it starts match the pattern in the direct command list for input
        # All the funcs of the matching pattern will be called
        self._parser.add_direct_command(func, pattern, flags)

    def add_argument(self, *args, **kwargs):
        # Limit some funtions of argparse.add_argument
        # make argument bind with callback on add
        if 'dest' in kwargs:
            raise ValueError('"dest" is forbidden for plugin argument')
        if 'func' in kwargs:
            func = kwargs['func']
            kwargs.pop('func')
        else:
            func = None
        for arg_str in args:
            # we dont accept positional args
            if not arg_str.startswith(self._sub_parser.prefix_chars):
                raise ValueError('supports only optional args starts with ' +
                                 self._sub_parser.prefix_chars)
            option = arg_str.lstrip(self._sub_parser.prefix_chars)
            self._arg_list[option] = {}
            self._arg_list[option]['func'] = func
            self._arg_list[option]['arg'] = arg_str
            if 'help' in kwargs:
                self._arg_list[option]['help'] = kwargs['help']
            else:
                self._arg_list[option]['help'] = ''
        self._sub_parser.add_argument(*args, **kwargs)

    def _process_args(self, input_args, sender):
        for args in self._arg_list:
            value = getattr(input_args, args, None)
            if value is not None and value is not False:
                func = self._arg_list[args]['func']
                if func is not None:
                    func(getattr(input_args, args), sender)
                else:
                    self._default_process(input_args, sender)
                return  # we assume that there will be only 1 argument each time

        # this call indicates that there are no known arguments
        # default process can handle this by determine if args is None
        self._default_process(None, sender)

    def print_help(self, args, sender=None):
        msg = BytesIO()
        print('[{} command list]'.format(self._subcmd), file=msg)
        # TODO fix this ....
        print('{} {}'.format(self._subcmd, '-h/--help'), file=msg)
        print('>> show this command list.', file=msg)
        print('--------------', file=msg)
        for arg in self._arg_list:
            if self._arg_list[arg]['help'] is SUPPRESS:
                continue
            if arg == 'help' or arg == 'h':
                continue
            help_text = self._arg_list[arg]['help']
            print('{} {}'.format(self._subcmd, self._arg_list[arg]['arg']), file=msg)
            if help_text != '':
                print('>> '+help_text, file=msg)
            print('--------------', file=msg)
        if sender is not None:
            sender.send_message(msg.getvalue())
