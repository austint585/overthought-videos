"""Voice shootout (Austin, Nov 10: "can you look at these free reconstructed elevenlabs"): the same lines from recent
episodes voiced by each engine through the exact same pipeline (at least 3 takes a line, the take nearest the median
pace, voice_fix, qa_voice), so the only difference is the voice model.

python voice_shootout.py [cb turbo qwen]     -> out/shootout/<engine>/narration_fixed.wav, a measurement table, and
                                              out/shootout/2026-11-11_Voice_<n>_<Engine>.m4a for listening

Engines (narrate_cb.ENGINES): cb = Chatterbox, the voice in use since Oct 29; turbo = Chatterbox Turbo (Resemble AI, MIT,
350M); qwen = Qwen3-TTS 1.7B (Alibaba, Apache 2.0), a narrator designed from a text description and cloned with the Base
model. Run one engine at a time and never next to Blender or an encode (this laptop's memory).
"""
import os, subprocess, sys, time
from common import ROOT
import narrate_cb, voice_fix, qa_voice

LINES = [
    "Breaking the *touch barrier* first? That is *quantum tunneling.*",
    "Between you two sits a barrier. Neither of you has the *energy* to get over it.",
    "A normal day only spawns *two* wish windows. Two minutes out of *1,440.*{fourteen forty.}",
    "That's a *0.14%*{zero point one four percent} drop rate.",
    "Pause the video now. Whatever you stopped on is your *next relationship.*",
    "No rerolls. The machine has *spoken.*",
    "He was not built for this. Total *collapse.*",
    "Send this to whoever breaks the barrier first.",
]
NAMES = {"cb": "1_Chatterbox_Current", "turbo": "2_Chatterbox_Turbo", "qwen": "3_Qwen3_TTS"}

def run(engine):
    d = os.path.join(ROOT, "out", "shootout", engine)
    os.makedirs(d, exist_ok=True)
    t = time.time()
    narrate_cb.narrate(LINES, d, exaggeration=0.5, cfg=0.4, gap=0.26, engine=engine)
    took = time.time() - t
    voice_fix.fixed(d)
    print(f"\n== {engine}: voiced in {took / 60:.1f} min")
    ok = qa_voice.check(d, "narration_fixed")
    m4a = os.path.join(ROOT, "out", "shootout", f"2026-11-11_Voice_{NAMES[engine]}.m4a")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(d, "narration_fixed.wav"),
                    "-af", "loudnorm=I=-16:TP=-1.5", "-c:a", "aac", "-b:a", "160k", m4a], check=True)
    return ok, took

if __name__ == "__main__":
    for e in sys.argv[1:] or ["cb", "turbo", "qwen"]:
        run(e)
