import base64
import contextlib
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from poison202_to_vital import poison, vital
from poison202_to_vital.cli import main
from poison202_to_vital.convert import (convert, lfo_free_rate_hz, lfo_pitch_semitones,
                                         supersaw_blend,
                                         supersaw_outer_cents,
                                         vital_unison_detune_value,
                                         xmod_effective_depth, xmod_vital_amount)
from poison202_to_vital.poison_schema import (FACTORY_ONLY_PARAMETER_KEYS,
                                               FACTORY_PRESET_COUNT,
                                               P202_PARAMETER_COUNT,
                                               P202_TAG_TO_FACTORY_KEY)
from poison202_to_vital.profile import Profile

MATERIALS = Path(__file__).resolve().parents[2] / '.materials'


def encode(records):
    bodies = []
    for default_slot, record in enumerate(records):
        name, parameters, *explicit_slot = record
        slot = explicit_slot[0] if explicit_slot else default_slot
        body = name.encode()[:15].ljust(15, b'\0') + bytes([slot])
        body += b''.join(tag.encode() + struct.pack('<f', value) for tag, value in parameters)
        bodies.append(body + b'####')
    start = 16 + len(records) * 4
    offsets = []
    for body in bodies:
        offsets.append(start)
        start += len(body)
    return b'P202' + struct.pack('<HH', len(records), 16) + bytes(8) + struct.pack(f'<{len(records)}I', *offsets) + b''.join(bodies)


def source(**overrides):
    parameters = {'O1TY': 2, 'O2TY': 2, 'BLNC': -1, 'F1TY': 0, 'F2TY': 0,
                  'A1SU': 1, 'A2SU': 1, 'GAIN': 1, 'FXON': 0}
    parameters.update(overrides)
    return poison.Preset('Test sine', parameters, 1, 20)


class ParserTests(unittest.TestCase):
    def test_single_and_bank_and_tag_order(self):
        bank = poison.parse(encode([('First', [('GAIN', 1), ('O1PI', -12)]),
                                    ('Second', [('O1PI', 24), ('GAIN', .5)])]))
        self.assertEqual([p.name for p in bank.presets], ['First', 'Second'])
        self.assertEqual(bank.presets[1].parameters['O1PI'], 24)
        self.assertEqual(bank.presets[0].parameters['O1PI'], -12)
        self.assertEqual(bank.presets[0].record_size, bank.presets[1].offset - bank.presets[0].offset)
        self.assertEqual([preset.source_slot for preset in bank.presets], [0, 1])

    def test_nonzero_name_padding_is_not_text(self):
        raw = bytearray(encode([('Name', [('GAIN', 1)])]))
        raw[30] = 38
        preset = poison.parse(raw).presets[0]
        self.assertEqual(preset.name, 'Name')
        self.assertEqual(preset.source_slot, 0)

    def test_source_slot_is_not_part_of_a_full_length_name(self):
        preset = poison.parse(encode([('FifteenByteName', [('GAIN', 1)], 247)])).presets[0]
        self.assertEqual(preset.name, 'FifteenByteName')
        self.assertEqual(preset.raw_name, b'FifteenByteName')
        self.assertEqual(preset.source_slot, 247)

    def test_reject_corruption(self):
        original = encode([('One', [('GAIN', 1)]), ('Two', [('GAIN', 2)])])
        variants = [b'', b'not p202', original[:-1], original + b'x']
        for position, replacement in [(4, b'\0\0'), (6, b'\x20\0'), (16, struct.pack('<I', 0)),
                                      (20, struct.pack('<I', 999999))]:
            data = bytearray(original)
            data[position:position+len(replacement)] = replacement
            variants.append(data)
        for value in variants:
            with self.subTest(value=value[:24]), self.assertRaises(poison.FormatError):
                poison.parse(value)

    def test_nonfinite_duplicate_and_bad_tags(self):
        for params in [[('GAIN', math.nan)], [('GAIN', math.inf)], [('GAIN', 1), ('GAIN', 2)], [('BAD\x00', 1)]]:
            with self.assertRaises(poison.FormatError):
                poison.parse(encode([('Test', params)]))

    @unittest.skipUnless((MATERIALS / 'SynthUserBank.p202').exists(), 'User samples not available')
    def test_real_exports(self):
        bank = poison.load(MATERIALS / 'SynthUserBank.p202')
        single = poison.load(MATERIALS / 'SinglePreset.p202')
        self.assertEqual(len(bank.presets), 47)
        self.assertTrue(all(len(p.parameters) == 106 for p in bank.presets))
        self.assertTrue(all(set(p.parameters) == set(P202_TAG_TO_FACTORY_KEY)
                            for p in bank.presets))
        self.assertEqual([p.source_slot for p in bank.presets], list(range(47)))
        match = next(p for p in bank.presets if p.name == 'Pretty Pluck')
        self.assertEqual(single.presets[0].parameters, match.parameters)
        self.assertEqual(single.presets[0].source_slot, match.source_slot)
        self.assertEqual(match.source_slot, 38)

    def test_factory_schema_crosswalk_is_complete(self):
        self.assertEqual(P202_PARAMETER_COUNT, 106)
        self.assertEqual(len(P202_TAG_TO_FACTORY_KEY), 106)
        self.assertEqual(len(set(P202_TAG_TO_FACTORY_KEY.values())), 106)
        self.assertEqual(FACTORY_ONLY_PARAMETER_KEYS, ('TEMPOSYNC',))
        self.assertEqual(FACTORY_PRESET_COUNT, 594)


