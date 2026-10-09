"""Compare the user's controlled Poison recordings to Vital WAV renders.

Optional deps: numpy, av. Decode by container magic, not file suffix: the
"original_wav/*.wav" files are AAC in QuickTime MOV containers.
"""
import argparse
import json
from pathlib import Path
import wave

import av
import numpy as np

SHAPES = ('saw', 'sine', 'square', 'supersaw', 'triangle')


def read_audio(path):
    with av.open(str(path)) as container:
        stream = container.streams.audio[0]
        rate = int(stream.rate)
        arrays = []
        for frame in container.decode(stream):
            data = frame.to_ndarray()
            if frame.format.is_planar:
                data = data.reshape(stream.channels, -1)
            else:
                data = data.reshape(-1, stream.channels).T
            if np.issubdtype(data.dtype, np.integer):
                data = data.astype(np.float64) / (2 ** (data.dtype.itemsize * 8 - 1))
            arrays.append(data.astype(np.float64))
    return np.concatenate(arrays, axis=1), rate


def envelope(audio, rate, hop=.01):
    mono = np.mean(audio, axis=0)
    size = max(1, round(rate * hop))
    pad = len(mono) % size
    if pad:
        mono = mono[:-pad]
    chunks = mono.reshape(-1, size)
    return np.sqrt(np.mean(chunks * chunks, axis=1)), size / rate


def activity(audio, rate):
    rms, dt = envelope(audio, rate)
    maximum = max(rms.max(), 1e-12)
    threshold = max(maximum * .08, .0003)
    active = np.flatnonzero(rms > threshold)
    if len(active) == 0:
        return 0, 0, float(maximum)
    return round(active[0] * dt, 4), round((active[-1] + 1) * dt, 4), float(maximum)


def major_frequency(audio, rate, start, seconds=.15):
    mono = audio.mean(axis=0)
    segment = mono[int(start*rate):int((start+seconds)*rate)]
    segment = segment - segment.mean()
    if len(segment) < 10:
        return 0
    spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment))))
    hz = np.fft.rfftfreq(len(segment), 1/rate)
    mask = (hz > 80) & (hz < 2000)
    return float(hz[mask][np.argmax(spectrum[mask])])


def precise_fundamental(audio, rate, start, seconds=.3):
    mono = audio.mean(axis=0)
    segment = mono[int(start * rate):int((start + seconds) * rate)]
    nfft = 2 ** 19
    spectrum = np.abs(np.fft.rfft((segment - segment.mean()) * np.hanning(len(segment)), n=nfft))
    frequencies = np.fft.rfftfreq(nfft, 1 / rate)
    mask = (frequencies > 150) & (frequencies < 800)
    return float(frequencies[mask][np.argmax(spectrum[mask])])


def harmonic_spectrum(audio, rate, start, seconds, fundamental):
    mono = audio.mean(axis=0)
    segment = mono[int(start * rate):int((start + seconds) * rate)]
    segment = segment - segment.mean()
    if len(segment) < round(rate * .08):
        raise ValueError('Steady-state window too short')
    nfft = 2 ** (int(np.ceil(np.log2(len(segment)))) + 2)
    spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment)), n=nfft))
    freq = np.fft.rfftfreq(nfft, 1/rate)
    values = []
    for n in range(1, 25):
        target = n * fundamental
        if target >= min(rate/2 - 30, 10000):
            break
        mask = np.abs(freq - target) <= max(7, 1.5 / seconds)
        values.append(float(np.max(spectrum[mask])) if mask.any() else 0.)
    return np.asarray(values)


def cosine_similarity(x, y):
    size = min(len(x), len(y))
    x, y = x[:size], y[:size]
    return float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-20))


