import numpy as np
import soundfile as sf


def rms(x):
    return float(np.sqrt(np.mean(x ** 2)))


def peak(x):
    return float(np.max(np.abs(x)))


def band_energy(x, sr, low_hz, high_hz):
    fft = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1.0 / sr)

    mask = (freqs >= low_hz) & (freqs <= high_hz)
    return float(np.sum(np.abs(fft[mask])))


def analyze_track(path):
    x, sr = sf.read(path, always_2d=False)

    if x.ndim > 1:
        x = x.mean(axis=1)

    if np.issubdtype(x.dtype, np.integer):
        x = x.astype(np.float32) / np.iinfo(x.dtype).max

    stats = {
        "rms": rms(x),
        "peak": peak(x),
        "low": band_energy(x, sr, 20, 150),
        "mid": band_energy(x, sr, 150, 5000),
        "high": band_energy(x, sr, 5000, 15000),
        "sr": sr,
    }

    return stats


def suggest_chain(stats, mode="rap_vocal"):
    low = stats["low"]
    mid = stats["mid"]
    high = stats["high"]
    loud = stats["rms"]

    chain = []

    if mode == "rap_vocal":
        hp_freq = 80 if low < mid * 0.10 else 120
        chain.append({"type": "highpass", "cutoff_hz": hp_freq, "order": 1})

        tilt = 3.0 if high < mid * 0.20 else 1.0
        chain.append({"type": "tilt", "tilt_db": tilt})

        ratio = 2.5 if loud > 0.1 else 4.0
        chain.append({"type": "compressor", "threshold_db": -18, "ratio": ratio})

        chain.append({"type": "saturation", "drive": 1.6})
        chain.append({"type": "normalize", "target_dbfs": -1.0})

    elif mode == "rap_mix":
        hp_freq = 25 if low > (mid + high) * 0.5 else 35
        chain.append({"type": "highpass", "cutoff_hz": hp_freq, "order": 1})

        tilt = -2.0 if high > mid * 0.45 else 0.0
        if tilt != 0.0:
            chain.append({"type": "tilt", "tilt_db": tilt})

        chain.append({"type": "compressor", "threshold_db": -12, "ratio": 2.0})
        chain.append({"type": "saturation", "drive": 1.3})
        chain.append({"type": "normalize", "target_dbfs": -1.0})

    else:
        chain.append({"type": "normalize", "target_dbfs": -1.0})

    return chain