class MappingTests(unittest.TestCase):
    def test_vital_envelope_and_volume_units(self):
        result = convert(source(A1AT=.5, GAIN=1))
        settings = result.preset['settings']
        self.assertAlmostEqual(settings['env_2_attack'] ** 4, 1.25)
        self.assertEqual(settings['volume'], 62 ** 2)
        self.assertEqual(settings['osc_1_destination'], 0)
        self.assertEqual(settings['osc_2_destination'], 1)

    def test_series_and_mono(self):
        settings = convert(source(STRU=1, SOLO=1, LGTO=1, A1AT=.5)).preset['settings']
        self.assertEqual(settings['filter_2_filter_input'], 1)
        self.assertEqual(settings['osc_2_destination'], 0)
        self.assertEqual(settings['polyphony'], 1)
        self.assertEqual(settings['legato'], 1)
        self.assertAlmostEqual(settings['env_1_attack'] ** 4, 1.25)

    def test_pitch_bipolar_depth_uses_full_range(self):
        settings = convert(source(**{'L1>P': 1})).preset['settings']
        idx = next(i for i, m in enumerate(settings['modulations'], 1) if m == {'source': 'lfo_1', 'destination': 'osc_1_transpose'})
        self.assertAlmostEqual(settings[f'modulation_{idx}_amount'] * 96 * .5, 24)
        self.assertEqual(settings[f'modulation_{idx}_bipolar'], 1)

    def test_measured_free_lfo_rate_curve_and_retrigger_policy(self):
        profile = Profile()
        self.assertAlmostEqual(lfo_free_rate_hz(.25, profile), 2.5)
        self.assertAlmostEqual(lfo_free_rate_hz(.5, profile), 10)
        self.assertAlmostEqual(lfo_free_rate_hz(.75, profile), 22.5)
        self.assertAlmostEqual(lfo_free_rate_hz(1, profile), 40)
        self.assertEqual(lfo_free_rate_hz(0, profile), .05)

        settings = convert(source(RETR=0, L1FQ=.5, **{'L1>P': -1})).preset['settings']
        self.assertAlmostEqual(settings['lfo_1_frequency'], math.log2(10))
        self.assertEqual(settings['lfo_1_sync'], 0)
        self.assertEqual(settings['lfo_1_sync_type'], 0)
        self.assertEqual(settings['lfo_1_phase'], 0)
        idx = next(i for i, mod in enumerate(settings['modulations'], 1)
                   if mod == {'source': 'lfo_1', 'destination': 'osc_1_transpose'})
        self.assertAlmostEqual(settings[f'modulation_{idx}_amount'] * 96 * .5, -24)

    def test_native_sine_lfo_dual_oscillator_routing_and_pitch_curve(self):
        profile = Profile()
        positive = .8
        negative = -.8
        result = convert(source(L1TY=1, L2TY=1,
                                **{'L1>P': positive, 'L1>F': .25,
                                   'L2>P': negative, 'L2>A': .4}), profile)
        settings = result.preset['settings']
        self.assertEqual(settings['lfos'][0], vital.sine_lfo())
        self.assertEqual(settings['lfos'][1], vital.sine_lfo())
        self.assertEqual(settings['lfos'][0]['name'], 'Sin')
        self.assertEqual(settings['lfos'][0]['num_points'], 3)
        self.assertTrue(settings['lfos'][0]['smooth'])

        def amount(source_name, destination):
            index = next(i for i, item in enumerate(settings['modulations'], 1)
                         if item == {'source': source_name, 'destination': destination})
            return settings[f'modulation_{index}_amount']

        expected_positive = 24 * positive ** profile.lfo_pitch_exponent
        expected_negative = -24 * abs(negative) ** profile.lfo_pitch_exponent
        self.assertAlmostEqual(lfo_pitch_semitones(positive, profile), expected_positive)
        self.assertAlmostEqual(lfo_pitch_semitones(negative, profile), expected_negative)
        for oscillator in (1, 2):
            destination = f'osc_{oscillator}_transpose'
            self.assertAlmostEqual(amount('lfo_1', destination) * 96 * .5, expected_positive)
            self.assertAlmostEqual(amount('lfo_2', destination) * 96 * .5, expected_negative)
        for filter_number in (1, 2):
            self.assertIn({'source': 'lfo_1', 'destination': f'filter_{filter_number}_cutoff'},
                          settings['modulations'])
        for oscillator in (1, 2):
            self.assertIn({'source': 'lfo_2', 'destination': f'osc_{oscillator}_level'},
                          settings['modulations'])

    def test_supersaw_uses_fitted_mix_and_detune_curves(self):
        profile = Profile()
        zero_result = convert(source(O1TY=4, O1PW=0, O1PM=0), profile)
        zero = zero_result.preset['settings']
        middle = convert(source(O1TY=4, O1PW=.5, O1PM=.5), profile).preset['settings']
        full = convert(source(O1TY=4, O1PW=1, O1PM=1), profile).preset['settings']

        for settings, detune in [(zero, 0), (middle, .5), (full, 1)]:
            self.assertEqual(settings['osc_1_unison_voices'], 7)
            self.assertEqual(settings['osc_1_stack_style'], 0)
            self.assertEqual(settings['osc_1_detune_range'], profile.supersaw_detune_range_cents)
            self.assertEqual(settings['osc_1_detune_power'], profile.supersaw_detune_power)
            self.assertAlmostEqual(
                settings['osc_1_unison_detune'] ** 2 * profile.supersaw_detune_range_cents,
                supersaw_outer_cents(detune), places=3)
            self.assertEqual(settings['osc_1_phase'], .5)
            self.assertEqual(settings['osc_1_random_phase'], 1)
            self.assertEqual(settings['osc_1_stereo_spread'], 0)
            frame = settings['wavetables'][0]['groups'][0]['components'][0]['keyframes'][0]
            self.assertEqual(settings['wavetables'][0]['name'], '202ToVital JP-8000 Inspired HP2')
            self.assertEqual(hashlib.sha256(base64.b64decode(frame['wave_data'])).hexdigest(),
                             '6f141c33c15a8f9c9cdd31ddc1f22fe8ac8bce0ffbcd1b26154c9ba969a30b95')
            # Muted Poison OSC2 remains OSC2 and retains its own waveform.
            self.assertEqual(settings['wavetables'][1]['name'], '202ToVital sine')

        self.assertAlmostEqual(zero['osc_1_unison_blend'], 0.036917, places=5)
        self.assertAlmostEqual(middle['osc_1_unison_blend'], supersaw_blend(.5))
        self.assertAlmostEqual(full['osc_1_unison_blend'], 0.919709, places=5)

        # Detune power 1.09 is the least-squares single-parameter fit to the
        # averaged absolute JP-8000 inner/middle/outer pairs. Vital remains
        # symmetric, so the individual +/- offsets cannot be exact.
        outer = supersaw_outer_cents(1)
        def power_scale(position):
            power = profile.supersaw_detune_power
            return math.expm1(power * position) / math.expm1(power)
        fitted = (outer * power_scale(1 / 3), outer * power_scale(2 / 3), outer)
        targets = (34.13, (112.44 + 104.41) / 2, (201.79 + 176.69) / 2)
        for actual, target in zip(fitted, targets):
            self.assertLess(abs(actual - target), 8)
        self.assertTrue(any(w['code'] == 'supersaw' for w in zero_result.report['warnings']))

    def test_each_poison_supersaw_keeps_its_vital_oscillator_slot(self):
        settings = convert(source(O1TY=4, O2TY=4, O1PW=1, O2PW=.5,
                                  O1PM=1, O2PM=.5, BLNC=0)).preset['settings']
        for number, mix, detune in [(1, 1, 1), (2, .5, .5)]:
            prefix = f'osc_{number}'
            self.assertEqual(settings[prefix + '_unison_voices'], 7)
            self.assertEqual(settings[prefix + '_stack_style'], 0)
            self.assertAlmostEqual(settings[prefix + '_unison_blend'], supersaw_blend(mix))
            self.assertAlmostEqual(settings[prefix + '_unison_detune'] ** 2 * 20,
                                   supersaw_outer_cents(detune), places=3)
            self.assertEqual(settings['wavetables'][number - 1]['name'], '202ToVital JP-8000 Inspired HP2')
        self.assertEqual(settings['osc_1_destination'], 0)
        self.assertEqual(settings['osc_2_destination'], 1)

    def test_effect_bypass_and_random_lfo(self):
        settings = convert(source(FXON=0, FX1S=1, FX1L=1, L1TY=5, **{'L1>F': .2})).preset['settings']
        self.assertNotIn('distortion_on', settings)
        self.assertEqual(settings['random_1_style'], 1)
        self.assertEqual(settings['random_1_sync_type'], 0)
        self.assertEqual(settings['random_1_sync'], 0)
        self.assertTrue(any(m['source'] == 'random_1' for m in settings['modulations']))

    def test_unknown_and_unsupported_are_reported(self):
        result = convert(source(ZZZZ=12, SYNC=1, XMOD=.5, RING=1))
        self.assertEqual(result.report['parameters']['ZZZZ']['status'], 'unmapped')
        codes = {w['code'] for w in result.report['warnings']}
        self.assertTrue({'unsupported', 'unknown_parameter', 'uncalibrated'} <= codes)
        self.assertEqual(result.preset['settings']['osc_1_distortion_type'], 10)

    def test_xmod_profile_curve_and_vital_quadratic_serialization(self):
        profile = Profile(xmod_depth_max=.64, xmod_depth_power=2)
        self.assertAlmostEqual(xmod_effective_depth(.5, profile), .16)
        self.assertAlmostEqual(xmod_vital_amount(.5, profile), .4)
        result = convert(source(XMOD=.5), profile)
        settings = result.preset['settings']
        report = result.report['cross_modulation']
        self.assertEqual(settings['osc_1_distortion_type'], 7)
        self.assertAlmostEqual(settings['osc_1_distortion_amount'], .4)
        self.assertAlmostEqual(settings['osc_1_distortion_amount'] ** 2, report['effective_depth'])
        self.assertEqual(report['carrier'], 'OSC1')
        self.assertEqual(report['modulator'], 'OSC2')
        self.assertEqual(report['status'], 'converted')

    def test_xmod_velocity_and_wheel_match_profiled_endpoints(self):
        profile = Profile(xmod_depth_max=.81, xmod_depth_power=2)
        result = convert(source(XMOD=.25, VELX=.25, MXFM=1, MDEP=.5), profile)
        settings = result.preset['settings']

        def amount(source_name):
            index = next(i for i, item in enumerate(settings['modulations'], 1)
                         if item == {'source': source_name, 'destination': 'osc_1_distortion_amount'})
            return settings[f'modulation_{index}_amount']

        base = xmod_vital_amount(.25, profile)
        self.assertAlmostEqual(settings['osc_1_distortion_amount'], base)
        self.assertAlmostEqual(amount('velocity'), xmod_vital_amount(.5, profile) - base)
        self.assertAlmostEqual(amount('mod_wheel'), xmod_vital_amount(.75, profile) - base)
        self.assertTrue(any(w['code'] == 'xfm_dynamic' for w in result.report['warnings']))

    def test_ring_omits_all_xmod_routes_and_supersaw_is_reported(self):
        ring = convert(source(XMOD=0, VELX=.5, MXFM=1, MDEP=.5, RING=1))
        self.assertEqual(ring.preset['settings']['osc_1_distortion_type'], 10)
        self.assertFalse(any(mod['destination'] == 'osc_1_distortion_amount'
                             for mod in ring.preset['settings']['modulations']))
        self.assertTrue(ring.report['cross_modulation']['status'].startswith('omitted'))

        supersaw = convert(source(O2TY=4, XMOD=.5))
        self.assertTrue(any(w['code'] == 'xfm_supersaw' for w in supersaw.report['warnings']))
        self.assertEqual(supersaw.report['cross_modulation']['confidence']['supersaw_interaction'],
                         'unverified')

    def test_profile_validation(self):
        for values in [{'envelope_exponent': math.nan}, {'cutoff_max_hz': 10}, {'envelope_max_seconds': 40},
                       {'fine_tune_cents': 'wrong'}, {'supersaw_detune_range_cents': 49},
                       {'supersaw_detune_power': 0}, {'xmod_depth_max': 1.1},
                       {'xmod_depth_power': 0}, {'lfo_rate_exponent': 0}, {'lfo_pitch_exponent': 0},
                       {'waveform_order': ['sine']}]:
            with self.assertRaises(ValueError):
                Profile(**values)
        for bpm in (0, 301, math.inf, math.nan):
            with self.assertRaises(ValueError):
                convert(source(), bpm=bpm)

    def test_assets_and_determinism(self):
        result = convert(source(SMIX=.5, NMIX=.25))
        settings = result.preset['settings']
        frame = settings['wavetables'][0]['groups'][0]['components'][0]['keyframes'][0]
        wave = struct.unpack('<2048f', base64.b64decode(frame['wave_data']))
        self.assertAlmostEqual(wave[512], 1)
        self.assertEqual(len(base64.b64decode(settings['sample']['samples'])), settings['sample']['length'] * 2)
        self.assertEqual(vital.serialize(result.preset), vital.serialize(convert(source(SMIX=.5, NMIX=.25)).preset))

    @unittest.skipUnless((MATERIALS / 'SynthUserBank.p202').exists(), 'User samples not available')
    def test_all_real_presets_validate(self):
        for preset in poison.load(MATERIALS / 'SynthUserBank.p202').presets:
            with self.subTest(preset=preset.name):
                result = convert(preset)
                vital.validate(result.preset)
                self.assertEqual(len(result.report['parameters']), 106)
                self.assertNotIn('unknown_parameter', {w['code'] for w in result.report['warnings']})


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input = self.root / 'test.p202'
        self.input.write_bytes(encode([('Same/name', [('GAIN', 1)]), ('Same/name', [('GAIN', .5)])]))

    def run_cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return main([str(x) for x in args])

    def test_bank_zip_layout_and_duplicates(self):
        out = self.root / 'Test.vitalbank'
        self.assertEqual(self.run_cli('convert', self.input, '-o', out), 0)
        with zipfile.ZipFile(out) as archive:
            self.assertEqual(archive.namelist(), ['Test/Presets/001 Same_name.vital', 'Test/Presets/002 Same_name.vital'])
            self.assertIsNone(archive.testzip())
            for name in archive.namelist():
                vital.validate(json.loads(archive.read(name)))
        self.assertEqual(json.loads(Path(str(out) + '.report.json').read_text())['preset_count'], 2)
        self.assertEqual(self.run_cli('convert', self.input, '-o', out), 2)
        self.assertEqual(self.run_cli('convert', self.input, '-o', out, '--force'), 0)

    def test_selection_directory_and_strict(self):
        out = self.root / 'one.vital'
        self.assertEqual(self.run_cli('convert', self.input, '-o', out), 2)
        self.assertEqual(self.run_cli('convert', self.input, '-o', out, '--preset', '0'), 2)
        self.assertEqual(self.run_cli('convert', self.input, '-o', out, '--preset', 'Same/name'), 2)
        self.assertEqual(self.run_cli('convert', self.input, '-o', out, '--preset', '1', '--strict'), 2)
        self.assertFalse(out.exists())
        self.assertEqual(self.run_cli('convert', self.input, '-o', out, '--preset', '1'), 0)
        folder = self.root / 'presets'
        self.assertEqual(self.run_cli('convert', self.input, '-o', folder, '--format', 'directory'), 0)
        self.assertEqual(len(list(folder.glob('*.vital'))), 2)

    def test_protect_input_and_report_collisions(self):
        original = self.input.read_bytes()
        out = self.root / 'bank.vitalbank'
        self.assertEqual(self.run_cli('convert', self.input, '-o', out, '--report', self.input, '--force'), 2)
        self.assertEqual(self.input.read_bytes(), original)
        self.assertEqual(self.run_cli('convert', self.input, '-o', out, '--report', out), 2)
        self.assertFalse(out.exists())

    def test_existing_report_prevents_any_write(self):
        out = self.root / 'bank.vitalbank'
        report = Path(str(out) + '.report.json')
        report.write_text('keep')
        self.assertEqual(self.run_cli('convert', self.input, '-o', out), 2)
        self.assertFalse(out.exists())
        self.assertEqual(report.read_text(), 'keep')

    def test_malformed_profile(self):
        profile = self.root / 'bad.json'
        profile.write_text('{"typo": 1}')
        self.assertEqual(self.run_cli('convert', self.input, '-o', self.root / 'a.vitalbank', '--profile', profile), 2)

    def test_inspect_shows_source_structure_midi_estimates_and_mapped_lfo_pitch(self):
        single = self.root / 'lfo.p202'
        single.write_bytes(encode([('LFO test', [('L2TY', 0), ('L2FQ', .5), ('L2>P', .8)])]))
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['inspect', str(single)]), 0)
        text = output.getvalue()
        self.assertIn('P202 file:', text)
        self.assertIn('Record: offset 20', text)
        self.assertIn('[LFO 2]', text)
        self.assertIn('Source slot: 0', text)
        self.assertIn('L2FQ / LFO2FREQ = 0.5 | normalized 0..1; MIDI≈63.500 (~64); free-rate≈10 Hz', text)
        self.assertIn('L2>P / LFO2PITCH = 0.800000012 | signed normalized -1..1; MIDI≈114.300 (~114); pitch≈', text)

        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['inspect', str(single), '--json']), 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload['file_size'], len(single.read_bytes()))
        self.assertEqual(payload['presets'][0]['source_slot'], 0)
        lfo_pitch = next(item for item in payload['presets'][0]['decoded_parameters']
                         if item['tag'] == 'L2>P')
        self.assertEqual(lfo_pitch['factory_key'], 'LFO2PITCH')
        self.assertAlmostEqual(lfo_pitch['midi_7bit_estimate'], 114.3, places=4)
        self.assertAlmostEqual(lfo_pitch['decoded']['pitch_semitones'],
                               lfo_pitch_semitones(.8, Profile()), places=5)

    def test_default_output_paths(self):
        # A multi-preset P202 defaults to a bank beside its input.
        bank_output = self.root / 'test.vitalbank'
        self.assertEqual(self.run_cli('convert', self.input), 0)
        self.assertTrue(bank_output.is_file())
        self.assertTrue(Path(str(bank_output) + '.report.json').is_file())

        # Selecting one preset instead defaults to a sibling .vital file.
        selected_output = self.root / 'test.vital'
        self.assertEqual(self.run_cli('convert', self.input, '--preset', '1'), 0)
        self.assertTrue(selected_output.is_file())
        self.assertTrue(Path(str(selected_output) + '.report.json').is_file())

        # Directory output is opt-in and uses the input stem as the directory.
        directory_input = self.root / 'directory.p202'
        directory_input.write_bytes(encode([('One', [('GAIN', 1)]), ('Two', [('GAIN', .5)])]))
        directory_output = self.root / 'directory'
        self.assertEqual(self.run_cli('convert', directory_input, '--format', 'directory'), 0)
        self.assertEqual(len(list(directory_output.glob('*.vital'))), 2)
        self.assertTrue((directory_output / 'conversion-report.json').is_file())


if __name__ == '__main__':
    unittest.main()
