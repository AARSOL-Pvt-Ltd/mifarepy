# API Reference

This document provides an in-depth reference for every public class, function, and method in the **mifarepy** library, complete with parameter descriptions, return values, exceptions raised, and detailed behavior narratives.

---

## Package Structure

```
mifarepy/
├── protocol.py      # Core message framing, CRC, and error classes
└── reader.py        # High-level MifareReader interface and card operations
```

Import core components:

```python
import mifarepy
from mifarepy.protocol import (
    gencrc,
    Message,
    QueryMessage,
    ResponseMessage,
    InvalidMessage,
    GNetPlusError
)
from mifarepy.reader import MifareReader
```

---

## `protocol.py`

### `gencrc(msg_bytes: bytes) -> int`
**Description:** Calculates the 16-bit CRC (Cyclic Redundancy Check) for a given sequence of bytes, following the GNetPlus® protocol specification. This checksum is appended to each message to ensure data integrity.

- **Parameters:**
  - `msg_bytes` (`bytes`): The header and payload bytes over which to compute the CRC (Exclude SOH and the trailing CRC field).
- **Returns:**
  - (`int`) CRC value ranging from `0` to `0xFFFF`.
- **Raises:** None.

---

### `class InvalidMessage(Exception)`
**Description:** Thrown during message parsing when the data read from the serial port is malformed, incomplete, or fails the CRC check.

- **Raised When:**
  - The Start-of-Header (SOH) byte is incorrect.
  - The header or payload length is less than expected.
  - CRC validation fails.

---

### `class GNetPlusError(Exception)`
**Description:** Represents a protocol-level or device error signaled by a Negative Acknowledge (NAK) from the reader.

- **Raised When:** A `ResponseMessage` with `function == ResponseMessage.NAK` is received. The exception carries the raw NAK payload for diagnostics.

---

### `class Message`
**Description:** Base class encapsulating the raw binary format of any GNetPlus® message (both queries and responses). Handles packing to bytes and unpacking from bytes with CRC.

#### Constructor
```python
Message(address: int, function: int, data: bytes)
```
- **Parameters:**
  - `address` (`int`): The 8-bit device address (commonly `0`).
  - `function` (`int`): The 8-bit function or command code.
  - `data` (`bytes`): Payload data.
- **Behavior:** Stores inputs; used by `__bytes__` and `readfrom` methods.

#### `__bytes__(self) -> bytes`
**Description:** Serializes the `Message` into the wire format:

```
[SOH=0x01][address][function][length][data...][CRC-high][CRC-low]
```

- **Returns:** A `bytes` object ready to write to a serial port.

#### `@classmethod readfrom(cls, serial_port) -> Message`
**Description:** Reads raw bytes from a `serial_port` instance and constructs a `Message` object, validating framing and CRC.

- **Parameters:**
  - `serial_port`: An object with a `.read(n)` method (e.g., `serial.Serial`).
- **Behavior:**
  1. Reads 1 byte for SOH, 3 bytes for header. Validates SOH.
  2. Extracts `address`, `function`, and `length`.
  3. Reads `length` bytes of payload.
  4. Reads 2-byte CRC, computes expected CRC via `gencrc`.
  5. Raises `InvalidMessage` if any step fails.
- **Returns:** A `Message` instance with `.address`, `.function`, `.data` set.
- **Raises:** `InvalidMessage` on framing, length, or CRC errors.

---

### `class QueryMessage(Message)`
**Description:** Subclass of `Message` defining constants for all supported outgoing commands in the GNetPlus® protocol.

| Constant         | Hex Value | Description                                 |
|------------------|-----------|---------------------------------------------|
| `POLLING`        | `0x00`    | Ping the reader to check connectivity       |
| `GET_VERSION`    | `0x01`    | Request reader firmware version             |
| `AUTO_MODE`      | `0x3F`    | Enable/disable automatic card event reporting |
| `REQUEST`        | `0x20`    | Begin anti-collision to detect one card UID |
| `ANTI_COLLISION` | `0x21`    | Complete anti-collision, retrieve full UID  |
| `SELECT_CARD`    | `0x22`    | Select a specific card after UID retrieval  |
| `AUTHENTICATE`   | `0x23`    | Authenticate a sector using loaded key      |
| `READ_BLOCK`     | `0x24`    | Read a single 16-byte block                 |
| `WRITE_BLOCK`    | `0x25`    | Write a single 16-byte block                |
| `SAVE_KEY`       | `0x2B`    | Load a 6-byte MIFARE key into reader RAM    |

Use these as:
```python
msg = QueryMessage(address, QueryMessage.READ_BLOCK, payload)
```

---

### `class ResponseMessage(Message)`
**Description:** Subclass for replies from the reader. Interprets acknowledgement, errors, and event notifications.

