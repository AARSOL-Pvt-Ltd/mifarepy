# 🔍 Examples

These examples demonstrate common **mifarepy** workflows using the `MifareReader` API.

---

## 1️⃣ Detect and Read Card UID

```python
from mifarepy import MifareReader

# 1. Initialize reader
reader = MifareReader(port='/dev/ttyUSB0')

# 2. Enable auto‐mode and wait for a card
reader.set_auto_mode(True)
try:
    uid = reader.wait_for_card(timeout=5)
    print(f"✅ Detected card UID: {uid}")
except TimeoutError:
    print("⏰ No card detected within 5 seconds.")
```

**What’s happening**:
- `set_auto_mode(True)`: Reader emits events when cards enter field.
- `wait_for_card()`: Blocks until a card is seen or timeout.

---

## 2️⃣ Authenticate Sector & Read Block

```python
from mifarepy import MifareReader

reader = MifareReader('/dev/ttyUSB0')

# Default MIFARE Key A
key_a = bytes.fromhex('FFFFFFFFFFFF')
sector = 1
block = 0  # first block in sector 1

# Authenticate sector
reader.authenticate_sector(sector=sector, key=key_a, key_type='A')

# Read block data
data = reader.read_block(block)
print(f"Block {block} data: {data.hex()}")
```

**Details**:
- `authenticate_sector()`: Loads and uses Key A to unlock sector.
- `read_block()`: Reads 16 bytes from specified block index.

---

## 3️⃣ Write to a Block

```python
from mifarepy import MifareReader

reader = MifareReader('/dev/ttyUSB0')

# Authenticate first
reader.authenticate_sector(sector=1, key=key_a)

# Prepare payload
payload = bytes(range(16))  # 0x00..0x0F
block = 1 # Second block in Sector 1

# Write and verify
reader.write_block(block, payload)
print(f"✍️ Wrote to block {block} successfully.")
```

**Note**: Data must be exactly 16 bytes.

---

## 4️⃣ Read Entire Sector

```python
from mifarepy import MifareReader

reader = MifareReader('/dev/ttyUSB0')
reader.authenticate_sector(sector=2, key=key_a)

sector_data = reader.read_sector(sector=2)
for block, blk_data in sector_data.items():
    print(f"Block {block}: {blk_data.hex()}")
```

- Returns a mapping of offsets (0–3) to block bytes.

---

## 5️⃣ Write Multiple Blocks in Sector

```python
from mifarepy import MifareReader

reader = MifareReader('/dev/ttyUSB0')
reader.authenticate_sector(sector=2, key=key_a)

updates = {
    0: bytes([0xAA] * 16),  # First Block of Sector 2 
    2: bytes([0xBB] * 16)   # Third Block of Sector 2
}
reader.write_sector(sector=2, data_blocks=updates)
print("🔧 Sector 2 updated on blocks 0 and 2.")
```

Data for unspecified offsets remains unchanged.

---

## 6️⃣ Bulk Mapping: Read and Write

```python
from mifarepy import MifareReader

reader = MifareReader('/dev/ttyUSB0')

# Define mapping: sector → list of offsets
read_map = {1: [0,1], 3: [2,3]}

# Optionally provide per-sector keys
keys = {1: key_a, 3: key_a}

data = reader.read_blocks(mapping=read_map, raw=False, combine=False, keys=keys)
print(data)

# Write mapping: full blob for sector 1 and dict for sector 3
write_map = {
    1: bytes(range(48)),             # three-block blob
    3: {0: b'HELLO-R3'*2, 3: b'BYE-R3'*2}
}
reader.write_blocks(mapping=write_map, keys=keys)
print("🚀 Bulk operations complete.")
```

- **`read_blocks`**: Reads arbitrary sets of blocks across sectors.
- **`write_blocks`**: Writes sector-wide or per-block based on mapping.

---

_For more details, see [usage](usage.md) and [api](api.md)._