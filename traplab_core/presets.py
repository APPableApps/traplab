_PRESETS = {
    "Trap Vocal Sauce": [
        {"type": "highpass", "cutoff_hz": 100.0, "order": 2},
        {"type": "saturation", "drive": 1.8},
        {"type": "compressor", "threshold_db": -18.0, "ratio": 3.0},
        {"type": "normalize", "target_dbfs": -1.0},
    ],

    "808 Punch": [
        {"type": "lowpass", "cutoff_hz": 8000.0, "order": 2},
        {"type": "saturation", "drive": 2.2},
        {"type": "limiter", "threshold_db": -3.0},
    ],

    "2-Track Glue": [
        {"type": "highpass", "cutoff_hz": 30.0, "order": 2},
        {"type": "compressor", "threshold_db": -14.0, "ratio": 2.0},
        {"type": "normalize", "target_dbfs": -1.0},
    ],

    "Bright Air": [
        {"type": "highpass", "cutoff_hz": 80.0, "order": 2},
        {"type": "tilt", "tilt_db": 4.0},
        {"type": "normalize", "target_dbfs": -1.0},
    ],
}


def get_presets():
    return sorted(_PRESETS.keys())


def get_chain_by_name(name: str):
    return _PRESETS.get(name)
