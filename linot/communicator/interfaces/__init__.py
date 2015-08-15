import pkgutil
import os
from linot import logger
logger = logger.getLogger(__name__)


interface_folder = os.path.dirname(os.path.abspath(__file__))
for importer, mod_name, _ in pkgutil.iter_modules([interface_folder]):
    if mod_name.endswith('interface'):
        importer.find_module(mod_name).load_module(mod_name)
