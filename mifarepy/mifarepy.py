# mifarepy -- Python library for interfacing with PROMAG RFID card reader
# Adapted from https://github.com/harishpillay/gnetplus (initially in Python 2)
#
# Authors:
#     Original: Chow Loong Jin <lchow@redhat.com>
#     Original: Harish Pillay <hpillay@redhat.com>
#     Adapted by: Spark Drago <https://github.com/SparkDrago05>
#
# This library is released under the GNU Lesser General Public License v3.0 or later.
# See the LICENSE file for more details.


"""
mifarepy: A Python library for interfacing with the PROMAG RFID card reader
using the GNetPlus® protocol.

Features:
- Communicates via serial interface (`pyserial`).
- Supports various RFID commands (get serial number, read/write blocks, etc.).
- Includes error handling for invalid messages and device errors.

Example:
    from mifarepy import Handle

    handle = Handle('/dev/ttyUSB0')
    print('S/N:', handle.get_sn(endian='little', as_string=True))

License:
    GNU Lesser General Public License v2.1 or later
"""

import logging
import serial
import struct
import sys
import time
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
        crc = self.gencrc(msg_bytes)

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

    @staticmethod
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
    WRITE_BLOCk = 0x25
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


class Handle(object):
    """
    Class for interfacing with the RFID card reader.
    """

    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 19200, deviceaddr: int = 0, **kwargs):
        """
        Initialize the RFID reader connection.

        @params port: Serial port name (e.g., '/dev/ttyUSB0').
        @params baudrate: Baudrate for interfacing with the device. Don't change this unless you know what you're doing.
        @params deviceaddr: Device address (default: 0).
        """
        self.port = port
        self.baudrate = baudrate
        self.deviceaddr = deviceaddr

        try:
            self.serial = serial.Serial(port, baudrate=baudrate, **kwargs)
        except serial.SerialException as pe:
            raise RuntimeError(f'Unable to open port {port}: {pe}')

    def sendmsg(self, function: int, data: bytes = b'') -> None:
        """
        Constructs and sends a QueryMessage to the RFID reader.

        @param function: @see Message.function
        @param data: @see Message.data
        """
        QueryMessage(self.deviceaddr, function, data).sendto(self.serial)

    def readmsg(self, sink_events: bool = False) -> ResponseMessage:
        """
        Reads a message, optionally ignoring event (EVN) messages which are
        device-driven.

        @param sink_events Boolean dictating whether events should be ignored.
        @returns: Constructed ResponseMessage instance.
        @raises GNetPlusError: If a NAK response is received.
        """
        while True:
            response = ResponseMessage.readfrom(self.serial)

            # skip over events. spec doesn't say what to do with them
            if sink_events and response.function == ResponseMessage.EVN:
                continue

            break

        if response.function == ResponseMessage.NAK:
            raise response.to_error()

        return response

    def get_sn(self, endian: str = 'little', as_string: bool = True) -> Union[str, int]:
        """
        Get the serial number of the card currently scanned.

        @param endian: 'big' or 'little'. Specifies how to interpret the 4-byte UID.
                       For example, if the raw response data is b'\xE3\x0E\x27\x0E':
                           - 'big' interprets it as 0xE30E270E.
                           - 'little' interprets it as 0x0E270EE3.
        @param as_string: If True, returns the UID as a formatted hexadecimal string (with leading zeros preserved);
                          otherwise, returns the UID as an integer.
        @returns: The 16-byte serial number of the card currently scanned.
        """
        self.sendmsg(QueryMessage.REQUEST)
        self.readmsg(sink_events=True)

        self.sendmsg(QueryMessage.ANTI_COLLISION)
        response = self.readmsg(sink_events=True)

        uid = struct.unpack('>L' if endian == 'big' else '<L', response.data)[0]

        return f'0x{uid:08X}' if as_string else uid

    def get_version(self) -> bytes:
        """
        Get product version string. May contain null bytes, so be careful when using it.

        @returns Product version string of the device connected to this handle.
        """
        self.sendmsg(QueryMessage.GET_VERSION)
        return self.readmsg().data

    def set_auto_mode(self, enabled: bool = True) -> bytes:
        """
        Toggle auto mode, i.e. whether the device emits events when a card comes close.
        After setting verify the change.

        @arg enabled Whether to enable or disable auto mode.
        """
        mode = b'\x01' if enabled else b'\x00'
        self.sendmsg(QueryMessage.AUTO_MODE, mode)
        response = self.readmsg(sink_events=True)

        if response.data != mode:
            raise GNetPlusError('Failed to set auto mode')
        return response.data

    def wait_for_card(self, timeout: int = 10) -> Optional[str]:
        """
        Check if a card is already present. If not, wait for an event.

        @param timeout: Maximum time to wait in seconds (default: 10).
        @return: Card serial number if found, else None.
        @raises TimeoutError: If no card is detected within the timeout.
        """
        self.set_auto_mode()

        try:
            card_sn = self.get_sn(as_string=True)
            if card_sn:
                logger.info(f'Card already present: {card_sn}')
                return card_sn  # Exit early if a card is already present
        except GNetPlusError:
            pass  # Ignore errors, we'll wait for the card event

        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.readmsg()
            if response.function == ResponseMessage.EVN and b'I' in response.data:
                logger.info(f'Card detected!')
                return self.get_sn(as_string=True)

            time.sleep(0.1)

        raise TimeoutError('No card detected within the time limit')


if __name__ == '__main__':
    try:
        port = '/dev/ttyUSB0'
    except IndexError:
        sys.stderr.write('Usage: {0} <serial port>, example /dev/ttyUSB0\n'.format(sys.argv[0]))
        sys.exit(1)

    handle = Handle(port)

    handle.wait_for_card()

    try:
        # Example: choose little-endian output as a formatted hex string.
        print('Little endian format as string')
        print('Found card: {0}'.format(handle.get_sn(endian='little', as_string=True)))
        # Example: choose big-endian output as an integer.
        print('Big endian format as integer')
        print('Found card: {0}'.format(handle.get_sn(endian='big', as_string=False)))
    except GNetPlusError:
        print('Tap card again.')
