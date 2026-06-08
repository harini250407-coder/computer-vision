import cv2
import numpy as np
import random
import time

# ── Window & Game Constants ──────────────────────────────────────────────────
W, H        = 480, 640
WIN         = "Flappy Bird (OpenCV)"
FPS         = 60

BIRD_X      = 90
BIRD_R      = 18
GRAVITY     = 0.4
FLAP_VEL    = -8.0
PIPE_W      = 55
GAP         = 150
PIPE_SPEED  = 3

# ── Colors (BGR) ─────────────────────────────────────────────────────────────
SKY         = (235, 220, 180)   # light blue-ish sky
GROUND_COL  = (80, 160, 210)    # brown ground
GRASS_COL   = (60, 180, 80)     # green grass
PIPE_COL    = (70, 175, 75)     # green pipe
PIPE_DK     = (45, 120, 46)     # darker green outline
BIRD_COL    = (30, 200, 245)    # yellow bird
BIRD_DK     = (20, 140, 200)    # dark yellow outline
BEAK_COL    = (20, 128, 240)    # orange beak
WING_COL    = (20, 168, 232)    # wing color
WHITE       = (255, 255, 255)
BLACK       = (0,   0,   0)
CLOUD_COL   = (245, 245, 245)
OVERLAY     = (0,   0,   0)     # black overlay (with alpha)

