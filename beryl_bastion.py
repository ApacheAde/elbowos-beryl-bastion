#!/usr/bin/env python3
"""Beryl Bastion — neon tower-lite arcade. Arrow/A-D aim slot, Space place turret.
Headless reel:  python3 beryl_bastion.py --record
Play:            python3 beryl_bastion.py
Featured: https://x.com/ElbowOS
"""
from __future__ import annotations
import math, os, random, subprocess, sys

W, H = 1080, 1920
FPS = 30
TITLE = "BERYL BASTION"
HANDLE = "x.com/ElbowOS"
RECORD_SEC = 15

# Deep jade + gold + magenta — distinct from prior cyan grids
BG = (6, 14, 18)
PATH_COL = (18, 72, 64)
PATH_GLOW = (40, 210, 160)
GOLD = (255, 210, 90)
MAG = (255, 70, 160)
CYAN = (80, 255, 220)
CREEP_COL = (255, 90, 70)
CORE_COL = (180, 255, 140)
HUD = (230, 240, 235)


def lerp(a, b, t):
    return a + (b - a) * t


def path_points():
    pts = []
    segs = [
        (140, 280), (940, 280), (940, 560), (160, 560),
        (160, 860), (920, 860), (920, 1160), (180, 1160),
        (180, 1480), (540, 1480), (540, 1720),
    ]
    for i in range(len(segs) - 1):
        x0, y0 = segs[i]
        x1, y1 = segs[i + 1]
        n = max(8, int(math.hypot(x1 - x0, y1 - y0) / 18))
        for k in range(n):
            t = k / n
            pts.append((lerp(x0, x1, t), lerp(y0, y1, t)))
    pts.append(segs[-1])
    return pts


PATH = path_points()


