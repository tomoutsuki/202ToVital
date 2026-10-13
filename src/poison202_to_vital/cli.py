"""CLI entry point; conversion is offline and has no third-party dependencies."""
import argparse
import json
from pathlib import Path
import sys

from . import __version__, poison, vital
from .convert import convert, lfo_free_rate_hz, lfo_pitch_semitones
from .profile import Profile


def json_bytes(data) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def parameter_group(tag: str) -> str:
    if tag.startswith('L1') or tag in ('TSL1', 'MLF1'):
        return 'LFO 1'
    if tag.startswith('L2') or tag in ('TSL2', 'MLF2'):
        return 'LFO 2'
    if tag in ('RETR', 'LXFM'):
        return 'LFO global'
    if tag.startswith(('O1', 'A1')):
        return 'Oscillator 1 / TVA 1'
    if tag.startswith(('O2', 'A2')):
        return 'Oscillator 2 / TVA 2'
    if tag.startswith('F1') and not tag.startswith(('F1P1', 'F1P2')):
        return 'Filter 1'
    if tag.startswith('F2') and not tag.startswith(('F2P1', 'F2P2')):
        return 'Filter 2'
    if tag.startswith(('FX', 'F1P', 'F2P', 'F3P', 'F4P')) or tag == 'TSDE':
        return 'Effects'
    if tag.startswith('EQ'):
        return 'EQ'
    if tag in ('SMIX', 'STYP', 'NMIX'):
        return 'Sub / noise'
    if tag in ('VELA', 'VELF', 'VELX'):
        return 'Velocity'
    if tag.startswith('M'):
        return 'Mod wheel'
    return 'Patch / routing'


def decoded_parameter(tag: str, value: float, profile: Profile) -> dict:
    """Add conservative UI/MIDI interpretations without replacing raw float32."""
    item = {'tag': tag, 'value': value, 'group': parameter_group(tag),
            'description': 'Tagged float32 parameter; interpretation is not verified'}
    if len(tag) == 4 and tag[0] == 'L' and tag[1] in '12':
        number = tag[1]
        suffix = tag[2:]
        descriptions = {
            'TY': 'waveform selector', 'FQ': 'rate', 'FD': 'fade',
            '>P': 'pitch depth', '>F': 'filter depth', '>A': 'amplitude depth',
        }
        if suffix in descriptions:
            item['description'] = f'LFO {number} {descriptions[suffix]}'
        if suffix == 'TY':
            index = round(value)
            if 0 <= index < len(profile.lfo_order):
                item['decoded'] = {'waveform': profile.lfo_order[index], 'enum_index': index}
        elif suffix == 'FQ' and 0 <= value <= 1:
            item['storage'] = 'normalized 0..1'
            item['midi_7bit_estimate'] = value * 127
            item['decoded'] = {'free_rate_hz': lfo_free_rate_hz(value, profile)}
        elif suffix in ('FD',) and 0 <= value <= 1:
            item['storage'] = 'normalized 0..1'
            item['midi_7bit_estimate'] = value * 127
        elif suffix in ('>P', '>F', '>A') and -1 <= value <= 1:
            item['storage'] = 'signed normalized -1..1'
            item['midi_7bit_estimate'] = (value + 1) * 63.5
            if suffix == '>P':
                item['decoded'] = {'pitch_semitones': lfo_pitch_semitones(value, profile)}
    elif tag in ('TSL1', 'TSL2', 'RETR', 'MLF1', 'MLF2', 'LXFM'):
        item['description'] = {
            'TSL1': 'LFO 1 tempo sync', 'TSL2': 'LFO 2 tempo sync',
            'RETR': 'LFO retrigger', 'MLF1': 'mod wheel to LFO 1',
            'MLF2': 'mod wheel to LFO 2', 'LXFM': 'LFO cross modulation depth',
        }[tag]
    return item


def preset_inspection(preset, profile: Profile) -> dict:
    return {
        'name': preset.name,
        'index': preset.index,
        'record_offset': preset.offset,
        'record_size': preset.record_size,
        'record_end_offset': preset.offset + preset.record_size,
        'raw_name_hex': preset.raw_name.hex(),
        'parameter_count': len(preset.parameters),
        'parameters': dict(preset.parameters),
        'decoded_parameters': [decoded_parameter(tag, value, profile)
                               for tag, value in preset.parameters.items()],
    }


