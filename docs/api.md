# API Reference — `mifarepy`

This document provides a detailed overview of the classes, methods, and constants available in the `mifarepy` library, which is used to interface with PROMAG RFID card readers using the GNetPlus® protocol.

---

## Table of Contents

- [Exceptions](#exceptions)
    - [InvalidMessage](#class-invalidmessage)
    - [GNetPlusError](#class-gnetpluserror)
- [Message Classes](#message-classes)
    - [Message](#class-message)
    - [QueryMessage](#class-querymessage)
    - [ResponseMessage](#class-responsemessage)
- [Handle Class](#handle-class)
    - [Constructor](#handle-__init__)
    - [sendmsg](#handle-sendmsg)
    - [readmsg](#handle-readmsg)
    - [get_sn](#handle-get_sn)
    - [get_version](#handle-get_version)
    - [set_auto_mode](#handle-set_auto_mode)
    - [wait_for_card](#handle-wait_for_card)
- [Additional Notes](#additional-notes)

---

## Exceptions

### Class: `InvalidMessage`
- **Description:**  
  Raised when an invalid message is received from the RFID reader. This can occur if the header is incomplete, the SOH (Start-of-Header) does not match, the data or CRC is incomplete, or if the CRC check fails.
- **Usage:**  
  This exception is automatically raised during message parsing in the `Message.readfrom` method.

---

### Class: `GNetPlusError`
- **Description:**  
  Thrown when a NAK (negative acknowledge) response is received from the RFID reader. This error indicates that an issue occurred during the communication process.
- **Usage:**  
  Raised by the `Handle.readmsg` method when a NAK response is detected. The error message usually includes details from the response's data payload.

---

## Message Classes

### Class: `Message`
#### Description
  The base class representing a message to be sent to or received from the RFID reader. This class handles message construction, conversion to raw bytes, and CRC checksum generation.

#### Methods

- **`__init__(self, address: int, function: int, data: Union[bytes, str])`**  
    **Parameters:**
    - `address`: An 8-bit device address (typically 0 unless specified otherwise).
    - `function`: An 8-bit function code representing the type of message.
    - `data`: The payload for the message, provided as either `bytes` or a `str` (if a string is provided, it is encoded using Latin-1).
  
    **Description:**  
    Initializes the message with the specified address, function code, and data.

- **`__bytes__(self) -> bytes`**  
    **Returns:**  
    The binary (raw byte) representation of the message.
  
    **Description:**  
    Packs the address, function code, and length of the data into bytes, appends the data payload, calculates the 16-bit CRC checksum using `gencrc`, and then prepends the SOH (Start-of-Header) byte.  
    **Message Format:**  
    `[SOH][address][function][data_length][data][CRC16]`

- **`__str__(self) -> str`**  
    **Returns:**  
    A hexadecimal string representation of the message.
  
    **Description:**  
    Converts the binary message (obtained from `__bytes__`) into a human-readable hex string.

- **`__repr__(self) -> str`**  
    **Returns:**  
    A debug-friendly string representation of the message, showing the address, function code, and data.
  
    **Description:**  
    Useful for debugging purposes.

- **`sendto(self, serial_port)`**  
    **Parameters:**
    - `serial_port`: An open serial port (from the `pyserial` package).
  
    **Description:**  
    Sends the constructed message over the provided serial port by writing the raw bytes to it.

- **`@classmethod readfrom(cls, serial_port)`**  
    **Parameters:**
    - `serial_port`: The serial port from which the message is read.
  
    **Returns:**  
    An instance of the `Message` class constructed from the read data.
  
    **Raises:**  
    `InvalidMessage` if the message is incomplete or the CRC check fails.
  
    **Description:**  
    Reads the message header, data payload, and CRC from the serial port, validates the message integrity, and returns a new message instance.

- **`@staticmethod gencrc(msg_bytes: bytes) -> int`**  
    **Parameters:**
    - `msg_bytes`: The message bytes over which the CRC is calculated.
  
    **Returns:**  
    A 16-bit integer representing the CRC checksum.
  
    **Description:**  
    Computes a CRC-16 checksum using the polynomial 0xA001 by processing each byte of the message.

---

### Class: `QueryMessage`
#### Description
  A subclass of `Message` used specifically for query messages (commands) sent from the host to the RFID reader. This class defines constants for various function codes as specified in the GNetPlus® protocol.
  
#### Constants (Examples)
  - `POLLING = 0x00`
  - `GET_VERSION = 0x01`
  - `SET_SLAVE_ADDR = 0x02`
  - `LOGON = 0x03`
  - `LOGOFF = 0x04`
  - ... (continues up to `AUTO_MODE = 0x3F`)
  
#### Usage 
  Construct a query message with the desired function code and optional data payload, then send it using the `sendto` method.

---

### Class: `ResponseMessage`
#### Description
  A subclass of `Message` designed for handling responses from the RFID reader.
  
#### Constants
  - `ACK = 0x06`: Indicates an acknowledgement (successful operation).
  - `NAK = 0x15`: Indicates a negative acknowledgement (error occurred).
  - `EVN = 0x12`: Indicates an event notification.
  
#### Methods
  - **`to_error(self) -> Optional[GNetPlusError]`**  
    **Returns:**  
    An instance of `GNetPlusError` if the message’s function code is `NAK`, otherwise `None`.
    
    **Description:**  
    Converts a negative acknowledgement response into an error that can be raised by the calling code.

---

## Handle Class

### Class: `Handle`
#### Description 
  The primary class for interfacing with the RFID card reader. It encapsulates the serial connection and provides high-level methods to send commands, read responses, and perform operations such as retrieving the card’s serial number.

#### Methods

- **`__init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 19200, deviceaddr: int = 0, **kwargs)`**  
    **Parameters:**
    - `port`: The serial port to connect to (e.g., `/dev/ttyUSB0`).
    - `baudrate`: The baud rate for the serial connection (default is 19200).
    - `deviceaddr`: The device address; typically 0 unless otherwise specified.
    - `**kwargs`: Additional keyword arguments for the `serial.Serial` constructor.
  
    **Raises:**  
    `RuntimeError` if the serial port cannot be opened.
  
    **Description:**  
    Initializes the serial connection to the RFID reader. If opening the serial port fails, a `RuntimeError` is raised with an appropriate error message.


- **`sendmsg(self, function: int, data: bytes = b'') -> None`**  
    **Parameters:**
    - `function`: The function code (from `QueryMessage`) that specifies the command.
    - `data`: Optional payload data as bytes.
  
    **Description:**  
    Constructs a `QueryMessage` using the device’s address, function code, and data, then sends the message over the established serial connection.


- **`readmsg(self, sink_events: bool = False) -> ResponseMessage`**  
    **Parameters:**
    - `sink_events`: A boolean flag indicating whether to ignore event messages (with function code `EVN`) until a non-event response is received.
  
    **Returns:**  
    A `ResponseMessage` instance containing the data received from the RFID reader.
  
    **Raises:**  
    `GNetPlusError` if a negative acknowledgement (NAK) response is received.
  
    **Description:**  
    Continuously reads messages from the serial port until a valid (non-event) message is obtained. If a NAK is received, it is converted to a `GNetPlusError` and raised.


- **`get_sn(self, endian: str = 'little', as_string: bool = True) -> Union[str, int]`**  
    **Parameters:**
    - `endian`: Specifies the byte order for interpreting the UID. Acceptable values are `'big'` or `'little'`.  
      - For example, raw data `b'\xE3\x0E\x27\x0E'` is interpreted as:
        - `'big'`: `0xE30E270E`
        - `'little'`: `0x0E270EE3`
    - `as_string`: If `True`, returns the UID as a formatted hexadecimal string (e.g., `"0x0E270EE3"`); otherwise, returns it as an integer.
  
    **Returns:**  
    The serial number of the card currently scanned.
  
    **Description:**  
    Retrieves the card’s serial number by sending a `REQUEST` command followed by an `ANTI_COLLISION` command to resolve potential collisions. The response data is unpacked according to the specified endian format and returned in the requested format.


- **`get_version(self) -> bytes`**  
    **Returns:**  
    A byte string containing the product version string of the RFID reader.
  
    **Description:**  
    Sends the `GET_VERSION` command to the RFID reader and returns the version information. The returned bytes may include null characters; therefore, proper handling is recommended when displaying or processing the version string.


- **`set_auto_mode(self, enabled: bool = True) -> bytes`**  
    **Parameters:**
    - `enabled`: A boolean indicating whether to enable (`True`) or disable (`False`) auto mode.
  
    **Returns:**  
    The response data from the RFID reader as bytes.
  
    **Raises:**  
    `GNetPlusError` if the response data does not match the expected mode (indicating that setting auto mode failed).
  
    **Description:**  
    Toggles the RFID reader’s auto mode by sending the `AUTO_MODE` command with the corresponding mode byte (`\x01` for enabled, `\x00` for disabled). The method then verifies that the response matches the intended mode.


- **`wait_for_card(self, timeout: int = 10) -> Optional[str]`**  
    **Parameters:**
    - `timeout`: The maximum number of seconds to wait for a card to be detected (default is 10 seconds).
  
    **Returns:**  
    The card’s serial number as a formatted hexadecimal string if detected; otherwise, returns `None`.
  
    **Raises:**  
    `TimeoutError` if no card is detected within the specified timeout period.
  
    **Description:**  
    First attempts to detect a card immediately. If unsuccessful, enters a loop where it periodically checks for a card event. When a card is detected (usually indicated by an event message containing a specific marker), it retrieves and returns the serial number. If no card is detected within the timeout, a `TimeoutError` is raised.

---

## Additional Notes

- **Data Encoding:**  
  The `Message` class encodes string data using Latin-1 encoding, ensuring that the data is properly formatted as bytes for serial transmission.

- **CRC Calculation:**  
  The static method `gencrc` implements a CRC-16 checksum calculation using the polynomial `0xA001`, ensuring data integrity.

- **Event Handling:**  
  The `readmsg` method can be set to ignore event messages (with function code `EVN`) using the `sink_events` flag, so that only responses to commands are processed.

- **Error Handling:**  
  If a NAK (negative acknowledge) response is received, the `to_error` method of the `ResponseMessage` class converts it into a `GNetPlusError`, which is then raised by `readmsg`.

---
