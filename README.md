# Overthought

Source and video hosting for [@overthought.daily](https://www.instagram.com/overthought.daily/).
Every video is drawn in code (Python + Skia, and Blender driven from Python for the 3D formats), with physics from pymunk and sound synthesized from scratch.

- `pipeline/` renderers for each format (`render_elim.py`, `render_fold.py`) and shared helpers (`common.py`)
- Finished videos live in `videos/`, which is where Instagram publishing pulls them from

Setup on a fresh machine: `pipeline/setup.sh`
