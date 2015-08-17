import pkgutil
import os
import inspect

from linot.base_interface import BaseInterface
from linot import logger
logger = logger.getLogger(__name__)

class_dict = {}
instance_dict = {}


def get(key):
    if key in class_dict and key not in instance_dict:
        instance_dict[key] = class_dict[key]()
    return instance_dict[key]


def avail():
    return class_dict.keys()


def find_and_import_interface_class(ifmod):
    for name, obj in inspect.getmembers(ifmod):
        if inspect.isclass(obj) and issubclass(obj, BaseInterface) and obj.NAME is not None:
            logger.debug('Found interface class: ' + str(obj))
            if obj.NAME in class_dict:
                raise NameError('Interface name conflict: '.format(class_dict[obj.NAME], obj))
            else:
                class_dict[obj.NAME] = obj

interface_folder = os.path.dirname(os.path.abspath(__file__))
for importer, mod_name, _ in pkgutil.iter_modules([interface_folder]):
    if mod_name.endswith('interface'):
        ifmod = importer.find_module(mod_name).load_module(mod_name)
        find_and_import_interface_class(ifmod)
