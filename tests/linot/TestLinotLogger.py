import sys
from io import BytesIO
from nose.tools import ok_


class TestLinotLogger:
    def testLogToStdout(self):
        from linot.LinotLogger import logging
        import linot.LinotLogger
        test_str = 'testtesttest'
        bkout = sys.stdout
        sys.stdout = cap = BytesIO()
        reload(linot.LinotLogger)
        logging.config.dictConfig(linot.LinotLogger.config)
        self.logger = logging.getLogger(__name__)
        self.logger.debug(test_str)
        sys.stdout = bkout
        reload(linot.LinotLogger)
        logging.config.dictConfig(linot.LinotLogger.config)
        cap_text = cap.getvalue()
        ok_(test_str in cap_text, True)
