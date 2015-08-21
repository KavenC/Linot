import io
import sys
from threading import Lock

from line import LineClient
from line import LineContact

from linot import config
from linot import logger
from linot.base_interface import BaseInterface
from linot.command_submitter import CommandSubmitter
logger = logger.get().getLogger(__name__)


class LineClientP(LineClient):
    """Patch for Line package cert issue"""

    def __init__(self, acc, pwd):
        super(LineClientP, self).__init__(acc, pwd, com_name="LinotMaster")
        self.lock = Lock()

    def ready(self):
        f = open(self.CERT_FILE, 'r')
        self.certificate = f.read()
        f.close()
        return

    def find_contact_by_id(self, userid):
        contacts = self._getContacts([userid])
        if len(contacts) == 0:
            raise ValueError('getContacts from server failed, id:' + str(userid))
        return LineContact(self, contacts[0])


class LineInterface(BaseInterface):
    NAME = 'line'
    SERVER = True

    def __init__(self):
        self._client = LineClientP(
            config['interface']['line']['account'],
            config['interface']['line']['password']
        )
        logger.debug('log-in done.')
        self._client.updateAuthToken()
        logger.debug('update auth done.')

    def polling_command(self):
        # hide longPoll debug msg
        org_stdout = sys.stdout
        sys.stdout = io.BytesIO()
        self._client.lock.acquire(True)
        ge = self._client.longPoll()
        op_list = []
        for op in ge:
            op_list.append(op)
        self._client.lock.release()
        sys.stdout = org_stdout

        # construct formal command list
        command_list = []
        for op in op_list:
            submitter = CommandSubmitter(self.NAME, op[0].id)
            command_list.append((submitter, op[2].text))
        return command_list

    def send_message(self, receiver, msg):
        assert receiver.interface_name == self.NAME
        self._send_message_to_id(receiver.code, msg)

    def get_display_name(self, submitter):
        contact = self._get_contact_by_id(submitter.code)
        return contact.name

    def _get_contact_by_id(self, id):
        self._client.lock.acquire(True)
        contact = self._client.find_contact_by_id(id)
        self._client.lock.release()
        return contact

    def _send_message_to_id(self, recvr_id, msg):
        recvr = self._get_contact_by_id(recvr_id)
        self._client.lock.acquire(True)
        recvr.sendMessage(msg)
        self._client.lock.release()