def print_inspection(path: Path, bank, selected, profile: Profile, detailed: bool) -> None:
    reserved = bank.reserved.hex()
    print(f'P202 file: {path}')
    print(f'File size: {path.stat().st_size} bytes')
    print(f'Presets: {len(bank.presets)}; selected: {len(selected)}')
    print(f'Reserved header: {reserved} ({"zero" if not any(bank.reserved) else "nonzero, unknown"})')
    for preset in selected:
        print(f'\nPreset {preset.index}: {preset.name}')
        print(f'  Record: offset {preset.offset}, size {preset.record_size}, end {preset.offset + preset.record_size}')
        print(f'  Raw name: {preset.raw_name.hex()}')
        print(f'  Parameters: {len(preset.parameters)}')
        if not detailed:
            continue
        decoded = [decoded_parameter(tag, value, profile)
                   for tag, value in preset.parameters.items()]
        groups = []
        for item in decoded:
            if item['group'] not in groups:
                groups.append(item['group'])
        for group in groups:
            print(f'  [{group}]')
            for item in decoded:
                if item['group'] != group:
                    continue
                annotations = []
                if 'storage' in item:
                    annotations.append(item['storage'])
                if 'midi_7bit_estimate' in item:
                    midi = item['midi_7bit_estimate']
                    annotations.append(f'MIDI≈{midi:.3f} (~{round(midi)})')
                mapped = item.get('decoded', {})
                if 'waveform' in mapped:
                    annotations.append(f'waveform={mapped["waveform"]}')
                if 'free_rate_hz' in mapped:
                    annotations.append(f'free-rate≈{mapped["free_rate_hz"]:.6g} Hz')
                if 'pitch_semitones' in mapped:
                    annotations.append(f'pitch≈{mapped["pitch_semitones"]:+.6g} st')
                extra = f' | {"; ".join(annotations)}' if annotations else ''
                print(f'    {item["tag"]} = {item["value"]:.9g}{extra} | {item["description"]}')


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog='202tovital', description='Convert Poison-202 P202 presets to approximate Vital presets.')
    root.add_argument('--version', action='version', version=__version__)
    commands = root.add_subparsers(dest='command', required=True)
    inspect = commands.add_parser('inspect', help='List source presets or dump decoded parameters')
    inspect.add_argument('input', type=Path)
    inspect.add_argument('--preset', help='Inspect one preset by 1-based index or exact name')
    inspect.add_argument('--json', action='store_true', help='Print raw values plus conservative decoded interpretations as JSON')
    profile = commands.add_parser('profile', help='Print the editable, uncalibrated default profile')
    profile.add_argument('-o', '--output', type=Path)
    profile.add_argument('--force', action='store_true')
    cmd = commands.add_parser('convert', help='Convert a preset or bank; always produce a fidelity report')
    cmd.add_argument('input', type=Path)
    cmd.add_argument('-o', '--output', type=Path, help='Default: beside input, using .vital, .vitalbank, or the input stem for directory mode')
    cmd.add_argument('--format', choices=['vital', 'vitalbank', 'directory'], help='Default: infer from .vital or .vitalbank output suffix')
    cmd.add_argument('--preset', help='Select one source preset by 1-based index or exact name')
    cmd.add_argument('--bank-name', help='Bank folder name inside the Vital ZIP')
    cmd.add_argument('--bpm', type=float, default=120, help='Tempo for synchronized settings (default 120)')
    cmd.add_argument('--profile', type=Path, help='JSON overrides for unmeasured Poison scaling and enum order')
    cmd.add_argument('--report', type=Path, help='Report path (default OUTPUT.report.json or directory/conversion-report.json)')
    cmd.add_argument('--strict', action='store_true', help='Fail on unsupported/unknown/missing parameters or range clipping; estimates remain estimates')
    cmd.add_argument('--force', action='store_true', help='Replace existing output files')
    return root


def select(presets, selector):
    if selector is None:
        return list(presets)
    if selector.isdecimal():
        index = int(selector)
        if not 1 <= index <= len(presets):
            raise ValueError(f'Preset index must be between 1 and {len(presets)}')
        return [presets[index - 1]]
    matching = [p for p in presets if p.name == selector]
    if len(matching) != 1:
        raise ValueError(f'Preset name {selector!r} matched {len(matching)} entries; use a 1-based index')
    return matching


def default_output_path(input_path: Path, fmt: str) -> Path:
    """Place implicit output beside its input without guessing a CWD path."""
    if fmt == 'directory':
        return input_path.parent / input_path.stem
    return input_path.with_suffix('.' + fmt)


