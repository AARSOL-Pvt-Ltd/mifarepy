# 📝 Examples

### Example 1: Authenticating a Sector and Reading from a Block

In this example, we demonstrate how to save the default key, authenticate a specific sector, and then read data from a block within that sector.

```python
from mifarepy import Handle, QueryMessage

# Initialize the RFID reader handle on the correct serial port.
handle = Handle('/dev/ttyUSB0')
# Wait for a card to be detected.
handle.wait_for_card()

# --- Step 1: Save the Key to the Reader ---
sector = 2                       # The sector to authenticate.
key_type = 0x60                  # Key A (use 0x61 for Key B if required).
default_key = "FFFFFFFFFFFF"      # Default key in hexadecimal.

# Build the payload: key type (1 byte), sector (1 byte), followed by key bytes.
save_key_data = bytes([key_type, sector]) + bytes.fromhex(default_key)
handle.sendmsg(QueryMessage.SAVE_KEY, save_key_data)
save_key_ack = handle.readmsg()
print("SAVE_KEY ACK:", save_key_ack.data.hex())

# --- Step 2: Authenticate the Sector ---
auth_data = bytes([key_type, sector])
handle.sendmsg(QueryMessage.AUTHENTICATE, auth_data)
auth_ack = handle.readmsg()
print("AUTHENTICATE ACK:", auth_ack.data.hex())

# --- Step 3: Read from a Block in the Authenticated Sector ---
block_number = 0  # The block number to read from.
handle.sendmsg(QueryMessage.READ_BLOCK, bytes([block_number]))
block_response = handle.readmsg()
print("Block Data:", block_response.data.hex())
```

### Example 2: Switching Sectors and Refreshing the Card Session

When switching to a new sector, it's important to refresh the card session by sending an ANTI_COLLISION command. This example shows how to do that before authenticating the new sector and reading from a block.

```python
from mifarepy import Handle, QueryMessage

# Initialize the RFID reader handle.
handle = Handle('/dev/ttyUSB0')

# Assume you have finished operations in the current sector.
# Now you want to switch to a new sector (e.g., sector 3).
new_sector = 3
key_type = 0x60                  # Using Key A.
default_key = "FFFFFFFFFFFF"      # Default key in hexadecimal.

# --- Step 1: Refresh the Card Session ---
# When switching sectors, send the ANTI_COLLISION command to re-identify the card.
handle.sendmsg(QueryMessage.ANTI_COLLISION, b'')
anti_collision_response = handle.readmsg(sink_events=True)
print("ANTI_COLLISION Response:", anti_collision_response.data.hex())

# --- Step 2: Save the Key for the New Sector ---
save_key_data = bytes([key_type, new_sector]) + bytes.fromhex(default_key)
handle.sendmsg(QueryMessage.SAVE_KEY, save_key_data)
save_key_ack = handle.readmsg()
print("SAVE_KEY ACK (New Sector):", save_key_ack.data.hex())

# --- Step 3: Authenticate the New Sector ---
auth_data = bytes([key_type, new_sector])
handle.sendmsg(QueryMessage.AUTHENTICATE, auth_data)
auth_ack = handle.readmsg()
print("AUTHENTICATE ACK (New Sector):", auth_ack.data.hex())

# --- Step 4: Read from a Block in the New Sector ---
block_number = 8  # Specify the block number to read from in the new sector.
handle.sendmsg(QueryMessage.READ_BLOCK, bytes([block_number]))
block_response = handle.readmsg()
print("Block Data (New Sector):", block_response.data.hex())
```
