# 📘 Usage Guide 🚀

This guide walks you through common workflows in **mifarepy**: connecting to your reader, detecting cards, reading/writing blocks and sectors, bulk operations, and error handling.

---

## 🔧 Prerequisites

- Python 3.6 or newer 🐍
- `pyserial` installed (automatically with `pip install mifarepy`)
- A supported MIFARE® reader (PROMAG PCR310U, MF5, MF10, etc.) connected via USB-to-serial or COM port 🔌
- Appropriate permissions (e.g., add your user to `dialout` on Linux) 🛠️

---

## 1️⃣ Connecting to the Reader

```python
from mifarepy.reader import MifareReader

# Replace '/dev/ttyUSB0' with your port (e.g., 'COM3' on Windows)
reader = MifareReader(port='/dev/ttyUSB0', baudrate=19200)
```

- **`port`**: Serial device path.
- **`baudrate`**: Communication speed (default `19200`).
- Raises **`RuntimeError`** ❌ if the port cannot be opened.

---

## 2️⃣ Discovering Cards

### 2.1 🔄 Enable Event Mode and Wait

```python
# Turn on automatic card detection
reader.set_auto_mode(True)

# Block up to 10 seconds for a card
uid = reader.wait_for_card(timeout=10)
if uid:
    print(f"✅ Card detected: {uid}")
else:
    print("⏰ No card detected within timeout.")
```

- **`set_auto_mode(True)`**: Enables event notifications 🔔.
- **`wait_for_card(timeout)`**: Returns UID string or raises **`TimeoutError`**.

### 2.2 📶 Polling for UID Directly

```python
# Manual polling
uid = reader.get_sn(endian='little', as_string=True)
print(f"🎴 Card UID: {uid}")
```

- **`get_sn`**: Anti-collision sequence; returns hex string or integer 🔢.
- **`endian`**: Byte order; **`as_string`** toggles return type.

---

## 3️⃣ Reading and Writing a Single Block

### 3.1 🔐 Authenticate a Sector

```python
# MIFARE Classic default Key A
default_key = bytes.fromhex('FFFFFFFFFFFF')
reader.authenticate_sector(sector=1, key=default_key, key_type='A')
```

- **`sector`**: 0–15 (for 1K cards).
- **`key_type`**: `'A'` or `'B'`.
- Raises **`ValueError`**, **`GNetPlusError`** on failure.

### 3.2 📖 Read 16 Bytes

```python
data = reader.read_block(block=4)
print("Block 4 data:", data.hex())
```

- **`block`**: Absolute index (0–63).
- Returns raw bytes 📦; `.hex()` for hex.

### 3.3 ✍️ Write 16 Bytes

```python
payload = bytes(range(16))  # 0x00,0x01,...0x0F
reader.write_block(block=4, data=payload)
```

- Data length must be exactly 16 bytes ⚠️.

---

## 4️⃣ Sector-Level Operations

### 4.1 🔄 Read Entire Sector

```python
sector_data = reader.read_sector(sector=2)
for offset, block in sector_data.items():
    print(f"Block {2*4 + offset}: {block.hex()}")
```

- Returns a dict `{offset: data}`.

### 4.2 ✍️ Write Multiple Blocks

```python
# Update blocks 0 and 2 of sector 2
updates = {
    0: bytes([0xAA]*16),
    2: bytes([0xBB]*16)
}
reader.write_sector(sector=2, data_blocks=updates)
```

- Supplies a dict of offsets → bytes.

---

## 5️⃣ Bulk Block Operations

### 5.1 📚 Reading Arbitrary Mapping

```python
mapping = {1: [0,1], 3: [2,3]}  # sector → list of offsets
data = reader.read_blocks(mapping=mapping, raw=True, combine=False)
```

- **`mapping`**: `{sector: [offsets]}`.
- Pass **`keys`, `key_types`, `timeout`, `flush`** as needed.

### 5.2 ✍️ Writing Arbitrary Mapping

```python
mapping = {
    1: bytes(range(48)),
    2: {1: bytes([0x11]*16), 3: bytes([0x22]*16)}
}
reader.write_blocks(mapping=mapping)
```

- Supports 16-byte, 48-byte blobs, or per-offset dicts.

---

## 6️⃣ Error Handling

- **`InvalidMessage`**: Framing/CRC errors ❌.
- **`GNetPlusError`**: Reader-reported NAK errors 🚫.
- **`ValueError`**: Bad args or lengths ⚠️.
- **`TimeoutError`**: No card in `wait_for_card` ⏱️.

```python
try:
    reader.read_block(5)
except GNetPlusError as e:
    print("Device error:", e)
except InvalidMessage as e:
    print("Protocol error:", e)
```

---

## 7️⃣ Troubleshooting Tips

- **Permissions:** `sudo usermod -aG dialout $USER` (Linux) 🔒.
- **Port Busy:** Close other apps using the COM port 🚪.
- **Timeouts:** Increase via `MifareReader(timeout=5)` or adjust code ⏲️.
- **Key Mismatch:** Ensure correct Key A/B 🔑.
- **Firmware:** Check `get_version()` for compatibility 🔍.

---

For more examples, see [examples](examples.md) and for a full API reference, see [api](api.md). 🎉
