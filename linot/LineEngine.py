from __future__ import print_function
from line import LineClient
from line import LineContact
from LinotConfig import LinotConfig as Config
from threading import Lock
from linot.LinotLogger import logging
logger = logging.getLogger(__name__)


class LineClientP(LineClient):
    """
    Patch for Line package cert issue
    """
    def __init__(self, acc, pwd):
        super(LineClientP, self).__init__(acc, pwd, com_name="LinotMaster")
        self.lock = Lock()

    def ready(self):
        f = open(self.CERT_FILE, 'r')
        self.certificate = f.read()
        f.close()
        return

    def findContactById(self, userid):
        contacts = self._getContacts([userid])
        if len(contacts) == 0:
            raise Exception('getContacts from server failed, id:'+str(userid))
        return LineContact(self, contacts[0])


class LineEngine:
    def __init__(self):
        self._client = LineClientP(
            Config['line_account'],
            Config['line_password']
            )
        logger.debug('LINE log-in done.')
        self._client.updateAuthToken()
        logger.debug('UpdateAuthToken done.')

    def longPoll(self):
        self._client.lock.acquire(True)
        # hide longPoll debug msg
        import io
        import sys
        org_stdout = sys.stdout
        sys.stdout = io.BytesIO()
        ge = self._client.longPoll()
        op_list = []
        for op in ge:
            op_list.append(op)
        sys.stdout = org_stdout
        self._client.lock.release()
        return op_list

    def getContactById(self, id):
        self._client.lock.acquire(True)
        contact = self._client.findContactById(id)
        self._client.lock.release()
        return contact

    def sendMessageToClient(self, recvr_client, msg):
        self._client.lock.acquire(True)
        recvr_client.sendMessage(msg)
        self._client.lock.release()

    def sendMessageToId(self, recvr_id, msg):
        recvr = self.getContactById(recvr_id)
        self._client.lock.acquire(True)
        recvr.sendMessage(msg)
        self._client.lock.release()
