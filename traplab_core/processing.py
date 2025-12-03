import numpy as np
import soundfile as sf


def db_to_linear(db):
    return 10.0 ** (db / 20.0)


def one_pole_lowpass(x, sr, cutoff_hz=8000.0):
    """
    Simple 1st-order lowpass filter (no SciPy).
    """
    if cutoff_hz <= 0:
        return x

    dt = 1.0 / float(sr)
    rc = 1.0 / (2.0 * np.pi * cutoff_hz)
    alpha = dt / (rc + dt)

    y = np.zeros_like(x)
    y[0] = x[0]
    for n in range(1, len(x)):
        y[n] = y[n - 1] + alpha * (x[n] - y[n - 1])
    return y


def one_pole_highpass(x, sr, cutoff_hz=100.0):
    """
    Highpass built from lowpass: HP = x - LP(x).
    """
    lp = one_pole_lowpass(x, sr, cutoff_hz)
    return x - lp


def apply_highpass(y, sr, cutoff_hz=100.0, order=1):
    # We ignore "order" here and just apply our 1st-order filter multiple times
    out = y.copy()
    for _ in range(max(1, int(order))):
        out = one_pole_highpass(out, sr, cutoff_hz)
    return out


def apply_lowpass(y, sr, cutoff_hz=8000.0, order=1):
    out = y.copy()
    for _ in range(max(1, int(order))):
        out = one_pole_lowpass(out, sr, cutoff_hz)
    return out


def apply_tilt(y, sr, tilt_db=4.0, cutoff_hz=1500.0):
    """
    Very simple 'tilt' EQ:
    - Boost or cut the high frequencies relative to lows using a highpass component.
    """
    if tilt_db == 0.0:
        return y

    # Get a rough "high frequency" component
    highs = one_pole_highpass(y, sr, cutoff_hz)
    tilt_gain = db_to_linear(tilt_db)

    # Blend high content back in
    y_out = y + (tilt_gain - 1.0) * highs

    # Prevent runaway gain
    max_val = np.max(np.abs(y_out)) + 1e-9
    if max_val > 1.0:
        y_out = y_out / max_val
    return y_out


def apply_saturation(y, drive=1.5):
    """
    Soft clipping saturation using tanh.
    """
    x = y * drive
    y_sat = np.tanh(x)
    max_val = np.max(np.abs(y_sat)) + 1e-9
    y_sat = y_sat / max_val
    return y_sat


def apply_compressor(y, threshold_db=-18.0, ratio=3.0):
    """
    Super simple static compressor curve.
    """
    threshold_lin = db_to_linear(threshold_db)
    x = y.copy()
    mag = np.abs(x)
    over = mag > threshold_lin

    compressed = threshold_lin + (mag[over] - threshold_lin) / ratio
    x[over] = np.sign(x[over]) * compressed
    return x


def apply_normalize(y, target_dbfs=-1.0):
    peak = np.max(np.abs(y)) + 1e-9
    target_lin = db_to_linear(target_dbfs)
    return y * (target_lin / peak)


def apply_limiter(y, threshold_db=-1.0):
    threshold_lin = db_to_linear(threshold_db)
    x = y.copy()
    mag = np.abs(x)
    over = mag > threshold_lin
    x[over] = np.sign(x[over]) * threshold_lin
    return x


def process_audio_with_chain(input_path, output_path, chain_config):
    """
    Load audio, run it through the provided chain, and write to disk.
    chain_config is a list of modules (dicts).
    """
    # Read audio (mono mixdown if needed)
    y, sr = sf.read(input_path, always_2d=False)

    if y.ndim > 1:
        y = y.mean(axis=1)

    # Convert to float32 in -1..1 if it's integer
    if np.issubdtype(y.dtype, np.integer):
        max_int = np.iinfo(y.dtype).max
        y = y.astype(np.float32) / max_int
    else:
        y = y.astype(np.float32)

    for module in chain_config:
        mtype = module.get("type")
        if mtype == "highpass":
            y = apply_highpass(
                y,
                sr,
                cutoff_hz=module.get("cutoff_hz", 100.0),
                order=module.get("order", 1),
            )
        elif mtype == "lowpass":
            y = apply_lowpass(
                y,
                sr,
                cutoff_hz=module.get("cutoff_hz", 8000.0),
                order=module.get("order", 1),
            )
        elif mtype == "tilt":
            y = apply_tilt(
                y,
                sr,
                tilt_db=module.get("tilt_db", 4.0),
                cutoff_hz=module.get("cutoff_cutoff_hz", 1500.0),
            )
        elif mtype == "saturation":
            y = apply_saturation(y, drive=module.get("drive", 1.5))
        elif mtype == "compressor":
            y = apply_compressor(
                y,
                threshold_db=module.get("threshold_db", -18.0),
                ratio=module.get("ratio", 3.0),
            )
        elif mtype == "normalize":
            y = apply_normalize(y, target_dbfs=module.get("target_dbfs", -1.0))
        elif mtype == "limiter":
            y = apply_limiter(y, threshold_db=module.get("threshold_db", -1.0))
        else:
            # Unknown module, ignore
            pass

    # Clip to be safe and write
    y = np.clip(y, -1.0, 1.0)
    sf.write(output_path, y, sr)
