"""Chatterbox Turbo narration worker (Resemble AI, MIT, 350M parameters). Runs inside vendor/venv_chatterbox_cpu on the
CPU, like cb_worker.py, and takes the same job file:

vendor/venv_chatterbox_cpu/Scripts/python cbt_worker.py job.json
job.json: {"ref": "<reference wav>", "items": [{"text": ..., "out": "<wav path>", "temperature": 0.8, "seed": 7}, ...]}

Turbo ignores exaggeration and cfg. The reference is the same synthetic Kokoro voice the regular model clones, so no real
person's voice is cloned. Weights are filled in one tensor at a time (cb_worker.fill) to fit this laptop's commit limit.
Skips items whose wav already exists.
"""
import json, os, sys
import numpy as np
import torch, torchaudio
from pathlib import Path
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer
import chatterbox.tts_turbo as tt
from cb_worker import fill

FILES = ["ve.safetensors", "t3_turbo_v1.safetensors", "s3gen_meanflow.safetensors", "*.json", "*.txt", "conds.pt", "*.model"]

def load():
    d = Path(snapshot_download(tt.REPO_ID, allow_patterns=FILES))
    ve = fill(tt.VoiceEncoder(), d / "ve.safetensors")
    hp = tt.T3Config(text_tokens_dict_size=50276)           # Turbo's settings, as in ChatterboxTurboTTS.from_local
    hp.llama_config_name = "GPT2_medium"
    hp.speech_tokens_dict_size = 6563
    hp.input_pos_emb = None
    hp.speech_cond_prompt_len = 375
    hp.use_perceiver_resampler = False
    hp.emotion_adv = False
    t3 = fill(tt.T3(hp), d / "t3_turbo_v1.safetensors")
    del t3.tfmr.wte
    s3gen = fill(tt.S3Gen(meanflow=True), d / "s3gen_meanflow.safetensors")
    tok = AutoTokenizer.from_pretrained(d)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    return tt.ChatterboxTurboTTS(t3, s3gen, ve, tok, "cpu", conds=None)

def main(job_path):
    job = json.load(open(job_path))
    todo = [it for it in job["items"] if not os.path.exists(it["out"])]
    if not todo:
        return
    torch.set_num_threads(max(1, (os.cpu_count() or 4) - 1))
    m = load()
    # Turbo's loudness step multiplies by a float64 gain, which turns the reference into float64 and breaks the mel
    # filter (float32) in the speech tokenizer: "expected scalar type Double but found Float" (Nov 12)
    norm = m.norm_loudness
    m.norm_loudness = lambda *a, **k: norm(*a, **k).astype(np.float32)
    m.prepare_conditionals(job["ref"])
    for it in todo:
        torch.manual_seed(it.get("seed", 7))
        with torch.inference_mode():
            wav = m.generate(it["text"], temperature=it.get("temperature", 0.8))
        os.makedirs(os.path.dirname(it["out"]), exist_ok=True)
        torchaudio.save(it["out"] + ".part.wav", wav.cpu(), m.sr)
        os.replace(it["out"] + ".part.wav", it["out"])
        print("voiced", os.path.basename(it["out"]), round(wav.shape[-1] / m.sr, 2), "s", flush=True)

if __name__ == "__main__":
    main(sys.argv[1])
