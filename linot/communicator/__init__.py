import command_server
import interfaces  # noqa


def start(arg_parser):
    """Start command receiving thread"""
    command_server.start(arg_parser)
    pass


def stop(wait=True):
    """Stop command receiving thread"""
    command_server.stop()
    pass
