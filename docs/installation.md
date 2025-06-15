# 📥 Installation Guide

This guide covers different ways to install **mifarepy** and its prerequisites.

---

## ⚙️ Prerequisites

- **Python version:** 3.7 or newer 🐍  
- **pyserial:** Installed automatically via PyPI, but ensure no conflicts.  
- **Permissions (Linux):** Add your user to the `dialout` group to access serial ports:
  ```bash
  sudo usermod -aG dialout $USER
  ```
  Then log out and back in, or restart.
- **Windows:** Identify your COM port (e.g., `COM3`) and install the driver if needed.

---

## 📦 Install from PyPI

The simplest way is via pip:

```bash
pip install mifarepy
```

This installs the latest stable release and its dependencies (including `pyserial`).

---

## 🔧 Editable / Development Install

If you plan to develop or contribute to **mifarepy**, install in editable mode:

```bash
git clone https://github.com/SparkDrago05/mifarepy.git
cd mifarepy
pip install -e .
```

This links the repository into your environment so changes are picked up immediately.

---

## 📁 Manual / Source Install

For environments without PyPI access, install from source:

```bash
git clone https://github.com/SparkDrago05/mifarepy.git
cd mifarepy
# Create a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** Ensure `requirements.txt` is up to date. Alternatively, you can use `pip install -e .` as above.

---

## 🐍 Using pyproject.toml (PEP 517/518)

If you use modern tooling:

```bash
pip install build
python -m build  # will generate wheel and sdist in dist/
pip install dist/mifarepy-*.whl
```

---

## 🔍 Verify Installation

```bash
python -c "import mifarepy; print(mifarepy.__version__)"
```

You should see the installed version number, confirming a successful install.

---

For further configuration and advanced usage, see the [API Reference](api.md) and [Usage Guide](usage.md). 🎉
