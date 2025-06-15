import pytest
import struct
from mifarepy.protocol import (
    gencrc,
    Message,
    QueryMessage,
    ResponseMessage,
    InvalidMessage,
    GNetPlusError,
)
from mifarepy import MifareReader
import serial


# --- Helpers for building fake serial interactions ---
class DummySerial:
    def __init__(self, to_read: bytes):
        self._to_read = to_read
        self.written = b''
        self.timeout = None

    def write(self, data: bytes):
        self.written += data

    def read(self, n: int) -> bytes:
        chunk = self._to_read[:n]
        self._to_read = self._to_read[n:]
        return chunk

    def reset_input_buffer(self):
        pass


def build_response(address: int, func: int, data: bytes) -> bytes:
    # Build a ResponseMessage bytes with CRC
    body = struct.pack('BBB', address, func, len(data)) + data
    crc = gencrc(body)
    return bytes([Message.SOH]) + body + struct.pack('>H', crc)


# --- Protocol Tests ---
def test_gencrc_empty():
    # CRC of no data should equal preset 0xFFFF
    assert gencrc(b'') == 0xFFFF


def test_message_roundtrip():
    # Message packing and unpacking
    msg = Message(0x02, 0x05, b"\xAA\xBB")
    raw = bytes(msg)
    # Simulate reading from serial
    ser = DummySerial(raw)
    parsed = Message.readfrom(ser)
    assert parsed.address == msg.address
    assert parsed.function == msg.function
    assert parsed.data == msg.data


def test_message_incomplete_header():
    ser = DummySerial(b'\x01\x02')
    with pytest.raises(InvalidMessage):
        Message.readfrom(ser)


def test_message_crc_mismatch():
    # valid header but bad CRC
    body = struct.pack('BBB', 0, 1, 1) + b'X'
    fake = bytes([Message.SOH]) + body + b'\x00\x00'
    ser = DummySerial(fake)
    with pytest.raises(InvalidMessage):
        Message.readfrom(ser)


def test_query_message_constants():
    assert QueryMessage.REQUEST == 0x20
    assert QueryMessage.GET_VERSION == 0x01


def test_response_to_error_and_ack():
    # NAK response should convert to error
    err = ResponseMessage(0, ResponseMessage.NAK, b'err')
    assert isinstance(err.to_error(), GNetPlusError)
    # ACK response should not be error
    ack = ResponseMessage(0, ResponseMessage.ACK, b'')
    assert ack.to_error() is None


# --- Reader Tests ---
@pytest.fixture(autouse=True)
def patch_serial(monkeypatch):
    # By default, serial.Serial returns a DummySerial; overwritten per-test
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: DummySerial(b''))


def test_init_failure(monkeypatch):
    class BadSerialExc(Exception): pass

    # Simulate SerialException
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: (_ for _ in ()).throw(serial.SerialException('fail')))
    with pytest.raises(RuntimeError):
        MifareReader('/dev/fake')


def test_get_version(monkeypatch):
    # Fake version string 'v1.2' in response
    resp = build_response(0, ResponseMessage.ACK, b'v1.2')
    dummy = DummySerial(resp)
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: dummy)
    r = MifareReader('/dev/ttyUSB0')
    ver = r.get_version()
    assert ver == 'v1.2'
    # Ensure correct command was sent
    sent = dummy.written
    assert bytes([Message.SOH, 0, QueryMessage.GET_VERSION, 0]) in sent


def test_set_auto_mode_success(monkeypatch):
    # Expect mode byte 0x01 back
    resp = build_response(0, ResponseMessage.ACK, b'\x01')
    dummy = DummySerial(resp)
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: dummy)
    r = MifareReader()
    out = r.set_auto_mode(True)
    assert out == b'\x01'