def run_conversion(args) -> int:
    bank = poison.load(args.input)
    selected = select(bank.presets, args.preset)
    if args.output:
        output = args.output
        fmt = args.format or {'.vital': 'vital', '.vitalbank': 'vitalbank'}.get(output.suffix.lower())
    else:
        # A selection is one preset; an unselected multi-preset P202 naturally
        # becomes a Vital bank. Directory mode is explicit because it creates a
        # new path rather than a single sibling file.
        fmt = args.format or ('vital' if len(selected) == 1 else 'vitalbank')
        output = default_output_path(args.input, fmt)
    if fmt is None:
        raise ValueError('Choose an output ending in .vital/.vitalbank, or supply --format')
    if fmt == 'vital' and len(selected) != 1:
        raise ValueError('Single .vital output requires --preset for a multi-preset bank')
    if fmt != 'directory' and output.suffix.lower() != '.' + fmt:
        raise ValueError(f'{fmt} output must end in .{fmt}')
    profile = Profile.load(args.profile) if args.profile else Profile()
    converted = [convert(preset, profile, args.bpm) for preset in selected]
    report = {'converter_version': __version__, 'input': str(args.input), 'format': fmt,
              'preset_count': len(converted), 'source_reserved_header_hex': bank.reserved.hex(),
              'conversions': [c.report for c in converted]}
    if any(bank.reserved):
        for result in converted:
            result.report['warnings'].append({'code': 'unknown_header', 'message': 'Nonzero reserved header bytes have unknown semantics.'})
    strict_codes = {'unsupported', 'unknown_parameter', 'missing_parameter', 'source_range', 'target_range', 'unknown_header'}
    issues = {warning['code'] for c in converted for warning in c.report['warnings']}
    if args.strict and issues & strict_codes:
        raise ValueError('Strict conversion refused: ' + ', '.join(sorted(issues & strict_codes)) + '. Run without --strict to generate the approximation and detailed report.')
    if fmt == 'directory':
        report_path = args.report or output / 'conversion-report.json'
        outputs = [(output / f'{i:03d} {vital.safe_name(c.preset["preset_name"])}.vital', vital.serialize(c.preset))
                   for i, c in enumerate(converted, 1)]
    else:
        report_path = args.report or Path(str(output) + '.report.json')
        content = vital.serialize(converted[0].preset) if fmt == 'vital' else vital.bundle([c.preset for c in converted], args.bank_name or output.stem)
        outputs = [(output, content)]
    outputs.append((report_path, json_bytes(report)))
    resolved = [path.resolve() for path, _ in outputs]
    if len(set(resolved)) != len(resolved):
        raise ValueError('Output and report paths must be distinct')
    protected = {args.input.resolve()}
    if args.profile:
        protected.add(args.profile.resolve())
    if set(resolved) & protected:
        raise ValueError('Refusing to overwrite the input or calibration profile')
    for path, _ in outputs:
        if path.is_symlink():
            raise ValueError(f'Refusing output symlink: {path}')
        if path.exists() and (not args.force or not path.is_file()):
            raise ValueError(f'Output exists: {path}; use --force to replace a regular file')
    for path, data in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        vital.atomic_write(path, data, args.force)
    print(f'Converted {len(converted)} preset(s) to {output}')
    print(f'Fidelity report: {report_path}')
    print('Approximate conversion: Poison DSP scaling is uncalibrated.', file=sys.stderr)
    return 0


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == 'inspect':
            bank = poison.load(args.input)
            selected = select(bank.presets, args.preset)
            profile = Profile()
            if args.json:
                data = {'format': 'P202', 'input': str(args.input),
                        'file_size': args.input.stat().st_size,
                        'count': len(bank.presets), 'selected_count': len(selected),
                        'reserved_header_hex': bank.reserved.hex(),
                        'presets': [preset_inspection(preset, profile) for preset in selected]}
                sys.stdout.write(json_bytes(data).decode('utf-8'))
            else:
                detailed = args.preset is not None or len(bank.presets) == 1
                print_inspection(args.input, bank, selected, profile, detailed)
                if not detailed:
                    print('\nUse --preset INDEX_OR_NAME for decoded parameter details, or --json for structured output.')
            return 0
        if args.command == 'profile':
            data = json_bytes(Profile().to_dict())
            if args.output:
                vital.atomic_write(args.output, data, args.force)
            else:
                sys.stdout.write(data.decode('utf-8'))
            return 0
        return run_conversion(args)
    except (OSError, ValueError, TypeError, OverflowError) as error:
        print(f'202tovital: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
