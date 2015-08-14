from __future__ import print_function
import LineEngine
import LineCmdServer
from LinotConfig import LinotConfig as Config
import argparse
import Plugins
from LinotArgParser import LinotArgParser, LinotParser
from LinotLogger import logging
logger = logging.getLogger(__name__)


def CmdProcess(args, sender):
    if args.stopserver:
        if sender.id == Config['admin_id']:
            line_eng.sendMessageToClient(sender, 'Server is shutting down')
            logger.info('server is shutting down')
            for plugin in PluginInstance:
                logger.debug('stopping plugin: '+plugin)
                PluginInstance[plugin].stop()
                logger.debug(plugin + ' is stopped')
            logger.debug('stopping command server')
            line_cmd_server.stop()
        return

    if args.listservices:
        for plugin in PluginInstance:
            line_eng.sendMessageToClient(sender, PluginInstance[plugin].CMD_PREFIX)
        return

# LINE chat bot start-up
line_eng = LineEngine.LineEngine()

# Add common commands
parser = LinotParser(usage=argparse.SUPPRESS, add_help=False)
cmd_group = LinotArgParser('linot', parser, CmdProcess, line_eng)
cmd_group.add_argument('-stopserver', action='store_true', help=argparse.SUPPRESS)
# cmd_group.add_argument('-backup', action='store_true', help=argparse.SUPPRESS)
# cmd_group.add_argument('-listbackups', action='store_true', help=argparse.SUPPRESS)
# cmd_group.add_argument('-restore', help=argparse.SUPPRESS)
cmd_group.add_argument('-listservices', action='store_true', help='Show installed services')

line_cmd_server = LineCmdServer.LineCmdServer(line_eng, parser)
line_cmd_server.start()

# Load plugins
PluginInstance = {}
for plugin in Plugins.List:
    logger.info('Loading Plugin: '+plugin)
    plugin_instance = Plugins.List[plugin].Plugin(line_eng)
    plugin_instance.setup(parser)
    PluginInstance[plugin] = plugin_instance
    plugin_instance.start()
