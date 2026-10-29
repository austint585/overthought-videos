"""Chatterbox narration worker. Runs inside vendor/venv_chatterbox_cpu (CPU-only torch), never in the main Python.

vendor/venv_chatterbox_cpu/Scripts/python cb_worker.py job.json
job.json: {"ref": "<reference wav>", "items": [{"text": ..., "out": "<wav path>", "exaggeration": 1.2, "cfg": 0.3,
           "temperature": 0.8, "seed": 7}, ...]}
Skips items whose wav already exists. Chatterbox is MIT licensed (Resemble AI). The reference is always one of
Kokoro's own synthetic voices, so no real person's voice is cloned.

Why CPU: Windows on this laptop has a 30 GB commit limit and the CUDA build of torch alone reserves a few GB of it;
with Blender idle there is still not enough left for the CUDA build plus the 3 GB model. The CPU build fits.
"""
import json, os, struct, sys
import torch, torchaudio
import chatterbox.tts as ct
from huggingface_hub import hf_hub_download
from pathlib import Path

DT = {"F32": torch.float32, "F16": torch.float16, "BF16": torch.bfloat16, "I64": torch.int64, "I32": torch.int32,
      "BOOL": torch.bool, "U8": torch.uint8, "I8": torch.int8}

def fill(model, path):
    """Copy a safetensors checkpoint into an already built model one tensor at a time. The stock loader keeps a full
    state dict next to the model, which is one copy too many for this laptop's memory."""
    target = model.state_dict()
    with open(path, "rb") as f, torch.no_grad():
        n = struct.unpack("<Q", f.read(8))[0]
        head = json.loads(f.read(n))
        for name, info in head.items():
            if name == "__metadata__" or name not in target:
                continue
            a, b = info["data_offsets"]
            f.seek(8 + n + a)
            target[name].copy_(torch.frombuffer(bytearray(f.read(b - a)), dtype=DT[info["dtype"]]).reshape(info["shape"]))
    return model.eval()

def load():
    for fname in ("ve.safetensors", "t3_cfg.safetensors", "s3gen.safetensors", "tokenizer.json", "conds.pt"):
        d = Path(hf_hub_download("ResembleAI/chatterbox", fname)).parent
    ve = fill(ct.VoiceEncoder(), d / "ve.safetensors")
    if os.environ.get("CB_BF16", "1") == "1":
        # the 0.5B text-to-speech-token model in bfloat16 halves its 2 GB, which is what lets this fit
        torch.set_default_dtype(torch.bfloat16)
        t3 = fill(ct.T3(), d / "t3_cfg.safetensors")
        torch.set_default_dtype(torch.float32)
        run = t3.inference
        t3.inference = lambda *a, t3_cond, **k: run(*a, t3_cond=t3_cond.to(device="cpu", dtype=torch.bfloat16), **k)
    else:
        t3 = fill(ct.T3(), d / "t3_cfg.safetensors")
    s3gen = fill(ct.S3Gen(), d / "s3gen.safetensors")
    conds = ct.Conditionals.load(d / "conds.pt", map_location=torch.device("cpu"))
    return ct.ChatterboxTTS(t3, s3gen, ve, ct.EnTokenizer(str(d / "tokenizer.json")), "cpu", conds=conds)

def main(job_path):
    job = json.load(open(job_path))
    todo = [it for it in job["items"] if not os.path.exists(it["out"])]
    if not todo:
        return
    torch.set_num_threads(max(1, (os.cpu_count() or 4) - 1))
    m = load()
    for it in todo:
        torch.manual_seed(it.get("seed", 7))
        wav = m.generate(it["text"], audio_prompt_path=job["ref"], exaggeration=it.get("exaggeration", 0.5),
                         cfg_weight=it.get("cfg", 0.5), temperature=it.get("temperature", 0.8))
        os.makedirs(os.path.dirname(it["out"]), exist_ok=True)
        torchaudio.save(it["out"] + ".part.wav", wav.cpu(), m.sr)
        os.replace(it["out"] + ".part.wav", it["out"])
        print("voiced", os.path.basename(it["out"]), round(wav.shape[-1] / m.sr, 2), "s", flush=True)

if __name__ == "__main__":
    main(sys.argv[1])
