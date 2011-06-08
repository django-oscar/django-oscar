from logging import Formatter
import re


class PciFormatter(Formatter):
    """
    Strip card numbers out of log messages to avoid leaving sensitive information
    in the logs.
    """
    
    def format(self, record):
        s = Formatter.format(self, record)
        return re.sub(r'\d[ \d-]{15,22}', 'XXXX-XXXX-XXXX-XXXX', s)
        