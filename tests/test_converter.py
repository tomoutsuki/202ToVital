import contextlib
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
from poison202_to_vital.convert import convert, lfo_free_rate_hz, supersaw_blend, supersaw_outer_cents
from poison202_to_vital.profile import Profile

MATERIALS = Path(__file__).resolve().parents[2] / '.materials'


def encode(records):
    bodies = []
    for name, parameters in records:
        body = name.encode()[:12].ljust(16, b'\0')
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

    def test_nonzero_name_padding_is_not_text(self):
        raw = bytearray(encode([('Name', [('GAIN', 1)])]))
        raw[35] = 38
        self.assertEqual(poison.parse(raw).presets[0].name, 'Name')

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
        match = next(p for p in bank.presets if p.name == 'Pretty Pluck')
        self.assertEqual(single.presets[0].parameters, match.parameters)


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

    def test_supersaw_uses_fitted_mix_and_detune_curves(self):
        zero = convert(source(O1TY=4, O1PW=0, O1PM=0)).preset['settings']
        middle = convert(source(O1TY=4, O1PW=.5, O1PM=.5)).preset['settings']
        full = convert(source(O1TY=4, O1PW=1, O1PM=1)).preset['settings']

        self.assertEqual(zero['osc_1_unison_voices'], 7)
        self.assertAlmostEqual(zero['osc_1_unison_blend'], 0.036917, places=5)
        self.assertEqual(zero['osc_1_unison_detune'], 0)
        self.assertEqual(zero['osc_1_detune_range'], 20)
        self.assertEqual(zero['osc_1_detune_power'], 1)
        self.assertAlmostEqual(middle['osc_1_unison_blend'], supersaw_blend(.5))
        self.assertAlmostEqual(middle['osc_1_unison_detune'] * 20, supersaw_outer_cents(.5))
        self.assertAlmostEqual(full['osc_1_unison_blend'], 0.919709, places=5)
        self.assertAlmostEqual(full['osc_1_unison_detune'] * 20, 176.686, places=3)

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

    def test_profile_validation(self):
        for values in [{'envelope_exponent': math.nan}, {'cutoff_max_hz': 10}, {'envelope_max_seconds': 40},
                       {'fine_tune_cents': 'wrong'}, {'supersaw_detune_range_cents': 49},
                       {'supersaw_detune_power': 0}, {'lfo_rate_exponent': 0},
                       {'waveform_order': ['sine']}]:
            with self.assertRaises(ValueError):
                Profile(**values)
        for bpm in (0, 301, math.inf, math.nan):
            with self.assertRaises(ValueError):
                convert(source(), bpm=bpm)

    def test_assets_and_determinism(self):
        import base64
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


if __name__ == '__main__':
    unittest.main()
