# mifarepy -- Python library for interfacing with PROMAG RFID card reader
# Adapted from https://github.com/harishpillay/gnetplus (initially in Python 2)
#
# Authors:
#     Original: Chow Loong Jin <lchow@redhat.com>
#     Original: Harish Pillay <hpillay@redhat.com>
#     Adapted by: Spark Drago <https://github.com/SparkDrago05>
#
# This library is released under the GNU Lesser General Public License v3.0 or later.
# See the LICENCE file for more details.


"""
mifarepy: A Python library for interfacing with the PROMAG RFID card reader
using the GNetPlus® protocol.

Features:
- Communicates via serial interface (`pyserial`).
- Supports various RFID commands (get serial number, read/write blocks, etc.).
- Includes error handling for invalid messages and device errors.

Example:
    from mifarepy import MifareReader

    Reader = MifareReader('/dev/ttyUSB0')
    print('S/N:', reader.get_sn(endian='little', as_string=True))

License:
    GNU Lesser General Public Licence v3.0 or later
"""

import logging
import serial
import struct
import sys
import time
from typing import Optional, Union, List, Dict
from .protocol import QueryMessage, ResponseMessage, GNetPlusError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MifareReader:
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

    def get_version(self) -> str:
        """
        Get product version string. May contain null bytes, so be careful when using it.

        @returns Product version string of the device connected to this handle.
        """
        self.sendmsg(QueryMessage.GET_VERSION)
        response = self.readmsg().data
        # Decode the version data; ignore decode errors if non-text bytes appear
        return response.decode('latin1', errors='ignore').strip()

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

    def authenticate_sector(self, sector: int, key: bytes, key_type: str = 'A', timeout: float = 1.0, flush: bool = True) -> None:
        """
        Load a key into the reader and authenticate the specified MIFARE Classic sector.

        @param sector: Sector number to authenticate (e.g., 0-15).
        @param key: 6-byte key for authentication.
        @param key_type: 'A' for Key A (0x60) or 'B' for Key B (0x61).
        @param timeout: Timeout in seconds for reader responses.
        @param flush: Whether to flush the input buffer before reading responses.
        @raises ValueError: If key_type is invalid or key length is not 6 bytes.
        @raises GNetPlusError: If the reader returns a NAK during key load or authentication.
        """
        # Validate inputs
        if key_type not in ('A', 'B'):
            raise ValueError('key_type must be \'A\' or \'B\'')
        if len(key) != 6:
            raise ValueError('key must be exactly 6 bytes long')

        # Determine authentication code for key type
        auth_code = 0x60 if key_type == 'A' else 0x61

        # Load the key into the reader
        # Data format: [KeyTypeCode, SectorNumber] + KeyBytes
        payload = bytes([auth_code, sector]) + key
        self.sendmsg(QueryMessage.SAVE_KEY, payload)
        # Optionally flush input buffer to clear residual data
        if flush:
            try:
                self.serial.reset_input_buffer()
            except AttributeError:
                pass
        # Short delay to allow reader processing
        time.sleep(0.05)

        # Temporarily adjust serial timeout for key load response
        orig_timeout = getattr(self.serial, 'timeout', None)
        self.serial.timeout = timeout
        try:
            self.readmsg()  # Raises GNetPlusError on failure
        finally:
            self.serial.timeout = orig_timeout

        # Authenticate the sector using the loaded key
        # Data format: [KeyTypeCode, SectorNumber]
        payload = bytes([auth_code, sector])
        self.sendmsg(QueryMessage.AUTHENTICATE, payload)
        # Temporarily adjust serial timeout for authentication
        orig_timeout = getattr(self.serial, 'timeout', None)
        self.serial.timeout = timeout
        try:
            self.readmsg()  # Raises GNetPlusError on failure
        finally:
            self.serial.timeout = orig_timeout

    def read_block(self, block: int, raw: bool = False) -> bytes:
        """
        Read a single 16-byte block from the card.

        @param block: Block number (block_index relative to authenticated sector, 0-3).
        @param raw: If True, returns bytes. If False, returns hex string.
        @return: Block data in bytes or hex string format.
        @raises GNetPlusError: If the read fails.
        """
        self.sendmsg(QueryMessage.READ_BLOCK, bytes([block]))
        response = self.readmsg()
        return response.data if raw else response.data.hex()

    def write_block(self, block: int, data: Union[str, bytes]) -> bytes:
        """
        Write a 16-byte block to the card.

        @param block: Block number (block_index relative to authenticated sector, 0-3).
        @param data: Data to write (16 bytes as bytes or 32-character hex string).
        @raises ValueError: If data is not exactly 16 bytes.
        @raises GNetPlusError: If the write fails.
        @return: Block data in hex format
        """
        # Convert the hex string to bytes
        if isinstance(data, str):
            data = bytes.fromhex(data)
        if len(data) != 16:
            raise ValueError('Data must be exactly 16 bytes long'
                             '')
        self.sendmsg(QueryMessage.WRITE_BLOCK, bytes([block]) + data)
        return self.readmsg().data.hex()

    def read_sector(self, raw: bool = False, combine: bool = False) -> Union[Dict[int, Union[str, bytes]], Union[str, bytes]]:
        """
        Read blocks 0,1,2 in a given sector, optionally combining them.

        @param raw: If True, returns raw bytes; otherwise hex strings.
        @param combine: If True, returns concatenated data across blocks as a single bytes or hex string.
        @return: Dict mapping absolute block number to data (bytes or hex), or combined bytes/hex string.
        @raises GNetPlusError: If any block read fails.
        """
        results: Dict[int, Union[str, bytes]] = {}

        for block in range(3):
            results[block] = self.read_block(block, raw=raw)

        if combine:
            if raw:
                return b''.join(results.values())
            return ''.join(results.values())

        return results

    def write_sector(self, data: Union[str, bytes, Dict[int, Union[str, bytes]]]) -> None:
        """
        Write up to three data blocks in a given sector.

        @param data:
          • 16-byte bytes or 32-char hex string → writes that to blocks 0,1,2.
          • 48-byte bytes or 96-char hex string → splits into three 16-byte chunks.
          • dict mapping blocks 0–2 to data blobs and 3 for trailing block.
        @raises ValueError: If data length isn’t one of the supported sizes, or if dict keys are invalid.
        @raises GNetPlusError: If any write fails.
        """
        # Normalize hex-string to bytes
        if isinstance(data, str):
            data = bytes.fromhex(data)

        # Case A: Single-block blob
        if isinstance(data, (bytes, bytearray)) and len(data) == 16:
            for block in (0, 1, 2):
                self.write_block(block, data)
            return

        # Case B: Triple-block blob
        if isinstance(data, (bytes, bytearray)) and len(data) == 16 * 3:
            for i, block in enumerate((0, 1, 2)):
                chunk = data[i * 16:(i + 1) * 16]
                self.write_block(block, chunk)
            return

        # Case C: Explicit per-block dict
        if isinstance(data, dict):
            for block, blob in data.items():
                # Determine absolute block number
                if block not in (0, 1, 2):
                    raise ValueError('Block keys must be integers (0-3)')
                # Normalize each entry
                if isinstance(blob, str):
                    blob = bytes.fromhex(blob)

                self.write_block(block, blob)

            return

        raise ValueError(
            'Unsupported data length %s; must be 16 or 48 bytes, or a dict of blocks→16-byte blobs' % len(data) if isinstance(data, (bytes, bytearray)) else 'unknown')

    def read_blocks(self, mapping: Dict[int, List[int]], raw: bool = False, combine: bool = False, keys: Union[bytes, Dict[int, bytes]] = None,
                    key_types: Union[str, Dict[int, str]] = 'A', timeout: Union[float, Dict[int, float]] = 1.0,
                    flush: Union[bool, Dict[int, bool]] = True) -> Union[Dict[int, Dict[int, Union[str, bytes]]], Union[str, bytes]]:
        """
        Read multiple blocks across sectors based on a sector->blocks mapping,
        optionally combining them and authenticating per sector with either a single key
        for all sectors or individual keys per sector.

        @param mapping: Dict where keys are sector numbers and values are lists of blocks (0-3).
        @param raw: If True, returns bytes; otherwise hex strings.
        @param combine: If True, returns concatenated data across blocks as a single bytes or hex string.
        @param keys: Optional 6-byte key or dict mapping sector->key bytes.
        @param key_types: 'A'/'B' or dict mapping sector->'A'/'B'.
        @param timeout: Timeout in seconds or dict mapping sector->timeout.
        @param flush: Whether to flush input buffer or dict mapping sector->flush flag.
        @return: Nested dict mapping sector -> {block: data}, or combined bytes/hex.
        @raises ValueError: If keys or key_types provided but invalid.
        @raises GNetPlusError: If authentication or block read fails.
        """
        results: Dict[int, Dict[int, Union[str, bytes]]] = {}

        # Normalize helper
        def get_param(param, sector, default):
            if isinstance(param, dict):
                return param.get(sector, default)
            return param if param is not None else default

        for sector, blocks in mapping.items():
            key = get_param(keys, sector, None)
            ktype = get_param(key_types, sector, 'A')
            ktout = get_param(timeout, sector, 1.0)
            kflush = get_param(flush, sector, True)

            if key is not None:
                self.authenticate_sector(sector, key, ktype, ktout, kflush)

            results[sector] = {}
            for block in blocks:
                results[sector][block] = self.read_block(block, raw=raw)

        if combine:
            if raw:
                combined = b''
                for sector, blocks in mapping.items():
                    for block in blocks:
                        combined += results[sector][block]
                return combined

            combined = ''
            for sector, blocks in mapping.items():
                for block in blocks:
                    combined += results[sector][block]
            return combined

        return results

    def write_blocks(self, mapping: Dict[int, Union[bytes, str, Dict[int, Union[str, bytes]]]], keys: Union[bytes, Dict[int, bytes]] = None,
                     key_types: Union[str, Dict[int, str]] = 'A',
                     timeout: Union[float, Dict[int, float]] = 1.0, flush: Union[bool, Dict[int, bool]] = True) -> None:
        """
        Write multiple blocks across sectors, supporting a mix of:
          • sector -> blob (bytes or hex-string)  (writes that blob to all 4 blocks via write_sector)
          • sector -> {block: data, …}           (writes per‐block via write_block)
        optionally authenticating per sector with either a global key or per-sector keys.

        @param mapping: Dict where keys are sector numbers and values are either dict mapping block (0-3) to data or a single blob for the whole sector.
        @param keys: Optional 6-byte key or dict mapping sector->key bytes.
        @param key_types: 'A'/'B' or dict mapping sector->'A'/'B'.
        @param timeout: Timeout in seconds or dict mapping sector->timeout.
        @param flush: Whether to flush input buffer or dict mapping sector->flush flag.
        @raises ValueError: If any block's data is not exactly 16 bytes.
        @raises GNetPlusError: If authentication or block write fails.
        """

        # Normalize helper
        def get_param(param, sector, default):
            if isinstance(param, dict):
                return param.get(sector, default)
            return param if param is not None else default

        # Otherwise, per‐block writes
        for sector, spec in mapping.items():
            key = get_param(keys, sector, None)
            ktype = get_param(key_types, sector, 'A')
            ktout = get_param(timeout, sector, 1.0)
            kflush = get_param(flush, sector, True)
            if key is not None:
                self.get_sn()  # Refresh card before authenticating next sector
                self.authenticate_sector(sector, key, ktype, ktout, kflush)

            # branch per-sector spec type
            if isinstance(spec, dict):
                # per-block writes
                for block, data in spec.items():
                    self.write_block(block, data)
            else:
                self.write_sector(spec)