def build_slots():
    out = []
    used = set()
    for i, (x, y) in enumerate(PATH):
        if i % 14 != 0:
            continue
        for dx, dy in ((0, -78), (0, 78), (-78, 0), (78, 0)):
            sx, sy = int(x + dx), int(y + dy)
            key = (sx // 40, sy // 40)
            if key in used:
                continue
            if 80 < sx < W - 80 and 260 < sy < H - 220:
                used.add(key)
                out.append((sx, sy))
    return out


SLOTS = build_slots()


class Creep:
    def __init__(self, hp, spd):
        self.i = 0.0
        self.hp = hp
        self.maxhp = hp
        self.spd = spd
        self.alive = True
        self.r = 18

    @property
    def pos(self):
        i = min(int(self.i), len(PATH) - 1)
        return PATH[i]

    def step(self):
        self.i += self.spd
        if self.i >= len(PATH) - 1:
            self.alive = False
            return "leak"
        return None


class Turret:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.cd = 0
        self.range = 168
        self.cool = 10

    def aim(self, creeps):
        best, bd = None, self.range
        for c in creeps:
            if not c.alive:
                continue
            px, py = c.pos
            d = math.hypot(px - self.x, py - self.y)
            if d < bd:
                best, bd = c, d
        return best


class Shot:
    def __init__(self, x, y, tx, ty):
        self.x, self.y = x, y
        ang = math.atan2(ty - y, tx - x)
        self.vx = math.cos(ang) * 22
        self.vy = math.sin(ang) * 22
        self.life = 28

    def step(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1


class Game:
    def __init__(self, auto=False):
        self.auto = auto
        self.creeps = []
        self.turrets = []
        self.shots = []
        self.fx = []
        self.score = 0
        self.lives = 8
        self.wave = 1
        self.spawn_cd = 20
        self.spawned = 0
        self.wave_size = 6
        self.sel = 0
        self.tick = 0
        self.over = False
        self.pulse = 0.0

    def spawn(self):
        hp = 2 + self.wave
        spd = 0.55 + self.wave * 0.06
        self.creeps.append(Creep(hp, spd))
        self.spawned += 1

    def place(self, idx):
        if idx < 0 or idx >= len(SLOTS):
            return
        x, y = SLOTS[idx]
        if any(abs(t.x - x) < 8 and abs(t.y - y) < 8 for t in self.turrets):
            return
        self.turrets.append(Turret(x, y))

    def update(self):
        self.tick += 1
        self.pulse = 0.5 + 0.5 * math.sin(self.tick * 0.12)
        if self.over:
            return
        if self.auto:
            if self.tick % 18 == 0 and len(self.turrets) < 10:
                empty = [i for i, s in enumerate(SLOTS)
                         if not any(abs(t.x - s[0]) < 8 and abs(t.y - s[1]) < 8
                                    for t in self.turrets)]
                if empty:
                    mid = sorted(empty, key=lambda i: abs(SLOTS[i][1] - 980))
                    self.place(mid[self.tick % max(1, min(4, len(mid)))])
                    self.sel = mid[0]
            self.sel = (self.sel + (1 if self.tick % 7 == 0 else 0)) % len(SLOTS)

        self.spawn_cd -= 1
        if self.spawn_cd <= 0 and self.spawned < self.wave_size:
            self.spawn()
            self.spawn_cd = max(12, 28 - self.wave * 2)
        if self.spawned >= self.wave_size and not any(c.alive for c in self.creeps):
            self.wave += 1
            self.spawned = 0
            self.wave_size = 5 + self.wave * 2
            self.spawn_cd = 25

        for c in self.creeps:
            if not c.alive:
                continue
            r = c.step()
            if r == "leak":
                self.lives -= 1
                if self.lives <= 0:
                    self.over = True
        self.creeps = [c for c in self.creeps if c.alive]

        for t in self.turrets:
            t.cd = max(0, t.cd - 1)
            if t.cd == 0:
                tgt = t.aim(self.creeps)
                if tgt:
                    px, py = tgt.pos
                    self.shots.append(Shot(t.x, t.y, px, py))
                    t.cd = t.cool

        for s in self.shots:
            s.step()
            for c in self.creeps:
                if not c.alive:
                    continue
                px, py = c.pos
                if math.hypot(s.x - px, s.y - py) < c.r + 8:
                    c.hp -= 1
                    s.life = 0
                    self.fx.append([px, py, 10, GOLD])
                    if c.hp <= 0:
                        c.alive = False
                        self.score += 25 + self.wave * 5
                        self.fx.append([px, py, 22, MAG])
                    break
        self.shots = [s for s in self.shots if s.life > 0]
        self.fx = [[x, y, n - 1, col] for x, y, n, col in self.fx if n > 1]

    def draw(self, surf, font, font_sm):
        import pygame
        surf.fill(BG)
        rng = random.Random(3)
        for _ in range(70):
            x = rng.randrange(W)
            y = (rng.randrange(H) + self.tick * 2) % H
            pygame.draw.circle(surf, (20, 50, 48), (x, y), rng.choice((1, 1, 2)))
        if len(PATH) > 1:
            pygame.draw.lines(surf, PATH_COL, False, PATH, 54)
            pygame.draw.lines(surf, PATH_GLOW, False, PATH, 8)
        pygame.draw.circle(surf, PATH_GLOW, (int(PATH[0][0]), int(PATH[0][1])), 22)
        cx, cy = PATH[-1]
        pygame.draw.circle(surf, CORE_COL, (int(cx), int(cy)), int(28 + 6 * self.pulse))
        pygame.draw.circle(surf, BG, (int(cx), int(cy)), 14)
        for i, (sx, sy) in enumerate(SLOTS):
            occ = any(abs(t.x - sx) < 8 and abs(t.y - sy) < 8 for t in self.turrets)
            col = (60, 90, 80) if occ else (30, 55, 50)
            pygame.draw.circle(surf, col, (sx, sy), 16, 2)
            if i == self.sel and not occ:
                pygame.draw.circle(surf, GOLD, (sx, sy), int(18 + 4 * self.pulse), 2)
        for t in self.turrets:
            pygame.draw.circle(surf, (20, 70, 55), (int(t.x), int(t.y)), 22)
            pygame.draw.circle(surf, GOLD, (int(t.x), int(t.y)), 18)
            pygame.draw.circle(surf, (40, 30, 10), (int(t.x), int(t.y)), 8)
            pygame.draw.circle(surf, PATH_GLOW, (int(t.x), int(t.y)), t.range, 1)
        for c in self.creeps:
            px, py = c.pos
            pygame.draw.circle(surf, CREEP_COL, (int(px), int(py)), c.r)
            pygame.draw.circle(surf, (255, 200, 180), (int(px - 5), int(py - 4)), 5)
            bw = 28
            pygame.draw.rect(surf, (40, 10, 10), (px - 14, py - 28, bw, 5))
            pygame.draw.rect(surf, MAG, (px - 14, py - 28, bw * max(0, c.hp) / c.maxhp, 5))
        for s in self.shots:
            pygame.draw.circle(surf, CYAN, (int(s.x), int(s.y)), 6)
            pygame.draw.circle(surf, (255, 255, 255), (int(s.x), int(s.y)), 3)
        for x, y, n, col in self.fx:
            pygame.draw.circle(surf, col, (int(x), int(y)), n, 2)
        pygame.draw.rect(surf, (8, 22, 24), (0, 0, W, 210))
        pygame.draw.rect(surf, PATH_GLOW, (0, 210, W, 4))
        title = font.render(TITLE, True, GOLD)
        surf.blit(title, title.get_rect(center=(W // 2, 72)))
        sub = font_sm.render(HANDLE, True, CYAN)
        surf.blit(sub, sub.get_rect(center=(W // 2, 128)))
        info = font_sm.render(
            f"SCORE  {self.score}    WAVE  {self.wave}    CORE  {max(0, self.lives)}",
            True, HUD,
        )
        surf.blit(info, info.get_rect(center=(W // 2, 176)))
        pygame.draw.rect(surf, (8, 22, 24), (0, H - 90, W, 90))
        pygame.draw.rect(surf, PATH_GLOW, (0, H - 90, W, 4))
        help_t = font_sm.render("A/D slot   SPACE plant turret   R restart", True, HUD)
        surf.blit(help_t, help_t.get_rect(center=(W // 2, H - 46)))
        if self.over:
            go = font.render("CORE BREACHED", True, MAG)
            surf.blit(go, go.get_rect(center=(W // 2, H // 2)))


def record_mp4(out_path):
    import pygame
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    surf = pygame.Surface((W, H))
    font = pygame.font.SysFont("dejavusans", 64, bold=True) or pygame.font.Font(None, 72)
    font_sm = pygame.font.SysFont("dejavusans", 36, bold=True) or pygame.font.Font(None, 40)
    g = Game(auto=True)
    frames = RECORD_SEC * FPS
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
        "-movflags", "+faststart", "-an", out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    try:
        for _ in range(frames):
            g.update()
            g.draw(surf, font, font_sm)
            raw = pygame.image.tostring(surf, "RGB")
            proc.stdin.write(raw)
        proc.stdin.close()
        err = proc.stderr.read()
        rc = proc.wait()
        if rc != 0:
            raise RuntimeError(err.decode("utf-8", "ignore")[-1500:])
    finally:
        pygame.quit()


def play():
    import pygame
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption(f"{TITLE} — {HANDLE}")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("dejavusans", 64, bold=True) or pygame.font.Font(None, 72)
    font_sm = pygame.font.SysFont("dejavusans", 36, bold=True) or pygame.font.Font(None, 40)
    g = Game(auto=False)
    run = True
    while run:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    run = False
                elif e.key == pygame.K_r:
                    g = Game(auto=False)
                elif e.key in (pygame.K_LEFT, pygame.K_a):
                    g.sel = (g.sel - 1) % len(SLOTS)
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    g.sel = (g.sel + 1) % len(SLOTS)
                elif e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    g.place(g.sel)
        g.update()
        g.draw(screen, font, font_sm)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    if "--record" in sys.argv:
        out = "/home/workdir/artifacts/BerylBastion_ElbowOS.mp4"
        if len(sys.argv) > sys.argv.index("--record") + 1:
            nxt = sys.argv[sys.argv.index("--record") + 1]
            if not nxt.startswith("-"):
                out = nxt
        record_mp4(out)
        print("wrote", out)
    else:
        play()
