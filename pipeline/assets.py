"""Real CC0 assets from Poly Haven (polyhaven.com, all CC0: free for commercial use, no attribution needed).

python assets.py model lightbulb_led 2k       -> vendor/assets/lightbulb_led/  (glTF + textures)
python assets.py texture black_walnut_veneer_01 2k
python assets.py hdri brown_photostudio_02 2k
In Blender scenes, use model_path(), texture_maps() and hdri_path() to find what was fetched. Files live in vendor/
(gitignored); a scene's render script calls fetch() so a fresh machine downloads what it needs.
"""
import json, os, sys, urllib.request
ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, "vendor", "assets")
API = "https://api.polyhaven.com"

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "overthought-pipeline"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

def _save(url, path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = _get(url)
        with open(path + ".part", "wb") as f:
            f.write(data)
        os.replace(path + ".part", path)
    return path

def fetch(kind, asset, res="2k"):
    files = json.loads(_get(f"{API}/files/{asset}"))
    out = os.path.join(DIR, asset)
    if kind == "model":
        g = files["gltf"][res]["gltf"]
        main = _save(g["url"], os.path.join(out, os.path.basename(g["url"])))
        for rel, f in g.get("include", {}).items():
            _save(f["url"], os.path.join(out, rel))
        return main
    if kind == "texture":
        maps = {}
        for m in ("Diffuse", "nor_gl", "Rough", "Displacement", "AO", "arm"):
            if m in files and res in files[m]:
                f = files[m][res].get("jpg") or files[m][res].get("png")
                maps[m] = _save(f["url"], os.path.join(out, os.path.basename(f["url"])))
        return maps
    if kind == "hdri":
        f = files["hdri"][res]["hdr"]
        return _save(f["url"], os.path.join(out, os.path.basename(f["url"])))
    raise ValueError(kind)

def model_path(asset):
    d = os.path.join(DIR, asset)
    return next(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".gltf"))

def texture_maps(asset):
    d = os.path.join(DIR, asset)
    keys = {"diff": "Diffuse", "nor_gl": "nor_gl", "rough": "Rough", "disp": "Displacement", "ao": "AO", "arm": "arm"}
    return {v: os.path.join(d, f) for f in os.listdir(d) for k, v in keys.items() if f"_{k}_" in f}

def hdri_path(asset):
    d = os.path.join(DIR, asset)
    return next(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".hdr"))

if __name__ == "__main__":
    print(fetch(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "2k"))
