"""Qwen3-TTS narration worker (Alibaba Qwen team, Apache 2.0). Runs inside vendor/venv_qwen3tts on the GPU (CUDA torch,
bfloat16, weights loaded straight to the card so they don't count against this laptop's ~27 GB commit limit).

vendor/venv_qwen3tts/Scripts/python qwen_worker.py job.json

Clone job (narrate_cb's format; the Base 1.7B model):
  {"ref": "<reference wav>", "ref_text": "<its exact words>", "items": [{"text": ..., "out": "<wav>", "seed": 7}, ...]}
Design job (the VoiceDesign 1.7B model builds a voice from a description; used once to make the reference clip):
  {"design": {"instruct": "<voice description>", "text": "<words to say>"}, "items": [{"out": "<wav>", "seed": 7}, ...]}
  An item may carry its own "instruct" and "text" to design a different voice in the same model load.

The narrator is designed from a text description, never cloned from a real person. Skips items whose wav exists.
"""
import json, os, struct, sys
os.environ.setdefault("HF_HUB_OFFLINE", "1")              # the models are in the local cache; no network at run time
import numpy as np
import soundfile as sf
import torch
import transformers.modeling_utils as hf_load
from huggingface_hub import snapshot_download
from qwen_tts import Qwen3TTSModel

BASE = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
DESIGN = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
GEN = {"max_new_tokens": 1200}     # 12 codec frames a second: 100 s, a stop for a runaway take; the rest are the model's defaults
DT = {"F32": torch.float32, "F16": torch.float16, "BF16": torch.bfloat16, "I64": torch.int64, "I32": torch.int32,
      "I16": torch.int16, "I8": torch.int8, "U8": torch.uint8, "BOOL": torch.bool}

class PlainRead:
    """Stands in for safetensors.safe_open in transformers' loader. safe_open maps the whole 3.8 GB file as private
    memory, which this laptop's commit limit can't spare (Nov 11: 40 crashes, access violations and os error 1455);
    this reads one tensor at a time with plain file reads and hands it straight to the GPU."""
    class Slice:
        def __init__(self, src, info):
            self.src, self.info = src, info
        def get_dtype(self):
            return self.info["dtype"]
        def get_shape(self):
            return self.info["shape"]
        def __getitem__(self, idx):
            return self.src.read(self.info)[idx]
    def __init__(self, path, framework="pt", device="cpu"):
        self.f = open(path, "rb")
        n = struct.unpack("<Q", self.f.read(8))[0]
        self.head, self.base = json.loads(self.f.read(n)), 8 + n
        self.device = f"cuda:{device}" if isinstance(device, int) else device
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        self.f.close()
    def __del__(self):
        self.f.close()
    def metadata(self):
        return self.head.get("__metadata__")
    def keys(self):
        return [k for k in self.head if k != "__metadata__"]
    def read(self, info):
        a, b = info["data_offsets"]
        self.f.seek(self.base + a)
        t = torch.frombuffer(bytearray(self.f.read(b - a)), dtype=DT[info["dtype"]]) if b > a else torch.empty(0, dtype=DT[info["dtype"]])
        return t.reshape(info["shape"]).to(self.device)
    def get_slice(self, k):
        return PlainRead.Slice(self, self.head[k])
    def get_tensor(self, k):
        return self.read(self.head[k])

hf_load.safe_open = PlainRead

def load(repo):
    # the local snapshot folder, not the repo id: given an id, the tokenizer asks the Hub about it even offline
    path = snapshot_download(repo, local_files_only=True)
    return Qwen3TTSModel.from_pretrained(path, device_map="cuda:0", dtype=torch.bfloat16, attn_implementation="sdpa")

def save(path, wav, sr):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path + ".part.wav", np.asarray(wav, dtype=np.float32), sr)
    os.replace(path + ".part.wav", path)
    print("voiced", os.path.basename(path), round(len(wav) / sr, 2), "s", flush=True)

def main(job_path):
    job = json.load(open(job_path, encoding="utf-8"))
    todo = [it for it in job["items"] if not os.path.exists(it["out"])]
    if not todo:
        return
    if "design" in job:
        m = load(DESIGN)
        for it in todo:
            d = {**job["design"], **{k: it[k] for k in ("instruct", "text") if k in it}}   # an item may design its own voice
            torch.manual_seed(it.get("seed", 7))
            wavs, sr = m.generate_voice_design(text=d["text"], instruct=d["instruct"], language="English", **GEN)
            save(it["out"], wavs[0], sr)
        return
    m = load(BASE)
    prompt = m.create_voice_clone_prompt(ref_audio=job["ref"], ref_text=job["ref_text"])
    for it in todo:
        torch.manual_seed(it.get("seed", 7))
        extra = {"temperature": it["temperature"]} if "temperature" in it else {}
        wavs, sr = m.generate_voice_clone(text=it["text"], language="English", voice_clone_prompt=prompt, **GEN, **extra)
        save(it["out"], wavs[0], sr)

if __name__ == "__main__":
    main(sys.argv[1])
