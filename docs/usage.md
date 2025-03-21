# 🚀 Usage Guide

This guide will help you quickly get started with `mifarepy`, from connecting to your RFID reader to performing basic
operations.

## **Connecting to a Reader**

The simplest way to connect to your MIFARE RFID reader is:

```python
from mifarepy import Handle

# Initialize the handle with the correct serial port (e.g., '/dev/ttyUSB0' for Linux)
handle = Handle('/dev/ttyUSB0')
# Wait for a card to be detected.
handle.wait_for_card()
# Retrieve the card's serial number as a formatted string
serial_number = handle.get_sn(as_string=True)
print(f'Found card: {serial_number}')
```

Note: wait_for_card() also returns the card's serial number, so you can skip the get_sn() call if you only need the
serial number.

## **Retrieving the Reader Version**

You can also query your RFID reader’s version:

```python
from mifarepy import Handle

# Initialize the handle with the correct serial port (e.g., '/dev/ttyUSB0' for Linux)
handle = Handle('/dev/ttyUSB0')
# Wait for a card to be detected.
handle.wait_for_card()
# Retrieve the reader's version information
version_info = handle.get_version()
print('Reader Version:', version_info)
```

For full, detailed examples, see the [Examples](examples.md) section.