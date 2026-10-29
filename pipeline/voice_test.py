"""Voice tryouts: the same lines read by our current Kokoro voice and by Chatterbox at a few emotion settings.

python voice_test.py kokoro      Kokoro baseline plus the male and female reference clips (main Python, onnx)
python voice_test.py chatterbox  Chatterbox reads (run with vendor/venv_chatterbox/Scripts/python, CUDA)
Writes MP3s into out/voice_tests/. The references are Kokoro's own synthetic voices (am_michael, af_heart), so no real person's voice is cloned.
"""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out", "voice_tests")
os.makedirs(OUT, exist_ok=True)

EXPLAINER = ("Your fridge doesn't make anything cold. It steals the heat out of your leftovers and dumps it out the back. "
             "Put your hand behind it tonight. That warm air? That's yesterday's lasagna.")
STORY = ("Bro. It says zero point one grams of sugar. Raw liver, fine. Mystery powder from a guy named Vlad, fine. "
         "But I am not putting that in my body.")
REF = os.path.join(OUT, "ref_am_michael.wav")
REF_F = os.path.join(OUT, "ref_af_heart.wav")

def to_mp3(wav, name):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-b:a", "160k", os.path.join(OUT, name + ".mp3")], check=True)

def kokoro():
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(ROOT, "vendor", "tts", "kokoro-v1.0.onnx"), os.path.join(ROOT, "vendor", "tts", "voices-v1.0.bin"))
    for label, text in (("explainer", EXPLAINER), ("story", STORY)):
        audio, sr = k.create(text, voice="am_adam", speed=1.05, lang="en-us")
        p = os.path.join(OUT, f"0_kokoro_now_{label}.wav"); sf.write(p, audio, sr); to_mp3(p, f"0_kokoro_now_{label}")
    ref_text = ("Okay, so here's the thing nobody tells you about the stuff in your kitchen. "
                "Every single appliance is quietly doing something wild, and I'm going to show you exactly what.")
    for voice, path in (("am_michael", REF), ("af_heart", REF_F)):
        audio, sr = k.create(ref_text, voice=voice, speed=1.0, lang="en-us")
        sf.write(path, audio, sr)

def chatterbox():
    import torch, torchaudio
    import chatterbox.tts as ct
    import json, struct
    from pathlib import Path
    from huggingface_hub import hf_hub_download
    # Windows has a small page file here: the stock loader holds a CPU copy of the model, a CPU state dict and a GPU
    # copy at once and runs out of commit memory. Build each part in place and copy the checkpoint into it
    # one tensor at a time.
    DT = {"F32": torch.float32, "F16": torch.float16, "BF16": torch.bfloat16, "I64": torch.int64, "I32": torch.int32,
          "BOOL": torch.bool, "U8": torch.uint8, "I8": torch.int8}
    def fill(model, path):
        target = model.state_dict()
        with open(path, "rb") as f, torch.no_grad():
            n = struct.unpack("<Q", f.read(8))[0]
            head = json.loads(f.read(n))
            for name, info in head.items():
                if name == "__metadata__" or name not in target:
                    continue
                a, b = info["data_offsets"]
                f.seek(8 + n + a)
                t = torch.frombuffer(bytearray(f.read(b - a)), dtype=DT[info["dtype"]]).reshape(info["shape"])
                target[name].copy_(t)
        return model.eval()
    for fname in ("ve.safetensors", "t3_cfg.safetensors", "s3gen.safetensors", "tokenizer.json", "conds.pt"):
        d = Path(hf_hub_download("ResembleAI/chatterbox", fname)).parent
    dev = os.environ.get("CHATTERBOX_DEVICE", "cpu")     # the 6 GB laptop GPU runs out during generation
    with torch.device(dev):
        ve = fill(ct.VoiceEncoder(), d / "ve.safetensors")
        t3 = fill(ct.T3(), d / "t3_cfg.safetensors")
        s3gen = fill(ct.S3Gen(), d / "s3gen.safetensors")
    conds = ct.Conditionals.load(d / "conds.pt", map_location=torch.device("cpu")).to(dev)
    if dev == "cuda":                                    # halve the 2 GB text-to-token model so generation fits in 6 GB
        t3.to(torch.bfloat16)
        run = t3.inference
        t3.inference = lambda *a, t3_cond, **k: run(*a, t3_cond=t3_cond.to(device="cuda", dtype=torch.bfloat16), **k)
    m = ct.ChatterboxTTS(t3, s3gen, ve, ct.EnTokenizer(str(d / "tokenizer.json")), dev, conds=conds)
    for name, ref, exag, cfg in TAKES:
        for label, text in (("explainer", EXPLAINER), ("story", STORY)):
            if os.path.exists(os.path.join(OUT, f"{name}_{label}.mp3")):
                continue
            torch.manual_seed(7)
            kw = {"exaggeration": exag, "cfg_weight": cfg}
            if ref:
                kw["audio_prompt_path"] = ref
            wav = m.generate(text, **kw)
            p = os.path.join(OUT, f"{name}_{label}.wav")
            torchaudio.save(p, wav.cpu(), m.sr)
            to_mp3(p, f"{name}_{label}")
            print(name, label, round(wav.shape[-1] / m.sr, 1), "s", flush=True)

TAKES = [("1_chatterbox_female_calm", REF_F, 0.5, 0.5),
         ("2_chatterbox_female_hyped", REF_F, 0.9, 0.3),
         ("3_chatterbox_male_calm", REF, 0.5, 0.5),
         ("4_chatterbox_male_screaming", REF, 1.4, 0.25)]

def hosted():
    """Same takes on Resemble's free Hugging Face demo, for when this laptop has no memory to spare."""
    import shutil
    from gradio_client import Client, handle_file
    c = Client("ResembleAI/Chatterbox", verbose=False)
    for name, ref, exag, cfg in TAKES:
        for label, text in (("explainer", EXPLAINER), ("story", STORY)):
            path = c.predict(text_input=text, audio_prompt_path_input=handle_file(ref), exaggeration_input=exag,
                             temperature_input=0.8, seed_num_input=7, cfgw_input=cfg, vad_trim_input=False,
                             api_name="/generate_tts_audio")
            wav = os.path.join(OUT, f"{name}_{label}.wav")
            shutil.copy(path, wav)
            to_mp3(wav, f"{name}_{label}")
            print(name, label, flush=True)

if __name__ == "__main__":
    {"kokoro": kokoro, "chatterbox": chatterbox, "hosted": hosted}[sys.argv[1]]()