| Constant | Hex Value | Description                                |
|----------|-----------|--------------------------------------------|
| `ACK`    | `0x06`    | Positive acknowledgement                   |
| `NAK`    | `0x15`    | Negative acknowledgement (error)           |
| `EVN`    | `0x12`    | Event notification (e.g., card arrival)    |

#### `to_error(self) -> Optional[GNetPlusError]`
**Description:** Converts a NAK response into a `GNetPlusError`. If the response is not NAK, returns `None`.

- **Returns:** A `GNetPlusError` instance for NAK responses, or `None` otherwise.

---

## reader.py

### `class MifareReader`
**Description:** High-level interface encapsulating serial communication and common card operations. Simplifies sending commands, parsing responses, and handling errors.

#### Constructor
```python
MifareReader(
    port: str = '/dev/ttyUSB0',
    baudrate: int = 19200,
    address: int = 0,
    **kwargs
)
```
- **Parameters:**
  - `port` (`str`): Path to serial device or COM port.
  - `baudrate` (`int`): Communication speed (default `19200`).
  - `address` (`int`): Reader device address (usually 0).
  - `**kwargs`: Additional settings for `serial.Serial` (e.g., `timeout`).
- **Behavior:** Opens serial port; raises `RuntimeError` on failure.

#### `sendmsg(self, function: int, data: bytes = b'') -> None`
**Description:** Packages and sends a `QueryMessage` to the reader.

- **Parameters:**
  - `function` (`int`): One of `QueryMessage` constants.
  - `data` (`bytes`): Optional payload.
- **Behavior:** Serializes and writes raw bytes to the serial port.
- **Raises:** Propagates exceptions from `serial.write()`.

#### `readmsg(self, sink_events: bool = False) -> ResponseMessage`
**Description:** Reads and returns the next meaningful response, optionally skipping event notifications.

- **Parameters:**
  - `sink_events` (`bool`): If `True`, ignore `EVN` messages.
- **Behavior:** Loops on `ResponseMessage.readfrom`, raises `GNetPlusError` on NAK.
- **Returns:** A `ResponseMessage` instance.
- **Raises:** `GNetPlusError`, `InvalidMessage`.

#### `get_version(self) -> str`
**Description:** Requests and returns the reader’s firmware version.

- **Behavior:** Sends `GET_VERSION`, reads response, decodes to string.
- **Returns:** Version string (e.g., `"v1.2.3"`).
- **Raises:** `GNetPlusError`, `InvalidMessage`.

#### `set_auto_mode(self, enable: bool = True) -> None`
**Description:** Toggles automatic card event reporting mode.

- **Parameters:**
  - `enable` (`bool`): `True` to enable, `False` to disable.
- **Behavior:** Sends `AUTO_MODE` with payload `\x01`/`\x00`, validates echo.
- **Raises:** `GNetPlusError` on mismatched response.

#### `wait_for_card(self, timeout: int = 10) -> Optional[str]`
**Description:** Blocks until a card arrives or timeout is reached.

- **Parameters:**
  - `timeout` (`int`): Seconds to wait.
- **Behavior:** Enables auto mode, tries immediate `get_sn`, then listens for EVN, returns UID.
- **Returns:** Card UID string or `None`.
- **Raises:** `TimeoutError`, `GNetPlusError`, `InvalidMessage`.

#### `get_sn(self, endian: str = 'little', as_string: bool = True) -> Union[str, int]`
**Description:** Retrieves the card’s unique serial number (UID).

- **Parameters:**
  - `endian` (`'little'` or `'big'`): Byte order.
  - `as_string` (`bool`): Return hex string if `True`, else integer.
- **Behavior:** Sends `REQUEST`/`ANTI_COLLISION`, unpacks UID.
- **Returns:** UID as `"0x..."` or int.
- **Raises:** `GNetPlusError`, `InvalidMessage`.

#### `authenticate_sector(self, sector: int, key: bytes, key_type: str = 'A') -> None`
**Description:** Loads and authenticates a MIFARE key for the specified sector.

- **Parameters:**
  - `sector` (`int`): Sector index (0–15).
  - `key` (`bytes`): 6-byte MIFARE key.
  - `key_type` (`'A'` or `'B'`): Key slot selection.
  - `timeout` (`int`): Timeout in seconds for reader responses.
  - `flush` (`bool`): Whether to flush the input buffer before reading responses.
- **Behavior:** Validates params, sends `SAVE_KEY` then `AUTHENTICATE`, checks ACKs.
- **Raises:** `ValueError`, `GNetPlusError`, `InvalidMessage`.

#### `read_block(self, block: int, raw: bool = False) -> bytes`
**Description:** Reads exactly 16 bytes from a specific memory block.

- **Parameters:**
  - `block` (`int`): Block number (0–63).
- **Behavior:** Sends `READ_BLOCK`, receives data payload.
- **Returns:** 16 bytes.
- **Raises:** `GNetPlusError`, `InvalidMessage`.

#### `write_block(self, block: int, data: Union[str, bytes]) -> None`
**Description:** Writes exactly 16 bytes or 32 bit hex to a specific block.

