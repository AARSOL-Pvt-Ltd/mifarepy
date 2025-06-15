class InvalidMessage(Exception):
    """Raised when an invalid message is received from the RFID reader."""
    pass


class GNetPlusError(Exception):
    """
    Exception thrown when receiving a NAK (negative acknowledge) response.
    """
    pass
