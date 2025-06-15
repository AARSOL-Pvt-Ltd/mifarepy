import logging
import serial
import struct
from typing import Optional, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InvalidMessage(Exception):
    """Raised when an invalid message is received from the RFID reader."""
    pass


class GNetPlusError(Exception):
    """
    Exception thrown when receiving a NAK (negative acknowledge) response.
    """
    pass


def gencrc(msg_bytes: bytes) -> int:
    """
    Generate a 16-bit CRC checksum.

    @param msg_bytes: bytes containing message for checksum
    @returns 16-bit integer containing CRC checksum
    """
    crc = 0xFFFF

    for byte in msg_bytes:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else crc >> 1

    return crc


class Message(object):
    """
    Base class representing a message for the RFID reader.
    """

    SOH = 0x01  # Start of Header

    def __init__(self, address: int, function: int, data: Union[bytes, str]):
        """
        Initialize a message.

        @param address: 8-bit device address (use 0 unless specified).
        @param function: 8-bit function code representing the message type.
        @param data: Message payload (bytes or string).
        """
        self.address = address
        self.function = function
        self.data = data.encode('latin1') if isinstance(data, str) else data

    def __bytes__(self) -> bytes:
        """
        Converts Message to raw binary form suitable for transmission.

        @return: Bytes representation of the message.
        """
        msg_bytes = struct.pack('BBB', self.address, self.function, len(self.data)) + self.data
        crc = gencrc(msg_bytes)

        return bytes([self.SOH]) + msg_bytes + struct.pack('>H', crc)

    def __str__(self) -> str:
        """
        Returns hex representation of the message.

        @return: Hexadecimal string representation.
        """
        return self.__bytes__().hex()

    def __repr__(self) -> str:
        return f'Message(address={hex(self.address)}, function={hex(self.function)}, data={self.data!r})'

    def sendto(self, serial_port):
        """
        Sends this message to the provided serial port.

        @param serial_port: Serial port to send the message.
        """
        serial_port.write(bytes(self))

    @classmethod
    def readfrom(cls, serial_port: serial.Serial):
        """
        Reads a message from the serial port and constructs a Message instance.

        @param serial_port: Serial interface to read from.
        @return: Constructed Message instance.
        @raises InvalidMessage: If message is incomplete or invalid.
        """
        header = serial_port.read(4)

        if len(header) < 4:
            raise InvalidMessage('Incomplete header')

        soh, address, function, length = struct.unpack('BBBB', header)

        if soh != cls.SOH:
            raise InvalidMessage('SOH does not match')

        data = serial_port.read(length)
        crc = serial_port.read(2)
        if len(data) < length or len(crc) < 2:
            raise InvalidMessage('Incomplete data or CRC')

        msg = cls(address=address, function=function, data=data)
        if bytes(msg)[-2:] != crc:
            raise InvalidMessage('CRC does not match')

        return msg


class QueryMessage(Message):
    """
    A query message to be sent from host machine to card reader device. Magical constants taken from protocol documentation.
    """
    POLLING = 0x00
    GET_VERSION = 0x01
    SET_SLAVE_ADDR = 0x02
    LOGON = 0x03
    LOGOFF = 0x04
    SET_PASSWORD = 0x05
    CLASSNAME = 0x06
    SET_DATETIME = 0x07
    GET_DATETIME = 0x08
    GET_REGISTER = 0x09
    SET_REGISTER = 0x0A
    RECORD_COUNT = 0x0B
    GET_FIRST_RECORD = 0x0C
    GET_NEXT_RECORD = 0x0D
    ERASE_ALL_RECORDS = 0x0E
    ADD_RECORD = 0x0F
    RECOVER_ALL_RECORDS = 0x10
    DO = 0x11
    DI = 0x12
    ANALOG_INPUT = 0x13
    THERMOMETER = 0x14
    GET_NODE = 0x15
    GET_SN = 0x16
    SILENT_MODE = 0x17
    RESERVE = 0x18
    ENABLE_AUTO_MODE = 0x19
    GET_TIME_ADJUST = 0x1A
    ECHO = 0x18
    SET_TIME_ADJUST = 0x1C
    DEBUG = 0x1D
    RESET = 0x1E
    GO_TO_ISP = 0x1F
    REQUEST = 0x20
    ANTI_COLLISION = 0x21
    SELECT_CARD = 0x22
    AUTHENTICATE = 0x23
    READ_BLOCK = 0x24
    WRITE_BLOCK = 0x25
    SET_VALUE = 0x26
    READ_VALUE = 0x27
    CREATE_VALUE_BLOCK = 0x28
    ACCESS_CONDITION = 0x29
    HALT = 0x2A
    SAVE_KEY = 0x2B
    GET_SECOND_SN = 0x2C
    GET_ACCESS_CONDITION = 0x2D
    AUTHENTICATE_KEY = 0x2E
    REQUEST_ALL = 0x2F
    SET_VALUEEX = 0x32
    TRANSFER = 0x33
    RESTORE = 0x34
    GET_SECTOR = 0x3D
    RF_POWER_ONOFF = 0x3E
    AUTO_MODE = 0x3F


class ResponseMessage(Message):
    """
    Message received from the RFID reader.
    """
    ACK = 0x06  # Acknowledge
    NAK = 0x15  # Negative Acknowledge
    EVN = 0x12  # Event Notification

    def to_error(self) -> Optional[GNetPlusError]:
        """
        Convert a NAK response into a GNetPlusError.

        @returns Constructed instance of GNetPlusError for this response
        """
        if self.function == self.NAK:
            return GNetPlusError(f'Error: {repr(self.data)}')

        return None