- **Parameters:**
  - `block` (`int`): Block number.
  - `data` (`bytes`): Must be length 16 bytes.
- **Behavior:** Validates length, sends `WRITE_BLOCK`, confirms ACK.
- **Raises:** `ValueError`, `GNetPlusError`, `InvalidMessage`.

#### `read_sector(self, raw: bool = False, combine: bool = False) -> Union[Dict[int, Union[str, bytes]], Union[str, bytes]]`
**Description:** Reads blocks `0,1,2` of the current sector and returns a mapping or concatenated data.

- **Parameters:**
  - `sector` (`int`): Sector index.
- **Behavior:** Calls `read_block` for offsets 0–3, returns dict.
- **Returns:** `{block: data} or combined data byte or hex`.
- **Raises:** `GNetPlusError`.

#### `write_sector(self, data: Union[str, bytes, Dict[int, Union[str, bytes]]]) -> None`
**Description:** Writes multiple blocks within one sector using a dictionary.

- **Parameters:**
  - `sector` (`int`): Sector index.
  - `data_blocks` (`Dict[int, bytes]`): Map of block offsets to 16-byte data.
    - **bytes/str length 16:** writes that blob to blocks 0,1,2.
    - **bytes/str length 48:** splits into three chunks for blocks 0–2.
    - **dict {block:data}:** dict mapping blocks 0–2 to data blobs and 3 for trailing block.
- **Behavior:** Iterates and calls `write_block` for each entry.
- **Raises:** `ValueError`, `GNetPlusError`, `InvalidMessage`.

#### `read_blocks(self, mapping: Dict[int, List[int]], raw: bool = False, combine: bool = False, keys: Union[bytes, Dict[int, bytes]] = None, key_types: Union[str, Dict[int, str]] = 'A', timeout: Union[float, Dict[int, float]] = 1.0, flush: Union[bool, Dict[int, bool]] = True) -> Union[Dict[int, Dict[int, Union[str, bytes]]], Union[str, bytes]]) -> Union[Dict[int, Dict[int, Union[str, bytes]]], Union[str, bytes]]`
**Description:** Read multiple blocks across sectors based on a sector->block-offsets mapping, optionally combining them and authenticating per sector with either a single key for all sectors or individual keys per sector.

- **Parameters:**
  - `mapping` (`dict`): Dict where keys are sector numbers and values are lists of block offsets (0-3).
  - `raw` (`bool`): If True, returns bytes; otherwise hex strings.
  - `combine` (`bool`): If True, returns concatenated data across blocks as a single bytes or hex string.
  - `keys` (`bytes or doct`): Optional 6-byte key or dict mapping sector->key bytes.
  - `key_types` (`str or dict`): 'A'/'B' or dict mapping sector->'A'/'B'.
  - `timeout` (`float or dict`): Timeout in seconds or dict mapping sector->timeout.
  - `flush` (`bool or dict`): Whether to flush input buffer or dict mapping sector->flush flag.
- **Behavior:** Returns Nested dict mapping sector -> {offset: data}, or combined bytes/hex.
- **Raises:** `ValueError`, `GNetPlusError`.

#### `write_blocks(self, mapping: Dict[int, Union[bytes, str, Dict[int, Union[str, bytes]]]], keys: Union[bytes, Dict[int, bytes]] = None, key_types: Union[str, Dict[int, str]] = 'A', timeout: Union[float, Dict[int, float]] = 1.0, flush: Union[bool, Dict[int, bool]] = True) -> None`
**Description:** Write multiple blocks across sectors, supporting a mix of:
- sector -> blob (bytes or hex-string) (writes that blob to all 4 blocks via write_sector)
- sector -> {block: data, …} (writes per‐block via write_block)

optionally authenticating per sector with either a global key or per-sector keys.

- **Parameters:**
  - `mapping` (`dict`): Dict where keys are sector numbers and values are either dict mapping block (0-3) to data or a single blob for the whole sector.
  - `keys` (`bytes or doct`): Optional 6-byte key or dict mapping sector->key bytes.
  - `key_types` (`str or dict`): 'A'/'B' or dict mapping sector->'A'/'B'.
  - `timeout` (`float or dict`): Timeout in seconds or dict mapping sector->timeout.
  - `flush` (`bool or dict`): Whether to flush input buffer or dict mapping sector->flush flag.
- **Behavior:** Writes data in the given blocks handling refreshing of card before authentication for new sector.
- **Raises:** `ValueError`, `GNetPlusError`.

---

### Exception Summary

All methods may raise:

- **`InvalidMessage`**: Frame/CRC parsing errors.
- **`GNetPlusError`**: Device-signaled errors (NAK).
- **`RuntimeError`**: Serial port failures.
- **`ValueError`**: Invalid arguments.
- **`TimeoutError`**: For `wait_for_card` timeouts.

---

*For real-world code examples using these APIs, see [examples](examples.md).*
