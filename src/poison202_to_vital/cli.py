"""CLI entry point; conversion is offline and has no third-party dependencies."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from . import __version__, poison, vital
from .convert import convert
from .profile import Profile


def json_bytes(data) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog='202tovital', description='Convert Poison-202 P202 presets to approximate Vital presets.')
    root.add_argument('--version', action='version', version=__version__)
    commands = root.add_subparsers(dest='command', required=True)
    inspect = commands.add_parser('inspect', help='List source presets or dump decoded parameters')
    inspect.add_argument('input', type=Path)
    inspect.add_argument('--json', action='store_true', help='Print all decoded values as JSON')
    profile = commands.add_parser('profile', help='Print the editable, uncalibrated default profile')
    profile.add_argument('-o', '--output', type=Path)
    profile.add_argument('--force', action='store_true')
    cmd = commands.add_parser('convert', help='Convert a preset or bank; always produce a fidelity report')
    cmd.add_argument('input', type=Path)
    cmd.add_argument('-o', '--output', type=Path, required=True)
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


def run_conversion(args) -> int:
    bank = poison.load(args.input)
    selected = select(bank.presets, args.preset)
    fmt = args.format or {'.vital': 'vital', '.vitalbank': 'vitalbank'}.get(args.output.suffix.lower())
    if fmt is None:
        raise ValueError('Choose an output ending in .vital/.vitalbank, or supply --format')
    if fmt == 'vital' and len(selected) != 1:
        raise ValueError('Single .vital output requires --preset for a multi-preset bank')
    if fmt != 'directory' and args.output.suffix.lower() != '.' + fmt:
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
        report_path = args.report or args.output / 'conversion-report.json'
        outputs = [(args.output / f'{i:03d} {vital.safe_name(c.preset["preset_name"])}.vital', vital.serialize(c.preset))
                   for i, c in enumerate(converted, 1)]
    else:
        report_path = args.report or Path(str(args.output) + '.report.json')
        content = vital.serialize(converted[0].preset) if fmt == 'vital' else vital.bundle([c.preset for c in converted], args.bank_name or args.output.stem)
        outputs = [(args.output, content)]
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
    print(f'Converted {len(converted)} preset(s) to {args.output}')
    print(f'Fidelity report: {report_path}')
    print('Approximate conversion: Poison DSP scaling is uncalibrated.', file=sys.stderr)
    return 0


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == 'inspect':
            bank = poison.load(args.input)
            if args.json:
                data = {'count': len(bank.presets), 'reserved_header_hex': bank.reserved.hex(),
                        'presets': [{**asdict(p), 'raw_name': p.raw_name.hex()} for p in bank.presets]}
                sys.stdout.write(json_bytes(data).decode('utf-8'))
            else:
                for preset in bank.presets:
                    print(f'{preset.index:3d}  {preset.name}  ({len(preset.parameters)} parameters)')
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
