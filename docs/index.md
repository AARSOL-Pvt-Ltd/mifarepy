# 📝 Welcome to **mifarepy** Documentation 🎉

Welcome to the official documentation for **mifarepy**, the lightweight and user-friendly Python library for interacting with MIFARE® RFID card readers over serial using the GNetPlus® protocol.

---

## 📖 Table of Contents

1. [Introduction](#introduction)  
2. [Features](#features)  
3. [Getting Started](#getting-started)  
   - [Installation](#installation)  
   - [Quickstart](#quickstart)  
4. [Core Concepts](#core-concepts)  
   - [Protocol Layer](#protocol-layer)  
   - [Reader API](#reader-api)  
5. [Detailed Guides](#detailed-guides)  
   - [API Reference](api.md)  
   - [Usage Guide](usage.md)  
   - [Examples](examples.md)  
   - [Installation](installation.md)  
6. [Contributing](contributing.md)  
7. [License](LICENSE)  

---

## 🚀 Introduction

`mifarepy` provides a clear, Pythonic interface to PROMAG, MF5, MF10, and other MIFARE-compatible RFID readers. Whether you are building an access-control system 🚪, an inventory tracker 📦, or simply experimenting with RFID cards 🎴 in your workshop, **mifarepy** makes it easy to send commands and interpret responses.

## ✨ Features

- **💾 Low-level protocol support:** Pack and parse GNetPlus® messages with CRC  
- **🔍 Automatic card detection:** Enable/disable event mode, wait for card arrivals  
- **🧩 Card operations:** Read/write single blocks or entire sectors  
- **⚡ Bulk reads/writes:** Map-based reads across multiple sectors or blocks  
- **🐍 Python 3.6+ support:** Works on Linux, macOS, and Windows (via COM ports)  
- **🔧 Extensible and testable:** Separation of protocol and device logic for easier testing  

## 🏁 Getting Started

### 📦 Installation

Install the latest stable release from PyPI:

```bash
pip install mifarepy
```

For active development, clone this repository and install in editable mode:

```bash
git clone https://github.com/SparkDrago05/mifarepy.git
cd mifarepy_project
pip install -e .
```

### ⚙️ Quickstart

Here is a minimal example to detect a card, read its UID, and fetch a data block:

```python
from mifarepy.reader import MifareReader

# 1. Initialize the reader on the serial port
reader = MifareReader('/dev/ttyUSB0')

# 2. Enable auto-mode and wait for a card
reader.set_auto_mode(True)
uid = reader.wait_for_card(timeout=5)
print(f"Card UID: {uid}")

# 3. Authenticate and read block 4
default_key = bytes.fromhex('FFFFFFFFFFFF')
reader.authenticate_sector(sector=1, key=default_key)
block4 = reader.read_block(4)
print(f"Block 4 (hex): {block4.hex()}")
```

## 🧠 Core Concepts

### 🔗 Protocol Layer

All GNetPlus® message framing, CRC calculations, and exceptions are implemented in `mifarepy/protocol.py`:

- **`Message`**: Base class, handles SOH, addressing, function codes, data, CRC.  
- **`QueryMessage`**: Subclass with constants for each command (e.g., `REQUEST`, `READ_BLOCK`).  
- **`ResponseMessage`**: Parses incoming replies, detects `ACK`, `NAK`, and event notifications.  
- **`gencrc()`**: Utility to compute 16-bit CRC as per the protocol specification.  

### 📡 Reader API

The high-level interface lives in `mifarepy/reader.py`:

- **`MifareReader`**: Connects to a serial port, sends queries, and returns parsed responses.  
- **Methods include:**  
  - `get_version()` 🔖  
  - `set_auto_mode()` / `wait_for_card()` ⏱️  
  - `get_sn()` 🆔  
  - `authenticate_sector()` 🔐  
  - `read_block()` / `write_block()` 📚  
  - `read_sector()` / `write_sector()` 🔄  

All methods raise `GNetPlusError` or `InvalidMessage` on protocol or hardware errors.

## 📚 Detailed Guides

- **API Reference:** Full descriptions of classes and functions — see [api.md].  
- **Usage Guide:** Common workflows and best practices — see [usage.md].  
- **Examples:** Real-world code samples — see [examples.md].  
- **Configuration and Troubleshooting:** Tips for serial-port permissions, timeouts, and error recovery.  

## 🤝 Contributing

We welcome contributions! Please read our [contributing guidelines](contributing.md) for details on setting up your development environment, code style, and submitting pull requests. ❤️

## 🏷️ License

`mifarepy` is released under the **LGPL v3.0 or later**. See the [LICENSE](LICENSE) file for full terms.
