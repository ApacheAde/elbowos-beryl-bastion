# Beryl Bastion

Full-colour **Python 3** neon tower-lite arcade for ElbowOS.

Plant gold beryl turrets along a jade path. Red creeps march an S-curve toward the core. Keep the core alive. Score for every shatter.

Featured / shout-out: **https://x.com/ElbowOS**

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 beryl_bastion.py
```

Controls: **A / D** or arrows cycle a pad · **Space** plant a turret · **R** restart · **Esc** quit.

Needs Python 3.10+ and a desktop window (pygame + SDL).

## Record a 9:16 reel

```bash
SDL_VIDEODRIVER=dummy python3 beryl_bastion.py --record
```

Writes a 15s 1080×1920 H.264 MP4 (title, score, and `x.com/ElbowOS` burned into every frame).

## Links

- Reel MP4 (Google Drive): https://drive.google.com/file/d/1E4qSzBBVDYJhKDXRvfQILyVFIwA9dIom/view?usp=drivesdk
- Reel folder: https://drive.google.com/drive/folders/1-BaLchrqoZB9irFFZH0UQZxnSHhgmPns
- Featured account: https://x.com/ElbowOS

Original rules and art. Not a ROM, not an emulator, not a clone of a prior ElbowOS pack.