def write_pcm16(path, audio, rate):
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(audio.T, -1, 1) * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(audio.shape[0])
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(pcm.tobytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('-o', '--output', type=Path)
    parser.add_argument('--matched-midi', type=int, default=72,
                        help='MIDI note for the native Vital comparison (default 72)')
    parser.add_argument('--write-matched-dir', type=Path,
                        help='Write pitch-matched Vital WAV previews here')
    args = parser.parse_args()
    import vita
    sine_poison, sine_poison_rate = read_audio(args.root / 'original_wav/single_note_waveshape_sine.wav')
    sine_vital, sine_vital_rate = read_audio(args.root / 'converted_wav/C_sine.wav')
    poison_fundamental = precise_fundamental(sine_poison, sine_poison_rate, 2.23)
    vital_fundamental = precise_fundamental(sine_vital, sine_vital_rate, 2.23)
    results = []
    for shape in SHAPES:
        a_path = args.root / 'original_wav' / f'single_note_waveshape_{shape}.wav'
        b_path = args.root / 'converted_wav' / f'C_{shape}.wav'
        original, original_rate = read_audio(a_path)
        vital, vital_rate = read_audio(b_path)
        a_on, a_off, a_max = activity(original, original_rate)
        b_on, b_off, b_max = activity(vital, vital_rate)
        synth = vita.Synth()
        synth.set_sample_rate(vital_rate)
        if not synth.load_preset(str(args.root / 'converted_preset' / f'C_{shape}.vital')):
            raise ValueError(f'Vita rejected C_{shape}.vital')
        # The DAW recordings have a 2.18 s lead-in. Prime Vital's control
        # smoothing for the same interval before asking Vita to render a note.
        synth.render(args.matched_midi, 0.0, .01, a_on)
        matched_vital = synth.render(args.matched_midi, .7, .55, .8).astype(np.float64)
        if args.write_matched_dir:
            aligned = np.zeros((matched_vital.shape[0],
                                round(original.shape[1] / original_rate * vital_rate)))
            offset = round(a_on * vital_rate)
            count = min(matched_vital.shape[1], aligned.shape[1] - offset)
            aligned[:, offset:offset + count] = matched_vital[:, :count]
            write_pcm16(args.write_matched_dir / f'C_{shape}_MIDI{args.matched_midi}.wav',
                        aligned, vital_rate)
        a_start = a_on + .06
        b_start = b_on + .06
        a_f0 = major_frequency(original, original_rate, a_start)
        b_f0 = major_frequency(vital, vital_rate, b_start)
        # The sine reference gives the fundamental when another waveform's
        # strongest harmonic is not its first (notably Poison Super Saw).
        duration = min(.30, max(.09, a_off - a_start - .03), max(.09, b_off - b_start - .03))
        a_harm = harmonic_spectrum(original, original_rate, a_start, duration, poison_fundamental)
        b_harm = harmonic_spectrum(vital, vital_rate, b_start, duration, vital_fundamental)
        matched_harm = harmonic_spectrum(matched_vital, vital_rate, .06, duration, poison_fundamental)
        a_segment = original[:, int(a_start*original_rate):int((a_start+duration)*original_rate)]
        b_segment = vital[:, int(b_start*vital_rate):int((b_start+duration)*vital_rate)]
        a_rms = float(np.sqrt(np.mean(a_segment*a_segment)))
        b_rms = float(np.sqrt(np.mean(b_segment*b_segment)))
        level_difference_db = float(20*np.log10((a_rms+1e-20)/(b_rms+1e-20)))
        matched_segment = matched_vital[:, int(.06*vital_rate):int((.06+duration)*vital_rate)]
        matched_rms = float(np.sqrt(np.mean(matched_segment*matched_segment)))
        result = {
            'shape': shape,
            'original_codec': 'QuickTime/AAC (despite .wav suffix)',
            'original_rate': original_rate, 'vital_rate': vital_rate,
            'original_channels': original.shape[0], 'vital_channels': vital.shape[0],
            'original_duration_s': round(original.shape[1]/original_rate, 4),
            'vital_duration_s': round(vital.shape[1]/vital_rate, 4),
            'original_active_s': [a_on, a_off], 'vital_active_s': [b_on, b_off],
            'original_max_frame_rms': round(a_max, 6), 'vital_max_frame_rms': round(b_max, 6),
            'original_steady_rms': round(a_rms, 6), 'vital_steady_rms': round(b_rms, 6),
            'original_louder_by_db': round(level_difference_db, 2),
            'matched_vital_midi': args.matched_midi,
            'matched_vital_steady_rms': round(matched_rms, 6),
            'original_louder_than_matched_vital_db': round(float(20*np.log10((a_rms+1e-20)/(matched_rms+1e-20))), 2),
            'original_dominant_hz': round(a_f0, 3), 'vital_dominant_hz': round(b_f0, 3),
            'spectral_cosine_24_harmonics': round(cosine_similarity(a_harm, b_harm), 4),
            'matched_spectral_cosine_24_harmonics': round(cosine_similarity(a_harm, matched_harm), 4),
            'original_odd_even_ratio': round(float(np.sum(a_harm[0::2])/(np.sum(a_harm[1::2])+1e-20)), 3),
            'vital_odd_even_ratio': round(float(np.sum(b_harm[0::2])/(np.sum(b_harm[1::2])+1e-20)), 3),
            'original_relative_harmonics': (a_harm/(a_harm[0]+1e-20)).round(4).tolist(),
            'vital_relative_harmonics': (b_harm/(b_harm[0]+1e-20)).round(4).tolist(),
            'matched_vital_relative_harmonics': (matched_harm/(matched_harm[0]+1e-20)).round(4).tolist(),
        }
        results.append(result)
        print(shape, 'dominant',a_f0,b_f0,'active',a_on,a_off,b_on,b_off,
              'louder dB',result['original_louder_by_db'], 'matched cosine',result['matched_spectral_cosine_24_harmonics'],
              'odd/even',result['original_odd_even_ratio'],result['vital_odd_even_ratio'])
    output = args.output or Path('waveform-comparison.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'method': 'AAC MOV and PCM WAV decoded by PyAV; steady windows start 60 ms after detected onset; the supplied Vital WAV is MIDI 60 while Poison is MIDI 72; Vita renders the exact converted presets at MIDI 72 for matched-pitch spectra; cosine similarity ignores phase and global level, and is not a perceptual similarity score',
                                  'poison_sine_fundamental_hz': poison_fundamental,
                                  'vital_sine_fundamental_hz': vital_fundamental,
                                  'results': results}, indent=2) + '\n')
    print('Wrote',output)


if __name__ == '__main__':
    main()
