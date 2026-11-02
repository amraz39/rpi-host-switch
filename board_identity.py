#!/usr/bin/env python3
"""Read-only identity acquisition draft. Not installed or wired into startup."""
from pathlib import Path
import re

SERIAL_PATTERN = re.compile(r'^[0-9a-f]{16}$')


def _read_property(root, relative):
    # Device-tree properties are kernel-exposed bytes, generally NUL terminated.
    raw = (root / relative).read_bytes()
    if len(raw) > 256 or b'\0' in raw.rstrip(b'\0'):
        raise ValueError('Malformed device-tree property')
    try:
        return raw.rstrip(b'\0').decode('ascii')
    except UnicodeDecodeError as exc:
        raise ValueError('Non-ASCII device-tree property') from exc


def read_identity(root=Path('/proc/device-tree')):
    """Fail closed if this Pi 5 and both serial views cannot be verified."""
    root = Path(root)
    try:
        model = _read_property(root, 'model')
        normal = _read_property(root, 'serial-number').lower()
        serial64 = _read_property(root, 'chosen/rpi-serial64').lower()
    except OSError as exc:
        raise ValueError('Required hardware identity is unavailable') from exc
    if not re.fullmatch(r'Raspberry Pi 5 Model B Rev [0-9]+\.[0-9]+', model):
        raise ValueError('Unsupported or unrecognized board model')
    if (not SERIAL_PATTERN.fullmatch(normal) or normal == '0000000000000000'
            or not SERIAL_PATTERN.fullmatch(serial64) or serial64 != normal):
        raise ValueError('Hardware serial is invalid or inconsistent')
    return {'model': model, 'serial': normal}


if __name__ == '__main__':
    raise SystemExit('Read-only draft library; not a startup service or installer.')