# ── State ────────────────────────────────────────────────────────────────────
class Bird:
    def __init__(self):
        self.x  = BIRD_X
        self.y  = float(H // 2 - 30)
        self.vy = 0.0
        self.flap_anim = 0

    def flap(self):
        self.vy = FLAP_VEL
        self.flap_anim = 8

    def update(self):
        self.vy += GRAVITY
        self.y  += self.vy
        if self.flap_anim > 0:
            self.flap_anim -= 1

    def draw(self, frame):
        x, y = int(self.x), int(self.y)

        # Wing
        wing_offset = int(6 + 4 * (self.flap_anim / 8 if self.flap_anim > 0 else 0))
        cv2.ellipse(frame, (x - 4, y + wing_offset),
                    (12, 7), 20, 0, 360, WING_COL, -1)

        # Body
        cv2.ellipse(frame, (x, y), (BIRD_R, BIRD_R - 4),
                    0, 0, 360, BIRD_COL, -1)
        cv2.ellipse(frame, (x, y), (BIRD_R, BIRD_R - 4),
                    0, 0, 360, BIRD_DK, 2)

        # Eye white
        cv2.circle(frame, (x + 8, y - 4), 6, WHITE, -1)
        # Pupil
        cv2.circle(frame, (x + 10, y - 4), 3, BLACK, -1)

        # Beak (triangle)
        beak = np.array([
            [x + 14, y - 2],
            [x + 23, y + 2],
            [x + 14, y + 5]
        ], np.int32)
        cv2.fillPoly(frame, [beak], BEAK_COL)


class Pipe:
    def __init__(self, x):
        self.x      = float(x)
        min_h       = 80
        max_h       = H - 140 - GAP
        self.top_h  = random.randint(min_h, max_h)
        self.scored = False

    def update(self):
        self.x -= PIPE_SPEED

    def draw(self, frame):
        x = int(self.x)
        cw = PIPE_W + 14          # cap width
        cx = x - 7                # cap x offset

        # ── Top pipe ──────────────────────────
        # Tube
        cv2.rectangle(frame, (x, 0), (x + PIPE_W, self.top_h - 16), PIPE_COL, -1)
        cv2.rectangle(frame, (x, 0), (x + PIPE_W, self.top_h - 16), PIPE_DK, 2)
        # Cap
        cv2.rectangle(frame, (cx, self.top_h - 24), (cx + cw, self.top_h), PIPE_COL, -1)
        cv2.rectangle(frame, (cx, self.top_h - 24), (cx + cw, self.top_h), PIPE_DK, 2)

        # ── Bottom pipe ───────────────────────
        bot_y = self.top_h + GAP
        # Cap
        cv2.rectangle(frame, (cx, bot_y), (cx + cw, bot_y + 24), PIPE_COL, -1)
        cv2.rectangle(frame, (cx, bot_y), (cx + cw, bot_y + 24), PIPE_DK, 2)
        # Tube
        cv2.rectangle(frame, (x, bot_y + 16), (x + PIPE_W, H), PIPE_COL, -1)
        cv2.rectangle(frame, (x, bot_y + 16), (x + PIPE_W, H), PIPE_DK, 2)

        # Light sheen on pipes
        cv2.line(frame, (x + 8, 0), (x + 8, self.top_h - 16), (180, 220, 180), 2)
        cv2.line(frame, (x + 8, bot_y + 16), (x + 8, H), (180, 220, 180), 2)

    def off_screen(self):
        return self.x + PIPE_W + 14 < 0

    def collides(self, bird):
        bx, by = bird.x, bird.y
        px, pw = self.x - 7, PIPE_W + 14
        if bx + BIRD_R - 5 > px and bx - BIRD_R + 5 < px + pw:
            if by - BIRD_R + 4 < self.top_h or by + BIRD_R - 4 > self.top_h + GAP:
                return True
        return False


# ── Cloud helper ─────────────────────────────────────────────────────────────
class Cloud:
    def __init__(self, x, y, r):
        self.x, self.y, self.r = float(x), y, r

    def update(self):
        self.x -= 0.4
        if self.x < -self.r * 2:
            self.x = W + self.r

    def draw(self, frame):
        x, y, r = int(self.x), self.y, self.r
        cv2.circle(frame, (x,      y),      r,          CLOUD_COL, -1)
        cv2.circle(frame, (x + r,  y - 5),  r * 3 // 4, CLOUD_COL, -1)
        cv2.circle(frame, (x - r // 2, y + 3), r // 2,  CLOUD_COL, -1)


# ── Drawing helpers ───────────────────────────────────────────────────────────
def draw_ground(frame, offset):
    cv2.rectangle(frame, (0, H - 55), (W, H), (80, 160, 210), -1)
    cv2.rectangle(frame, (0, H - 55), (W, H - 41), (60, 180, 80), -1)
    # Scrolling bumps
    for i in range(0, W + 20, 20):
        bx = (i + int(offset) % 20) % (W + 20)
        cv2.ellipse(frame, (bx, H - 55), (10, 8), 0, 180, 360, (40, 160, 60), -1)


def draw_text_centered(frame, text, y, font_scale=1.0, thickness=2, color=WHITE, shadow=True):
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
    tx = (W - tw) // 2
    if shadow:
        cv2.putText(frame, text, (tx + 2, y + 2), font,
                    font_scale, BLACK, thickness + 1, cv2.LINE_AA)
    cv2.putText(frame, text, (tx, y), font,
                font_scale, color, thickness, cv2.LINE_AA)


def draw_score(frame, score):
    draw_text_centered(frame, str(score), 60, font_scale=1.4, thickness=3)


def draw_overlay(frame, title, score=None, best=None):
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (W, H), OVERLAY, -1)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)
    draw_text_centered(frame, title,           H // 2 - 30, font_scale=1.3, thickness=3)
    draw_text_centered(frame, "SPACE to flap", H // 2 + 14, font_scale=0.6, thickness=1,
                       color=(200, 200, 200))
    if score is not None:
        draw_text_centered(frame, f"Score: {score}   Best: {best}",
                           H // 2 + 46, font_scale=0.55, thickness=1, color=(200, 200, 200))


# ── Main game loop ────────────────────────────────────────────────────────────
def main():
    cv2.namedWindow(WIN)

    clouds = [
        Cloud(60,  70,  28),
        Cloud(200, 100, 22),
        Cloud(340, 60,  32),
        Cloud(430, 120, 18),
    ]

    bird  = Bird()
    pipes = [Pipe(W + 20 + i * (W // 2)) for i in range(3)]
    score = 0
    best  = 0
    state = 'idle'      # 'idle' | 'play' | 'dead'
    ground_offset = 0.0
    last_time = time.time()

    def on_key(key):
        nonlocal state, score, bird, pipes, ground_offset
        if key == 32:            # SPACE
            if state in ('idle', 'dead'):
                state = 'play'
                bird  = Bird()
                pipes = [Pipe(W + 20 + i * (W // 2)) for i in range(3)]
                score = 0
                ground_offset = 0.0
            elif state == 'play':
                bird.flap()

    while True:
        now  = time.time()
        dt   = now - last_time
        last_time = now

        # ── Build frame ───────────────────────────────────────────────────
        frame = np.full((H, W, 3), SKY, dtype=np.uint8)

        # Clouds
        for c in clouds:
            if state == 'play':
                c.update()
            c.draw(frame)

        # Ground offset scroll
        if state == 'play':
            ground_offset += PIPE_SPEED

        draw_ground(frame, ground_offset)

        # Pipes
        if state == 'play':
            for p in pipes:
                p.update()
            pipes = [p for p in pipes if not p.off_screen()]
            last_pipe = pipes[-1]
            if last_pipe.x < W - W // 2:
                pipes.append(Pipe(int(last_pipe.x + W // 2)))

            # Score
            for p in pipes:
                if not p.scored and p.x + PIPE_W < bird.x:
                    p.scored = True
                    score   += 1
                    if score > best:
                        best = score

        for p in pipes:
            p.draw(frame)

        # Bird
        if state == 'play':
            bird.update()

        bird.draw(frame)

        # Collision
        if state == 'play':
            hit_ground   = bird.y + BIRD_R - 4 > H - 55
            hit_ceiling  = bird.y - BIRD_R + 4 < 0
            hit_pipe     = any(p.collides(bird) for p in pipes)
            if hit_ground or hit_ceiling or hit_pipe:
                state = 'dead'

        # HUD
        draw_score(frame, score)

        if state == 'idle':
            draw_overlay(frame, "Flappy Bird")
        elif state == 'dead':
            draw_overlay(frame, "Game Over", score, best)

        # Best score top-right
        cv2.putText(frame, f"Best:{best}", (W - 110, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2, cv2.LINE_AA)

        cv2.imshow(WIN, frame)

        # ── Input ─────────────────────────────────────────────────────────
        key = cv2.waitKey(max(1, int(1000 / FPS - dt * 1000)))
        if key == 27:            # ESC → quit
            break
        on_key(key & 0xFF)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()