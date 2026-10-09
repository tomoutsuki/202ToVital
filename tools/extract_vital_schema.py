"""Regenerate numeric Vital control metadata from the supplied 1.0.6 source.

Run: python tools/extract_vital_schema.py ../.materials/vital/vital
No C++ executes. Only whitelisted numeric constants and arithmetic are accepted.
"""
import ast
import json
import operator
from pathlib import Path
import re
import sys

CONSTANTS = {
    'Distortion::kMinDrive': -30, 'Distortion::kMaxDrive': 30,
    'kMaxPolyphony': 33, 'PredefinedWaveFrames::kNumShapes': 6,
    'constants::kNumSourceDestinations': 5, 'constants::kNumEffects': 9,
    'vital::MultibandCompressor::kNumBandOptions': 4,
    'DigitalSvf::kMinGain': -15, 'DigitalSvf::kMaxGain': 15,
    'vital::utils::factorial(vital::kNumEffects)': 362880,
    'VoiceHandler::kNumVoicePriorities': 5, 'VoiceHandler::kRoundRobin': 4,
    'VoiceHandler::kNumVoiceOverrides': 2, 'VoiceHandler::kKill': 0,
    'SynthLfo::kNumSyncTypes': 6, 'SynthLfo::kNumSyncOptions': 5,
    'RandomLfo::kNumStyles': 4, 'kNumFilterModels': 8,
    'SynthOscillator::kNumUnisonStackTypes': 11,
    'kNumOscillatorWaveFrames': 256,
    'SynthOscillator::kNumDistortionTypes': 13,
    'SynthOscillator::kNumSpectralMorphTypes': 12,
}


def number(expression):
    for key in sorted(CONSTANTS, key=len, reverse=True):
        expression = expression.replace(key, str(CONSTANTS[key]))
    expression = re.sub(r'(?<=\d)f\b', '', expression.strip())
    def calc(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -calc(node.operand)
        if isinstance(node, ast.BinOp):
            op = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Div: operator.truediv}[type(node.op)]
            return op(calc(node.left), calc(node.right))
        raise ValueError(expression)
    return calc(ast.parse(expression, mode='eval').body)


def main():
    source = Path(sys.argv[1]) / 'src/common/synth_parameters.cpp'
    text = source.read_text()
    groups = {'parameter_list': [''], 'env_parameter_list': [f'env_{i}_' for i in range(1, 7)],
              'lfo_parameter_list': [f'lfo_{i}_' for i in range(1, 9)],
              'random_lfo_parameter_list': [f'random_{i}_' for i in range(1, 5)],
              'osc_parameter_list': [f'osc_{i}_' for i in range(1, 4)],
              'filter_parameter_list': ['filter_1_', 'filter_2_', 'filter_fx_'],
              'mod_parameter_list': [f'modulation_{i}_' for i in range(1, 65)]}
    schema = {}
    for group, prefixes in groups.items():
        section = text.split(f'{group}[] = {{', 1)[1].split('\n  };', 1)[0]
        for match in re.finditer(r'\{ "(\w+)", 0x[\da-f]+, (.*?),\s*ValueDetails::(\w+)', section):
            lo, hi, default = [number(x) for x in match[2].split(',')[:3]]
            for prefix in prefixes:
                schema[prefix + match[1]] = {'min': lo, 'max': hi, 'default': default, 'scale': match[3]}
    for key, value in {'osc_1_on': 1, 'osc_2_destination': 1, 'osc_3_destination': 3,
                       'filter_1_osc1_input': 1, 'filter_2_osc2_input': 1}.items():
        schema[key]['default'] = value
    out = Path('src/poison202_to_vital/data/vital_schema.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2, sort_keys=True) + '\n')
    print(f'Wrote {len(schema)} control definitions')


if __name__ == '__main__':
    main()
