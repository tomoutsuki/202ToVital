"""Best-effort mappings; all unknown Poison laws are reported, never asserted exact."""
from dataclasses import dataclass
import math

from .poison import Preset
from .poison_schema import P202_TAG_TO_FACTORY_KEY
from .profile import Profile
from . import vital


def supersaw_detune_curve(value: float) -> float:
    """JP-8000/Szabo-style normalized Super Saw detune fit.

    Poison's controlled 0/25/50/75/100 sweep closely matched this curve. The
    fitted intercept is deliberately suppressed at zero: the available short
    Poison zero-detune recording cannot establish a real nonzero spread there.
    """
    value = max(0.0, min(1.0, value))
    if value == 0.0:
        return 0.0
    return (((((((((((10028.7312891634 * value - 50818.8652045924) * value
                    + 111363.4808729368) * value - 138150.6761080548) * value
                  + 106649.6679158292) * value - 53046.9642751875) * value
                + 17019.9518580080) * value - 3425.0836591318) * value
              + 404.2703938388) * value - 24.1878824391) * value
            + 0.6717417634) * value + 0.0030115596)


def supersaw_blend(value: float) -> float:
    """Map Poison MIX to Vital Blend by matching center/side gain ratios.

    The Poison sweep follows the JP/Szabo center and per-side gain curves.
    Vital uses a different gain law, so a direct control-value copy is wrong.
    """
    value = max(0.0, min(1.0, value))
    center = 0.99785 - 0.55366 * value
    side = 0.044372 + 1.2841 * value - 0.73764 * value * value
    ratio = side / center
    discriminant = (2.0 + ratio) ** 2 - (20.0 / 3.0) * ratio
    return ((2.0 + ratio) - math.sqrt(max(0.0, discriminant))) / 2.0


def supersaw_outer_cents(value: float) -> float:
    """Return the symmetric outer spread fitted to the asymmetric JP pair.

    Vital unison is symmetric, so use the mean absolute distance of Szabo's
    measured -201.79/+176.69-cent outer voices after applying the fitted
    Poison DETUNE curve in the frequency-ratio domain.
    """
    if value <= 0.0:
        return 0.0
    scale = supersaw_detune_curve(value)
    lower = 1200.0 * math.log2(1.0 + (0.88997686 - 1.0) * scale)
    upper = 1200.0 * math.log2(1.0 + (1.10745242 - 1.0) * scale)
    return (upper - lower) / 2.0


def vital_unison_detune_value(outer_cents: float, detune_range_cents: float) -> float:
    """Serialize Vital's quadratically scaled unison-detune control.

    Vital computes physical outer spread as
    ``detune_range * unison_detune**2``. The preset value therefore needs the
    square root of the desired cents ratio, rather than the ratio itself.
    """
    return math.sqrt(max(0.0, outer_cents / detune_range_cents))


def xmod_effective_depth(value: float, profile: Profile) -> float:
    """Map normalized Poison XMOD to Vital's effective phase-mod depth.

    The defaults deliberately preserve a linear effective-depth hypothesis.
    ``xmod_depth_max`` and ``xmod_depth_power`` make that hypothesis replaceable
    once controlled Poison/Vital sideband measurements are available.
    """
    value = max(0.0, min(1.0, value))
    return profile.xmod_depth_max * value ** profile.xmod_depth_power


def xmod_vital_amount(value: float, profile: Profile) -> float:
    """Serialize an XMOD depth for Vital's quadratically scaled FM control."""
    return math.sqrt(xmod_effective_depth(value, profile))


@dataclass(frozen=True)
class XmodModel:
    """One-way OSC2-to-OSC1 XMOD hypothesis and its dynamic controls."""
    depth: float
    velocity_depth: float
    wheel_depth: float
    wheel_enabled: bool
    profile: Profile

    @property
    def active(self) -> bool:
        return bool(self.depth or self.velocity_depth or (self.wheel_enabled and self.wheel_depth))

    @property
    def vital_amount(self) -> float:
        return xmod_vital_amount(self.depth, self.profile)

    def control_delta(self, additive_depth: float) -> float:
        """Approximate nonlinear Poison modulation at the source's full scale."""
        target = min(1.0, self.depth + max(0.0, additive_depth))
        return xmod_vital_amount(target, self.profile) - self.vital_amount


