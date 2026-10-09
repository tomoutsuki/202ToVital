"""Explicit, replaceable assumptions for unmeasured Poison DSP scaling."""
from dataclasses import asdict, dataclass, fields
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class Profile:
    name: str = "uncalibrated-v1"
    envelope_max_seconds: float = 10.0
    envelope_exponent: float = 3.0
    cutoff_min_hz: float = 20.0
    cutoff_max_hz: float = 20000.0
    fine_tune_cents: float = 100.0
    pitch_envelope_semitones: float = 24.0
    filter_envelope_semitones: float = 64.0
    lfo_min_hz: float = 0.05
    lfo_max_hz: float = 40.0
    lfo_rate_exponent: float = 2.0
    lfo_pitch_semitones: float = 24.0
    eq_gain_db: float = 12.0
    portamento_max_seconds: float = 2.0
    output_gain_db: float = -18.0
    supersaw_detune_range_cents: float = 20.0
    supersaw_detune_power: float = 1.0
    waveform_order: tuple[str, ...] = ("saw", "pulse", "sine", "triangle", "supersaw")
    filter_order: tuple[str, ...] = ("off", "lp", "bp", "hp", "peak", "notch")
    lfo_order: tuple[str, ...] = ("triangle", "sine", "saw", "square", "trapezoid", "random")

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Profile name must be a nonempty string")
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name in ('name', 'waveform_order', 'filter_order', 'lfo_order'):
                continue
            if field.name == 'supersaw_detune_range_cents':
                if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 < value <= 48:
                    raise ValueError('Profile supersaw_detune_range_cents must be between 0 and 48')
                continue
            if field.name == 'supersaw_detune_power':
                if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 < value <= 5:
                    raise ValueError('Profile supersaw_detune_power must be between 0 and 5')
                continue
            if field.name == 'output_gain_db':
                if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not -60 <= value <= 6:
                    raise ValueError('Profile output_gain_db must be between -60 and 6 dB')
                continue
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f'Profile {field.name} must be a positive finite number')
        for name, allowed in [('waveform_order', {'saw', 'pulse', 'sine', 'triangle', 'supersaw'}),
                              ('filter_order', {'off', 'lp', 'bp', 'hp', 'peak', 'notch'}),
                              ('lfo_order', {'triangle', 'sine', 'saw', 'square', 'trapezoid', 'random'})]:
            values = getattr(self, name)
            if not isinstance(values, (tuple, list)) or len(values) != len(allowed) or set(values) != allowed:
                raise ValueError(f'Profile {name} must be a permutation of {sorted(allowed)}')
        for prefix in ('cutoff', 'lfo'):
            if getattr(self, prefix + '_max_hz') <= getattr(self, prefix + '_min_hz'):
                raise ValueError(f'{prefix}_max_hz must exceed {prefix}_min_hz')
        if self.envelope_max_seconds > 32 or self.envelope_exponent > 10:
            raise ValueError('Envelope profile exceeds supported 32 second / exponent 10 bounds')

    def seconds(self, value: float) -> float:
        return self.envelope_max_seconds * value ** self.envelope_exponent

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def load(cls, path: str | Path) -> 'Profile':
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('Profile must be a JSON object')
        unknown = set(data) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f'Unknown profile fields: {", ".join(sorted(unknown))}')
        return cls(**data)
