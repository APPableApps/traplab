import json
import os

PROFILE_FILE = "profiles.json"


def _ensure_file():
    if not os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "w") as f:
            json.dump({}, f)


def load_profiles_dict():
    _ensure_file()
    with open(PROFILE_FILE, "r") as f:
        return json.load(f)


def save_profiles_dict(data):
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_profiles():
    data = load_profiles_dict()
    return sorted(list(data.keys()))


def get_profile_by_name(name: str):
    if not name:
        return None
    data = load_profiles_dict()
    return data.get(name)


def save_profile(name: str, chain_config):
    data = load_profiles_dict()
    data[name] = chain_config
    save_profiles_dict(data)
