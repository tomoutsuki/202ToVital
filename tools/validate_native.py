"""Optional native compatibility check using Vita; never implies Poison fidelity.

PYTHONPATH=src .venv/bin/python tools/validate_native.py bank.vitalbank [-o report.json]
"""
import argparse
from importlib.metadata import version
import json
from pathlib import Path
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('-o', '--output', type=Path)
    args = parser.parse_args()
    try:
        import numpy as np
        import vita
    except ImportError:
        parser.error('Install the optional vita and numpy packages into your virtual environment')
    if args.input.suffix == '.vitalbank':
        with zipfile.ZipFile(args.input) as archive:
            presets = [(name, json.loads(archive.read(name))) for name in archive.namelist() if name.endswith('.vital')]
    else:
        presets = [(args.input.name, json.loads(args.input.read_text()))]
    results = []
    for name, data in presets:
        synth = vita.Synth()
        synth.set_sample_rate(22050)
        loaded = synth.load_json(json.dumps(data))
        if not loaded:
            raise RuntimeError(f'Vita rejected {name}')
        samples = synth.render(60, .7, .35, .75)
        finite = bool(np.isfinite(samples).all())
        if not finite:
            raise RuntimeError(f'Non-finite render in {name}')
        result = {'name': name, 'loaded': bool(loaded), 'finite': finite,
                  'peak': float(np.max(np.abs(samples))),
                  'rms': float(np.sqrt(np.mean(samples ** 2))), 'above_unity': bool(np.max(np.abs(samples)) > 1),
                  'non_silent': bool(np.max(np.abs(samples)) > 1e-8), 'samples': samples.shape[1]}
        results.append(result)
        print(f'{len(results)}/{len(presets)} {name}: peak={result["peak"]:.5f}, rms={result["rms"]:.5f}', flush=True)
    report = {'vita_version': version('vita'), 'sample_rate': 22050,
              'midi_note': 60, 'velocity': .7, 'note_seconds': .35, 'render_seconds': .75,
              'reference_poison_audio': False, 'results': results}
    output = args.output or args.input.with_suffix('.native-validation.json')
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'All {len(results)} presets loaded and rendered finite samples. Results: {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