def test_get_sn(monkeypatch):
    # Simulate two responses: one for REQUEST, one for ANTI_COLLISION
    uid_val = 0x11223344
    # First: dummy ACK
    resp1 = build_response(0, ResponseMessage.ACK, b'')
    # Second: return LE-packed UID
    resp2 = build_response(0, ResponseMessage.ACK, struct.pack('<L', uid_val))
    dummy = DummySerial(resp1 + resp2)
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: dummy)
    r = MifareReader()
    sn = r.get_sn(endian='little', as_string=True)
    assert sn == '0x11223344'


def test_read_block_and_write_block(monkeypatch):
    # Simulate read_block returning 16 bytes of 0xAB
    data = b'\xAB' * 16
    resp_read = build_response(0, ResponseMessage.ACK, data)
    dummy = DummySerial(resp_read)
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: dummy)
    r = MifareReader()
    out_hex = r.read_block(5, raw=False)
    assert isinstance(out_hex, str) and len(out_hex) == 32
    # Now test write_block; simulate ACK
    resp_write = build_response(0, ResponseMessage.ACK, b'')
    dummy2 = DummySerial(resp_write)
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: dummy2)
    r2 = MifareReader()
    # valid write
    result = r2.write_block(3, b'A' * 16)
    assert result == ''  # no data returned, ack without payload
    # invalid length
    with pytest.raises(ValueError):
        r2.write_block(1, b'short')


def test_read_and_write_sector(monkeypatch):
    # read_sector: prepare 4 blocks of '00'
    blocks = [build_response(0, ResponseMessage.ACK, b'\x00' * 16) for _ in range(4)]
    dummy = DummySerial(b''.join(blocks))
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: dummy)
    r = MifareReader()
    sec = r.read_sector(1)
    assert isinstance(sec, dict) and len(sec) == 4
    # write_sector single blob
    resp_ack = build_response(0, ResponseMessage.ACK, b'')
    dummy2 = DummySerial(resp_ack * 3)
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: dummy2)
    r2 = MifareReader()
    # write single-block blob should call write_block 3 times
    r2.write_sector(b'\x11' * 16)
    assert dummy2.written.count(QueryMessage.WRITE_BLOCK.to_bytes(1, 'little')) == 3


def test_authenticate_sector_invalid_type():
    r = MifareReader()
    with pytest.raises(ValueError):
        r.authenticate_sector(1, b'\x00' * 6, key_type='C')


def test_authenticate_sector_invalid_length():
    r = MifareReader()
    with pytest.raises(ValueError):
        r.authenticate_sector(1, b'\x00' * 5, key_type='A')


def test_authenticate_sector_nak_on_save_key(monkeypatch):
    resp_nak = build_response(0, ResponseMessage.NAK, b'badkey')
    dummy = DummySerial(resp_nak)
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: dummy)
    r = MifareReader()
    with pytest.raises(GNetPlusError):
        r.authenticate_sector(0, b'\x01\x02\x03\x04\x05\x06', key_type='A')


def test_authenticate_sector_nak_on_auth(monkeypatch):
    resp_ack = build_response(0, ResponseMessage.ACK, b'')
    resp_nak = build_response(0, ResponseMessage.NAK, b'failauth')
    dummy = DummySerial(resp_ack + resp_nak)
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: dummy)
    r = MifareReader()
    with pytest.raises(GNetPlusError):
        r.authenticate_sector(0, b'\x01\x02\x03\x04\x05\x06', key_type='B')


def test_write_sector_dict_variant(monkeypatch):
    data_map = {0: b'\xAA' * 16, 2: b'\xBB' * 16}
    resp_ack = build_response(0, ResponseMessage.ACK, b'')
    dummy = DummySerial(resp_ack * 2)
    monkeypatch.setattr(serial, 'Serial', lambda *args, **kwargs: dummy)
    r = MifareReader()
    r.write_sector(data_map)
    write_byte = bytes([QueryMessage.WRITE_BLOCK])
    assert dummy.written.count(write_byte) == 2