def lfo_free_rate_hz(value: float, profile: Profile) -> float:
    """Approximate Poison's measured free-running LFO RATE response.

    The controlled RATE sweep is near quadratic (2.6, 10.3, 22.6 and 40 Hz
    at 25, 50, 75 and 100). RATE zero was not measurable, so the profile's
    existing positive minimum is a Vital-safe floor rather than a Poison claim.
    """
    value = max(0.0, min(1.0, value))
    return max(profile.lfo_min_hz, profile.lfo_max_hz * value ** profile.lfo_rate_exponent)


def lfo_pitch_semitones(value: float, profile: Profile) -> float:
    """Map Poison's signed LFO pitch control through its provisional cubic law."""
    value = max(-1.0, min(1.0, value))
    return math.copysign(profile.lfo_pitch_semitones * abs(value) ** profile.lfo_pitch_exponent,
                         value)


@dataclass
class Conversion:
    preset: dict
    report: dict


class Converter:
    def __init__(self, source: Preset, profile: Profile, bpm: float):
        self.source, self.profile = source, profile
        self.preset = vital.init_preset(source.name)
        self.settings = self.preset['settings']
        self.report = {'name': source.name, 'source_index': source.index,
                       'source_slot': source.source_slot,
                       'profile': profile.to_dict(), 'parameters': {}, 'warnings': [],
                       'fidelity': 'uncalibrated approximation; no Poison audio comparison'}
        self.set('beats_per_minute', bpm / 60)
        self.warn('uncalibrated', 'Poison enum order, timing, cutoff, fine tuning, gain and modulation laws are inferred. Profile values are hypotheses, not measured calibration.')

    def warn(self, code: str, message: str):
        item = {'code': code, 'message': message}
        if item not in self.report['warnings']:
            self.report['warnings'].append(item)

    def read(self, tag: str, default: float = 0, lo: float = 0, hi: float = 1,
             *, discrete: bool = False, status: str = 'estimated') -> float:
        raw = self.source.parameters.get(tag, default)
        if tag not in self.source.parameters:
            self.warn('missing_parameter', f'{tag} absent; using {default}.')
        if not math.isfinite(raw):
            raise ValueError(f'{tag} must be finite')
        value = max(lo, min(hi, raw))
        if discrete:
            value = round(value)
        if value != raw:
            self.warn('source_range', f'{tag}={raw} is outside the expected domain; using {value}.')
        self.report['parameters'][tag] = {
            'factory_key': P202_TAG_TO_FACTORY_KEY.get(tag),
            'raw': self.source.parameters.get(tag), 'used': value, 'status': status,
        }
        return value

    def set(self, key: str, value: float):
        info = vital.schema()[key]
        if not math.isfinite(value):
            raise ValueError(f'Non-finite converted value for {key}')
        bounded = max(info['min'], min(info['max'], value))
        if info['scale'] == 'kIndexed':
            bounded = round(bounded)
        if abs(bounded - value) > 1e-7:
            self.warn('target_range', f'{key}: requested {value:g}, limited to {bounded:g}.')
        self.settings[key] = bounded

    def mod(self, source: str, destination: str, depth: float, bipolar=False) -> int | None:
        if abs(depth) < 1e-12:
            return None
        slots = self.settings['modulations']
        if len(slots) >= 64:
            raise ValueError('Conversion exceeds Vital modulation capacity')
        info = vital.schema()[destination]
        # Bipolar Vital subtracts 0.5 rather than rescaling the source to +/-1.
        amount = depth / (info['max'] - info['min']) * (2 if bipolar else 1)
        slots.append({'source': source, 'destination': destination})
        number = len(slots)
        self.set(f'modulation_{number}_amount', amount)
        self.set(f'modulation_{number}_bipolar', int(bipolar))
        return number

    def envelope(self, number: int, tag: str):
        for suffix, target in [('AT', 'attack'), ('DE', 'decay'), ('RE', 'release')]:
            seconds = self.profile.seconds(self.read(tag + suffix))
            self.set(f'env_{number}_{target}', seconds ** .25)
        self.set(f'env_{number}_sustain', self.read(tag + 'SU', 1))

    def cutoff(self, value: float) -> float:
        p = self.profile
        hz = p.cutoff_min_hz * (p.cutoff_max_hz / p.cutoff_min_hz) ** value
        return 69 + 12 * math.log2(hz / 440)

    def tempo(self, prefix: str, value: float):
        # Observed UI sequence, explicitly uncertain in Poison202Features section 4.5.
        divisions = [8, 6, 4, 3, 2, 1.5, 1, .75, .5, .375, 1/3, 5/16,
                     .25, 3/16, 1/6, .125, 1/12, 1/16, 1/24, 1/32, 1/48, 1/64]
        division = divisions[round(value * (len(divisions) - 1))]
        lo = int(vital.schema()[prefix + '_tempo']['min'])
        candidates = [(abs(math.log2((2 ** (6 - t) * multiplier) / division)), sync, t)
                      for t in range(max(1, lo), 13)
                      for sync, multiplier in [(1, 1), (2, 1.5), (3, 2/3)]]
        error, sync, tempo = min(candidates)
        self.set(prefix + '_sync', sync)
        self.set(prefix + '_tempo', tempo)
        self.warn('tempo_assumption', 'Tempo rate is interpreted as a normalized index into the unverified UI division list; nearest Vital division used.')
        if error > 1e-6:
            self.warn('tempo_quantized', f'{prefix}: {division:g} whole notes has no exact supported division.')

    def oscillators(self, serial: bool):
        p = self.profile
        balance = self.read('BLNC', lo=-1)
        levels = [(.5 * (1 - balance)) ** .5, (.5 * (1 + balance)) ** .5]
        for i, level in enumerate(levels, 1):
            prefix, tag = f'osc_{i}', f'O{i}'
            shape = p.waveform_order[int(self.read(tag + 'TY', hi=4, discrete=True))]
            width = self.read(tag + 'PW')
            pwm = self.read(tag + 'PM')
            # A Poison Super Saw remains one Vital oscillator. Its embedded
            # JP-inspired single-cycle wavetable provides the spectral color;
            # unison supplies the seven independently detuned voices.
            wavetable_shape = 'jp_inspired_supersaw' if shape == 'supersaw' else shape
            self.settings['wavetables'][i-1] = vital.wavetable(wavetable_shape, .5 + .49 * width)
            self.set(prefix + '_on', 1)
            self.set(prefix + '_transpose', self.read(tag + 'PI', lo=-24, hi=24, discrete=True))
            self.set(prefix + '_tune', self.read(tag + 'TU', lo=-1) * p.fine_tune_cents / 100)
            self.set(prefix + '_destination', 0 if serial else i - 1)
            self.set(prefix + '_stereo_spread', 0)
            self.set(prefix + '_random_phase', 0)
            if shape == 'supersaw':
                self.set(prefix + '_unison_voices', 7)
                self.set(prefix + '_stack_style', 0)
                self.set(prefix + '_unison_blend', supersaw_blend(width))
                self.set(prefix + '_detune_range', p.supersaw_detune_range_cents)
                self.set(prefix + '_detune_power', p.supersaw_detune_power)
                outer_cents = supersaw_outer_cents(pwm)
                self.set(prefix + '_unison_detune', vital_unison_detune_value(outer_cents, p.supersaw_detune_range_cents))
                self.set(prefix + '_phase', .5)
                self.set(prefix + '_random_phase', 1)
                self.warn('supersaw', f'Seven-voice Vital unison stays in the corresponding oscillator slot and uses the embedded JP-8000 Inspired HP2 wavetable, fitted nonlinear Poison MIX/DETUNE curves, detune power {p.supersaw_detune_power:g}, zero stereo spread, and random phase. Vital unison is symmetric, and absolute loudness remains approximate.')
            elif shape == 'pulse' and pwm:
                self.warn('unsupported', f'{tag}PM: dynamic PWM routing is unknown; static pulse width is retained.')
            # Parallel TVA is approximated before each filter. Serial TVA1 remains
            # the main post-filter envelope; TVA2 modulates OSC2 before the sum.
            if serial and i == 1:
                self.set(prefix + '_level', level)
            else:
                self.set(prefix + '_level', 0)
                self.mod(f'env_{i+1}', prefix + '_level', level)
            self.envelope(i + 1, f'A{i}')
            attack = p.seconds(self.read(tag + 'PA'))
            decay = p.seconds(self.read(tag + 'PD'))
            depth = self.read(tag + 'PE', lo=-1) * p.pitch_envelope_semitones
            if depth and attack + decay:
                duration = max(attack + decay, 1 / 512)
                # One-shot LFOs leave all six ADSRs available for amp/filter behavior.
                points = [(0, 0), (attack / duration, 1), (1, 0)]
                lfo_number = i + 2
                self.settings['lfos'][lfo_number - 1] = vital.line(f'Pitch AD {i}', points)
                self.set(f'lfo_{lfo_number}_sync', 0)
                self.set(f'lfo_{lfo_number}_sync_type', 2)
                self.set(f'lfo_{lfo_number}_frequency', -math.log2(duration))
                self.set(f'lfo_{lfo_number}_smooth_mode', 0)
                self.set(f'lfo_{lfo_number}_smooth_time', -10)
                self.mod(f'lfo_{lfo_number}', prefix + '_transpose', depth)
        if serial:
            self.envelope(1, 'A1')
            self.warn('series_routing', 'Series: OSC2 TVA precedes filter sum; TVA1 controls final voice output. Vital envelope shapes and gain law differ.')
        else:
            # Vital's mandatory envelope must not cut a branch off before its release.
            release = max(self.settings['env_2_release'], self.settings['env_3_release'])
            for target, value in [('attack', 0), ('decay', 0), ('sustain', 1), ('release', release)]:
                self.set(f'env_1_{target}', value)
            self.warn('parallel_tva', 'Independent TVA envelopes are applied before their filters and multiplied by Vital ENV1 on release; filter-tail and gain contours differ.')
        self.warn('envelope_shape', 'Vital level and main envelope gains are squared; Poison envelope curvature is unmeasured.')

    def filters(self, serial: bool):
        for i in (1, 2):
            tag, prefix = f'F{i}', f'filter_{i}'
            shape = self.profile.filter_order[int(self.read(tag + 'TY', default=1, hi=5, discrete=True))]
            self.set(prefix + '_on', int(shape != 'off'))
            self.set(prefix + '_model', 0)
            style, blend = {'off': (0, 0), 'lp': (0, 0), 'bp': (0, 1), 'hp': (0, 2),
                            'peak': (4, 1), 'notch': (2, 1)}[shape]
            self.set(prefix + '_style', style)
            self.set(prefix + '_blend', blend)
            self.set(prefix + '_cutoff', self.cutoff(self.read(tag + 'CU', 1)))
            self.set(prefix + '_resonance', self.read(tag + 'RS'))
            self.set(prefix + '_keytrack', self.read(tag + 'KB'))
            self.envelope(i+3, tag)
            self.mod(f'env_{i+3}', prefix + '_cutoff', self.read(tag + 'EN', lo=-1) * self.profile.filter_envelope_semitones)
        self.set('filter_2_filter_input', int(serial))
        if self.read('PAIR', discrete=True):
            self.warn('unsupported', 'TVF PAIRED semantics are unknown; the two stored filters are retained without inventing control mirroring or extra poles.')
        if self.read('SOFT', discrete=True):
            self.warn('unsupported', 'SOFT RESO has no verified equivalent; Vital Analog resonance is used.')

    def interactions(self):
        xmod = self.read('XMOD')
        ring = self.read('RING', discrete=True)
        sync = self.read('SYNC', discrete=True)
        velocity_depth = self.read('VELX')
        wheel_enabled = bool(self.read('MXFM', discrete=True))
        wheel_depth = self.read('MDEP', 1)
        model = XmodModel(xmod, velocity_depth, wheel_depth, wheel_enabled, self.profile)
        supersaw = any(self.settings.get(f'osc_{number}_unison_voices', 1) > 1
                       for number in (1, 2))
        xmod_report = {
            'source_mode': 'Poison XMOD',
            'carrier': 'OSC1',
            'modulator': 'OSC2',
            'conversion': 'Vital FM from OSC2',
            'vital_distortion_type': 7,
            'raw_depth': self.source.parameters.get('XMOD'),
            'normalized_depth': xmod,
            'effective_depth': xmod_effective_depth(xmod, self.profile),
            'vital_fm_amount': model.vital_amount,
            'depth_curve': {
                'maximum': self.profile.xmod_depth_max,
                'power': self.profile.xmod_depth_power,
                'vital_serialization': 'sqrt(maximum * normalized_depth ** power)',
            },
            'velocity': {
                'source_depth': velocity_depth,
                'vital_amount_delta': model.control_delta(velocity_depth),
                'confidence': 'approximate',
            },
            'mod_wheel': {
                'enabled': wheel_enabled,
                'source_depth': wheel_depth,
                'vital_amount_delta': model.control_delta(wheel_depth) if wheel_enabled else 0.0,
                'confidence': 'approximate',
            },
            'confidence': {
                'carrier_modulator_direction': 'hypothesis',
                'static_depth': 'profiled hypothesis',
                'dynamic_depth': 'approximate endpoint match',
                'phase_and_smoothing': 'unverified',
                'supersaw_interaction': 'unverified' if supersaw and model.active else 'not applicable',
            },
            'status': 'inactive',
        }
        self.report['cross_modulation'] = xmod_report
        # Vital only permits one phase-distortion mode per oscillator.
        if ring:
            self.set('osc_1_distortion_type', 10)  # RM <- OSC2
            self.set('osc_1_distortion_amount', 1)
            self.warn('ring', 'Ring modulation assumes OSC1 carrier and OSC2 modulator.')
            if model.active:
                xmod_report['status'] = 'omitted: ring modulation has priority'
                self.warn('unsupported', 'Ring and XMOD are both active; Vital has one phase slot, so ring takes precedence and static/dynamic XMOD are omitted.')
        elif model.active:
            self.set('osc_1_distortion_type', 7)  # FM <- OSC2
            self.set('osc_1_distortion_amount', model.vital_amount)
            velocity_delta = model.control_delta(velocity_depth)
            wheel_delta = model.control_delta(wheel_depth) if wheel_enabled else 0.0
            self.mod('velocity', 'osc_1_distortion_amount', velocity_delta)
            self.mod('mod_wheel', 'osc_1_distortion_amount', wheel_delta)
            xmod_report['status'] = 'converted'
            self.warn('xfm', 'XMOD uses the profile depth curve and Vital FM from OSC2 into OSC1. Carrier direction, Poison algorithm, phase behavior and smoothing remain unverified.')
            if velocity_depth or wheel_enabled:
                self.warn('xfm_dynamic', 'Velocity and mod wheel target the FM amount with endpoint-matched control deltas. Combined modulation and the nonlinear response between endpoints remain approximate.')
            if supersaw:
                self.warn('xfm_supersaw', 'XMOD with Super Saw is experimental: Vital modulates its unison rendering, but Poison may cross-modulate internal Super Saw voices differently.')
        if sync:
            self.warn('unsupported', 'Poison oscillator-to-oscillator hard sync is not reproduced by Vital self-sync; SYNC is omitted.')

    def lfos(self):
        # RETR is recorded for auditability but the export policy intentionally
        # resets every Vital LFO per note, including Poison RETRIG OFF patches.
        self.read('RETR', discrete=True)
        for i in (1, 2):
            tag, prefix = f'L{i}', f'lfo_{i}'
            shape = self.profile.lfo_order[int(self.read(tag + 'TY', hi=5, discrete=True))]
            rate = self.read(tag + 'FQ', .5)
            frequency = math.log2(lfo_free_rate_hz(rate, self.profile))
            source = f'random_{i}' if shape == 'random' else prefix
            self.set(source + '_frequency', frequency)
            # Vital sync_type 0 is per-note trigger/reset for both SynthLfo
            # and RandomLfo. sync below independently selects free vs tempo rate.
            self.set(source + '_sync_type', 0)
            self.set(source + '_sync', 0)
            if self.read(f'TSL{i}', discrete=True):
                self.tempo(source, rate)
            fade = self.read(tag + 'FD') * 8
            if shape == 'random':
                self.set(source + '_style', 1)
                if fade:
                    self.warn('unsupported', f'{tag}FD: random-source fade is not reproduced.')
            else:
                self.set(prefix + '_fade_time', fade)
                self.set(prefix + '_phase', 0)
                if shape == 'sine':
                    self.settings['lfos'][i-1] = vital.sine_lfo()
                else:
                    points = {'triangle': [(0, 0), (.5, 1), (1, 0)],
                              'saw': [(0, 1), (1, 0)],
                              'square': [(0, 1), (.5, 1), (.5, 0), (1, 0)],
                              'trapezoid': [(0, 0), (.125, 0), (.375, 1), (.625, 1), (.875, 0), (1, 0)]}[shape]
                    self.settings['lfos'][i-1] = vital.line(shape, points)
                self.set(prefix + '_smooth_mode', 0)
                self.set(prefix + '_smooth_time', -10)
            slots = []
            pitch = lfo_pitch_semitones(self.read(tag + '>P', lo=-1), self.profile)
            filter_depth = self.read(tag + '>F', lo=-1) * self.profile.filter_envelope_semitones
            amp_depth = self.read(tag + '>A', lo=-1) * .5
            for branch in (1, 2):
                for target, depth in [(f'osc_{branch}_transpose', pitch),
                                      (f'filter_{branch}_cutoff', filter_depth),
                                      (f'osc_{branch}_level', amp_depth)]:
                    slot = self.mod(source, target, depth, bipolar=True)
                    if slot:
                        slots.append(slot)
            if self.read(f'MLF{i}', discrete=True) and slots:
                depth = self.read('MDEP', 1)
                for slot in slots:
                    amount = self.settings[f'modulation_{slot}_amount']
                    self.mod('mod_wheel', f'modulation_{slot}_amount', amount * depth)
                self.warn('modwheel_lfo', 'Mod wheel adds to existing LFO depth; Poison wheel behavior is unmeasured.')
        if self.read('LXFM'):
            self.warn('unsupported', 'LFO cross-frequency modulation direction and law are unknown; LXFM is omitted.')
        self.warn('lfo_retrigger_policy', 'Vital normal LFOs reset per note at phase zero and random LFOs reset per note. Poison RETR is recorded but does not change this export policy.')
        self.warn('lfo_routing', f'Each Poison LFO is routed to both oscillator branches for pitch, filter and amplitude. Pitch uses the provisional signed power curve exponent {self.profile.lfo_pitch_exponent:g}; filter and amp depths remain linear estimates. Reset-phase offset still needs measurement, and amp modulation is additive at oscillator level.')

    def performance(self):
        p = self.profile
        self.set('polyphony', 1 if self.read('SOLO', discrete=True) else 24)
        self.set('legato', self.read('LGTO', discrete=True))
        self.set('pitch_bend_range', self.read('BEND', 2, hi=24, lo=2, discrete=True))
        porta = self.read('PORT')
        self.set('portamento_time', math.log2(p.portamento_max_seconds * porta ** 3) if porta else -10)
        self.set('portamento_force', self.read('SLID', discrete=True))
        self.set('velocity_track', self.read('VELA'))
        velocity_filter = self.read('VELF') * p.filter_envelope_semitones
        for i in (1, 2):
            self.mod('velocity', f'filter_{i}_cutoff', velocity_filter)
        gain = self.read('GAIN', 1, hi=2)
        # Vital volume is (dB + 80)^2, not a linear 0..1 knob.
        self.set('volume', 0 if gain == 0 else (max(-80, p.output_gain_db + 20 * math.log10(gain)) + 80) ** 2)
        self.warn('output_gain', f'Patch gain is assumed linear; {p.output_gain_db:g} dB output offset provides adjustable headroom. Original loudness is unmeasured.')
        wheel = self.read('MDEP', 1)
        for i in (1, 2):
            if self.read(f'MFI{i}', discrete=True):
                self.mod('mod_wheel', f'filter_{i}_cutoff', wheel * p.filter_envelope_semitones)
        if self.read('MPI2', discrete=True):
            self.mod('mod_wheel', 'osc_2_transpose', wheel * 24)
        sub = self.read('SMIX')
        serial = bool(self.settings.get('filter_2_filter_input'))
        self.set('osc_3_on', int(sub > 0))
        self.set('osc_3_level', math.sqrt(sub) if serial else 0)
        if not serial:
            self.mod('env_2', 'osc_3_level', math.sqrt(sub))
        self.set('osc_3_transpose', -24 if self.read('STYP', discrete=True) else -12)
        self.settings['wavetables'][2] = vital.wavetable('sine')
        self.set('osc_3_destination', 0)
        self.set('osc_3_stereo_spread', 0)
        noise = self.read('NMIX')
        self.set('sample_on', int(noise > 0))
        self.set('sample_level', math.sqrt(noise) if serial else 0)
        if not serial:
            self.mod('env_2', 'sample_level', math.sqrt(noise))
        self.set('sample_destination', 0)
        self.set('sample_loop', 1)
        self.set('sample_random_phase', 1)
        if noise:
            self.settings['sample'] = vital.noise_sample()
        if noise or sub:
            self.warn('sub_noise', 'Sub uses a sine; sub/noise feed filter 1 and follow TVA1. Original waveform/injection is unknown. Noise loops a deterministic one-second sample.')
        if 'KPOS' in self.source.parameters:
            self.read('KPOS', hi=127, status='non_sonic')

    def effects(self):
        enabled = self.read('FXON', 1, discrete=True)
        for group in range(1, 5):
            mode = self.read(f'FX{group}S', hi=1 if group == 4 else 2, discrete=True)
            level = self.read(f'FX{group}L')
            a, b = self.read(f'F{group}P1'), self.read(f'F{group}P2')
            if not enabled or not mode:
                continue
            self.warn('effects', 'FX selectors and PARAM1/PARAM2 roles are inferred; effect algorithms and processing order differ.')
            if group == 1:
                self.set('distortion_on', 1)
                self.set('distortion_type', 0 if mode == 1 else 4)
                self.set('distortion_mix', level)
                self.set('distortion_drive', a * 30)
                if mode == 1:
                    self.set('distortion_filter_order', 2)
                    self.set('distortion_filter_cutoff', self.cutoff(b))
                else:
                    self.warn('unsupported', 'Crusher PARAM2 is omitted: Vital bit-crush uses drive and cannot simultaneously match Poison rate reduction.')
            elif group == 2:
                prefix = 'chorus' if mode == 1 else 'flanger'
                self.set(prefix + '_on', 1)
                self.set(prefix + '_sync', 0)
                self.set(prefix + '_frequency', -5 + 7 * a)
                self.set(prefix + '_dry_wet', level if mode == 1 else level * .5)
                self.set(prefix + '_mod_depth', b)
            elif group == 3:
                self.set('delay_on', 1)
                self.set('delay_style', 0 if mode == 1 else 2)
                self.set('delay_dry_wet', level)
                self.set('delay_feedback', b * .95)
                self.set('delay_sync', 0)
                self.set('delay_aux_sync', 0)
                freq = -math.log2(.001953125 * 1024 ** a)
                self.set('delay_frequency', freq)
                self.set('delay_aux_frequency', freq)
                if self.source.parameters.get('TSDE', 0):
                    self.tempo('delay', a)
                    self.set('delay_aux_sync', self.settings['delay_sync'])
                    self.set('delay_aux_tempo', self.settings['delay_tempo'])
            else:
                self.set('reverb_on', 1)
                self.set('reverb_dry_wet', level)
                self.set('reverb_size', a)
                self.set('reverb_decay_time', -3 + a * 6)
                self.set('reverb_high_shelf_gain', -6 * b)
        self.read('TSDE', discrete=True)
        eq = [self.read(tag, lo=-1) for tag in ('EQLO', 'EQMD', 'EQHI')]
        self.set('eq_on', int(any(eq)))
        for band, gain in zip(('low', 'band', 'high'), eq):
            self.set(f'eq_{band}_gain', gain * self.profile.eq_gain_db)
        if any(eq):
            self.warn('eq', 'EQ gain range assumes +/-12 dB (profile adjustable); Vital default band frequencies are used.')

    def run(self) -> Conversion:
        serial = bool(self.read('STRU', discrete=True))
        self.oscillators(serial)
        self.filters(serial)
        self.interactions()
        self.lfos()
        self.performance()
        self.effects()
        for tag, value in self.source.parameters.items():
            if tag not in self.report['parameters']:
                self.report['parameters'][tag] = {
                    'factory_key': P202_TAG_TO_FACTORY_KEY.get(tag),
                    'raw': value, 'status': 'unmapped',
                }
                self.warn('unknown_parameter', f'Unknown tag {tag}={value}; preserved in report, not converted.')
        self.preset['comments'] = 'Poison-202 conversion (' + self.profile.name + '). Approximate; see report. ' + ' '.join(w['message'] for w in self.report['warnings'])
        vital.validate(self.preset)
        return Conversion(self.preset, self.report)


def convert(source: Preset, profile: Profile | None = None, bpm: float = 120) -> Conversion:
    if not math.isfinite(bpm) or not 20 <= bpm <= 300:
        raise ValueError('BPM must be between 20 and 300')
    return Converter(source, profile or Profile(), bpm).run()
