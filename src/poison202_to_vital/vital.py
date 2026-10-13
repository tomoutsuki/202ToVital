"""Vital 1.0.6 serialization, self-contained DSP assets, and bank packaging."""
import base64
from functools import lru_cache
from importlib.resources import files
import io
import json
import math
import os
from pathlib import Path
import random
import re
import struct
import tempfile
import zipfile

VERSION = '1.0.6'
JP_INSPIRED_HP2_WAV = 'JP_inspired_HP2_fc_1p5xF0_2048.wav'


@lru_cache(maxsize=1)
def schema() -> dict:
    return json.loads(files('poison202_to_vital').joinpath('data/vital_schema.json').read_text())


def line(name: str, points: list[tuple[float, float]], smooth: bool = False) -> dict:
    # Vital stores screen-space y: 0 is the top (maximum modulation).
    return {'name': name, 'num_points': len(points),
            'points': [v for x, y in points for v in (x, 1 - y)],
            'powers': [0.0] * len(points), 'smooth': smooth}


def sine_lfo() -> dict:
    """Return Vital's built-in three-point smooth sine shape exactly."""
    return line('Sin', [(0, 0), (.5, 1), (1, 0)], smooth=True)


@lru_cache(maxsize=1)
def jp_inspired_supersaw_wave_data() -> str:
    """Load the packaged mono IEEE-float single-cycle Super Saw asset."""
    wav = files('poison202_to_vital').joinpath('data').joinpath(JP_INSPIRED_HP2_WAV).read_bytes()
    if wav[:12] != b'RIFF' + (len(wav) - 8).to_bytes(4, 'little') + b'WAVE':
        raise ValueError(f'Invalid RIFF WAV resource: {JP_INSPIRED_HP2_WAV}')
    position, fmt, payload = 12, None, None
    while position + 8 <= len(wav):
        kind = wav[position:position + 4]
        size = int.from_bytes(wav[position + 4:position + 8], 'little')
        start, end = position + 8, position + 8 + size
        if end > len(wav):
            raise ValueError(f'Truncated WAV resource: {JP_INSPIRED_HP2_WAV}')
        if kind == b'fmt ':
            fmt = wav[start:end]
        elif kind == b'data':
            payload = wav[start:end]
        position = end + size % 2
    if fmt is None or payload is None or len(fmt) < 16:
        raise ValueError(f'Missing format or data chunk in {JP_INSPIRED_HP2_WAV}')
    audio_format, channels, _rate, _byte_rate, block_align, bits = struct.unpack('<HHIIHH', fmt[:16])
    if (audio_format, channels, block_align, bits, len(payload)) != (3, 1, 4, 32, 2048 * 4):
        raise ValueError(f'Unexpected WAV format for {JP_INSPIRED_HP2_WAV}')
    samples = struct.unpack('<2048f', payload)
    if not all(math.isfinite(sample) for sample in samples):
        raise ValueError(f'Non-finite sample in {JP_INSPIRED_HP2_WAV}')
    return base64.b64encode(payload).decode('ascii')


@lru_cache(maxsize=128)
def wavetable(shape: str, width: float = 0.5) -> dict:
    if shape == 'jp_inspired_supersaw':
        data = jp_inspired_supersaw_wave_data()
        name = '202ToVital JP-8000 Inspired HP2'
    else:
        wave = []
        for i in range(2048):
            phase = i / 2048
            if shape in ('saw', 'supersaw'):
                value = 2 * phase - 1
            elif shape == 'pulse':
                value = 1.0 if phase < width else -1.0
            elif shape == 'sine':
                value = math.sin(2 * math.pi * phase)
            elif shape == 'triangle':
                value = 1 - 4 * abs(phase - 0.5)
            else:
                raise ValueError(f'Unknown waveform: {shape}')
            wave.append(value)
        data = base64.b64encode(struct.pack('<2048f', *wave)).decode('ascii')
        name = f'202ToVital {shape}'
    return {'name': name, 'author': '202ToVital', 'version': VERSION,
            'remove_all_dc': True, 'full_normalize': False,
            'groups': [{'components': [{'type': 'Wave Source', 'interpolation': 1,
                                        'interpolation_style': 0,
                                        'keyframes': [{'position': 0, 'wave_data': data}]}]}]}


@lru_cache(maxsize=1)
def noise_sample() -> dict:
    rng = random.Random(202)
    samples = [rng.randrange(-32767, 32768) for _ in range(44100)]
    return {'name': '202ToVital White Noise', 'length': len(samples), 'sample_rate': 44100,
            'samples': base64.b64encode(struct.pack(f'<{len(samples)}h', *samples)).decode('ascii')}


def init_preset(name: str) -> dict:
    # Missing scalar controls receive defaults in LoadSave::loadControls.
    # Embedded assets reset every non-scalar state regardless of previously loaded preset.
    settings = {'modulations': [], 'wavetables': [wavetable('saw') for _ in range(3)],
                'lfos': [line('Triangle', [(0, 0), (.5, 1), (1, 0)]) for _ in range(8)],
                'sample': {'name': '', 'length': 8, 'sample_rate': 44100,
                           'samples': base64.b64encode(bytes(16)).decode('ascii')}}
    return {'author': '202ToVital', 'preset_name': name, 'preset_style': '',
            'comments': '', 'synth_version': VERSION, 'settings': settings,
            **{f'macro{i}': f'MACRO {i}' for i in range(1, 5)}}


def validate(preset: dict) -> None:
    controls = schema()
    settings = preset['settings']
    for key, value in settings.items():
        if isinstance(value, (dict, list)):
            continue
        if key not in controls:
            raise ValueError(f'Unknown Vital control: {key}')
        info = controls[key]
        if not isinstance(value, (int, float)) or not math.isfinite(value) or not info['min'] <= value <= info['max']:
            raise ValueError(f'Invalid Vital value {key}={value}')
        if info['scale'] == 'kIndexed' and value != int(value):
            raise ValueError(f'Non-integer Vital selector {key}={value}')
    if len(settings['modulations']) > 64:
        raise ValueError('Vital supports at most 64 modulation connections')
    for mod in settings['modulations']:
        if mod['destination'] not in controls:
            raise ValueError(f'Unknown modulation destination: {mod["destination"]}')


def serialize(preset: dict) -> bytes:
    validate(preset)
    return (json.dumps(preset, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n').encode('utf-8')


def safe_name(name: str) -> str:
    result = re.sub(r'[^\w .()-]', '_', name, flags=re.UNICODE).strip(' .')[:100]
    if not result or result.upper().split('.')[0] in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}:
        result = 'Preset_' + result
    return result


def bundle(presets: list[dict], bank_name: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for index, preset in enumerate(presets, 1):
            path = f'{safe_name(bank_name)}/Presets/{index:03d} {safe_name(preset["preset_name"])}.vital'
            entry = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, serialize(preset))
    return buffer.getvalue()


def atomic_write(path: Path, data: bytes, force: bool = False) -> None:
    """Publish a complete file; default link operation refuses overwrite atomically."""
    path = Path(path)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f'.{path.name}.', delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        if force:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
