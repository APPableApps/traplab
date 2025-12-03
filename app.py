from flask import Flask, render_template, request, send_file, jsonify
import os
import uuid

from traplab_core.presets import get_presets, get_chain_by_name
from traplab_core.processing import process_audio_with_chain
from traplab_core.profiles import get_profiles, get_profile_by_name, save_profile
from traplab_core.ai_engine import analyze_track, suggest_chain

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


def save_upload(file_storage):
    uid = str(uuid.uuid4())
    path = os.path.join(UPLOAD_FOLDER, f"{uid}.wav")
    file_storage.save(path)
    return path


def output_path():
    uid = str(uuid.uuid4())
    return os.path.join(OUTPUT_FOLDER, f"{uid}.wav")


@app.route("/")
def index():
    return render_template(
        "index.html",
        presets=get_presets(),
        profiles=get_profiles(),
    )


# ---------------- STANDARD MIX ----------------
@app.route("/process", methods=["POST"])
def process_audio():
    if "audio_file" not in request.files:
        return "No file uploaded", 400

    file = request.files["audio_file"]
    if not file.filename:
        return "Invalid file", 400

    preset = request.form.get("preset_name")
    profile = request.form.get("profile_name")

    chain = None
    if profile:
        chain = get_profile_by_name(profile)
    if chain is None and preset:
        chain = get_chain_by_name(preset)
    if chain is None:
        return "Invalid preset/profile", 400

    in_path = save_upload(file)
    out_path = output_path()

    process_audio_with_chain(in_path, out_path, chain)

    return send_file(out_path, as_attachment=True, download_name="traplab_mix.wav")


# ---------------- PURE AI MIX ----------------
@app.route("/ai_mix", methods=["POST"])
def ai_mix():
    if "audio_file" not in request.files:
        return "No file uploaded", 400

    file = request.files["audio_file"]
    if not file.filename:
        return "Invalid file", 400

    mode = request.form.get("mode", "rap_vocal")
    cleanup_flag = request.form.get("cleanup") == "on"

    in_path = save_upload(file)

    # Analyze once
    stats = analyze_track(in_path)

    # Optional cleanup chain
    combined_chain = []
    if cleanup_flag:
        cleanup_chain = suggest_chain(stats, mode="vocal_clean")
        combined_chain.extend(cleanup_chain)

    # Main AI mix chain
    main_chain = suggest_chain(stats, mode=mode)
    combined_chain.extend(main_chain)

    out_path = output_path()
    process_audio_with_chain(in_path, out_path, combined_chain)

    return send_file(out_path, as_attachment=True, download_name="traplab_ai_mix.wav")


# ---------------- HYBRID / STACKED MIX ----------------
@app.route("/hybrid_mix", methods=["POST"])
def hybrid_mix():
    if "audio_file" not in request.files:
        return "No file uploaded", 400

    file = request.files["audio_file"]
    if not file.filename:
        return "Invalid file", 400

    mode = request.form.get("mode", "rap_vocal")
    preset = request.form.get("preset_name")
    cleanup_flag = request.form.get("cleanup") == "on"

    in_path = save_upload(file)

    # Base preset chain (color/character)
    preset_chain = get_chain_by_name(preset) if preset else None

    # Analyze once
    stats = analyze_track(in_path)

    combined_chain = []

    # 1) Preset chain first
    if preset_chain:
        combined_chain.extend(preset_chain)

    # 2) Optional cleanup chain (noise + de-ess + leveling)
    if cleanup_flag:
        cleanup_chain = suggest_chain(stats, mode="vocal_clean")
        combined_chain.extend(cleanup_chain)

    # 3) Main AI chain to polish/optimize
    ai_chain = suggest_chain(stats, mode=mode)
    combined_chain.extend(ai_chain)

    out_path = output_path()
    process_audio_with_chain(in_path, out_path, combined_chain)

    return send_file(out_path, as_attachment=True, download_name="traplab_hybrid_mix.wav")


# ---------------- PROFILES API ----------------
@app.route("/profiles/save", methods=["POST"])
def profile_save():
    data = request.json
    name = data.get("profile_name")
    preset = data.get("source_preset")

    if not name or not preset:
        return jsonify({"error": "Missing name/preset"}), 400

    chain = get_chain_by_name(preset)
    if not chain:
        return jsonify({"error": "Unknown preset"}), 400

    save_profile(name, chain)
    return jsonify({"status": "ok"})


@app.route("/profiles")
def list_profiles():
    return jsonify(get_profiles())


if __name__ == "__main__":
    import threading
    import webbrowser

    def open_browser():
        webbrowser.open("http://127.0.0.1:5000")

    threading.Timer(1.0, open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
