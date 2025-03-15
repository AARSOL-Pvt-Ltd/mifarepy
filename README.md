# **mifarepy**

## **Overview**

`mifarepy` is a **Python library** for interfacing with **MIFARE® RFID card readers** using the **GNetPlus® protocol**.
It enables communication with **PROMAG card readers**, specifically the **PCR310U** and other **GIGA-TMS Inc.** devices
that support **ISO14443A MIFARE® Ultra-Light/1K/PRO** cards.

This library provides functions for:

- **Reading serial numbers** from MIFARE® cards
- **Interacting via RS232 and USB-serial** interfaces
- **Supporting GNetPlus® commands** (Read, Write, Authenticate, Auto Mode, etc.)

---

## **Attribution & Original Repository**

This project is **derived from** the original `mifarepy.py` by **Chow Loong Jin & Harish Pillay**.

- **Original Repository:** [gnetplus by harishpillay](https://github.com/harishpillay/gnetplus)
- **Original Authors:** Chow Loong Jin & Harish Pillay
- **License:** This project remains under **LGPL v3.0 or later** to comply with the original licensing terms.

This version of `gnetplus.py` includes **bug fixes, documentation improvements, and enhanced compatibility**.

---

## **Supported Hardware**

This library is compatible with **PROMAG** MIFARE® readers, including:

- **PCR310U** (USB-based)
- **MF5 OEM Read/Write Module**
- **MF10 MIFARE Read/Write Module**
- **Other devices using the GNetPlus® protocol**

These readers operate at **13.56 MHz** and support **MIFARE® 1K/4K, Ultra-Light, and PRO cards**.

---

## **Installation**

To install `mifarepy`, ensure **Python 3.6+** is installed, then run:

```sh
pip install pyserial
```

Or manually include the `mifarepy.py` file in your project.

---

## **Usage**

### **Command-Line Usage**

You can run `mifarepy.py` directly from the command line:

```sh
python mifarepy.py /dev/ttyUSB0
```

Replace `/dev/ttyUSB0` with the correct serial port.

### **Library Usage (Python)**

You can also use it in your Python scripts:

```python
from mifarepy import Handle

handle = Handle('/dev/ttyUSB0')
serial_number = handle.get_sn(as_string=True)
print(f'Found card: {serial_number}')
```

---

## **Communicating with the Reader**

### **Detecting the Device**

When plugged into a **Linux** system (such as **Raspberry Pi** or **Fedora**), the reader is detected as:

```
Prolific Technology, Inc. PL2303 Serial Port
```

To find the assigned port, check:

```sh
dmesg | grep ttyUSB
```

Example output:

```
usb 6-1: pl2303 converter now attached to ttyUSB3
```

This means the device is at `/dev/ttyUSB3`.

---

## **Supported Commands**

This library supports the following **GNetPlus® protocol commands**:

| Command               | Functionality                                |
|-----------------------|----------------------------------------------|
| **Polling**           | Check if a reader is connected               |
| **Get Version**       | Retrieve firmware version                    |
| **Logon/Logoff**      | Secure access                                |
| **Get Serial Number** | Retrieve MIFARE® card serial number          |
| **Read Block**        | Read memory block from MIFARE® 1K card       |
| **Write Block**       | Write to a specific block                    |
| **Authenticate**      | Perform authentication with Key A/Key B      |
| **Set Auto Mode**     | Enable/Disable automatic event notifications |
| **Request All**       | Detect multiple cards in the field           |

For a full list of commands, refer to the *
*[mifarepy Communication Protocol](./TM970013_GNetPlusCommunicationProtocol_REV_D.pdf)**.

---

## **Example Output**

When a card is detected, you will see:

```
Found card: 0x19593d65
Tap card again.
Found card: 0x19593d65
```

If no card is found, the script prompts:

```
Tap card again.
```

---

## **MIFARE® 1K Card Structure**

The **MIFARE® 1K card** consists of **16 sectors**, each with **4 blocks** (16 bytes each).  
Memory layout:

- **Blocks 0-3**: Sector 0 (First block stores manufacturer data)
- **Blocks 4-7**: Sector 1
- **Blocks 8-11**: Sector 2
- **...**
- **Blocks 60-63**: Sector 15 (Contains access keys & conditions)

For authentication, use **Key A** or **Key B** stored in the last block of each sector.

---

## **MIFARE® 1K Authentication & Security**

1. **Authenticate** before reading/writing.
2. Use **GNetPlus SAVE_KEY command** to store keys securely.
3. Blocks are **protected** by access conditions.
4. **Keys should not be stored in the same sector** as sensitive data.

For further details, refer to:

- **[MIFARE Application Programming Guide](./TM970014_MifareAppliactionProgrammingGuide_REV_H.pdf)**
- **[MIFARE Demo Quick Start](./TM970018_Mifare%20Demo%20Quick%20Start.pdf)**

---

## **License**

This project is licensed under **GNU Lesser General Public License v3.0 or later (LGPL-3.0-or-later)**.  
See [COPYING](./COPYING) for full details.

---

## **Documentation & References**

For more details, refer to:

- **[GNetPlus Communication Protocol](./TM970013_GNetPlusCommunicationProtocol_REV_D.pdf)**
- **[MIFARE Application Guide](./TM970014_MifareAppliactionProgrammingGuide_REV_H.pdf)**
- **[MIFARE RWD Specification](./TM970023_RWD_SPEC.pdf)**
- **[MF10 Instruction Sheet](./TM951179_MF10_Instruction.pdf)**

For further information, visit: [GIGA-TMS Inc.](http://www.gigatms.com.tw)

---

## **Author & Credits**

**Original Authors:**

- **Chow Loong Jin** (<lchow@redhat.com>)
- **Harish Pillay** (<hpillay@redhat.com>)

**Adapted & Maintained by:**

- **Spark Drago** (<https://github.com/SparkDrago05>)

---
