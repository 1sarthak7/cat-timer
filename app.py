"""
🐱 Kitty Timer & Alarm Clock
A cute cat-themed timer and alarm clock with a pink UI and smooth animations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import time
import threading
import os
import sys
import subprocess
import math
import random

# ─── Color Palette ───────────────────────────────────────────────────────────
PINK_DARK      = "#E75480"
PINK_MAIN      = "#FF69B4"
PINK_LIGHT     = "#FFB6C1"
PINK_PALE      = "#FFF0F5"
PINK_ACCENT    = "#FF1493"
WHITE          = "#FFFFFF"
PINK_BTN_HOVER = "#FF85C8"
PINK_TEXT      = "#C2185B"
GRAY_TEXT      = "#9E9E9E"
DARK_TEXT      = "#4A2040"

# Gradient shades for smooth transitions
PINK_SHADES = [
    "#FFB6C1", "#FF9FB4", "#FF85C8", "#FF7EB8",
    "#FF69B4", "#FF5CA8", "#FF4F9C", "#FF1493",
]

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


def resource_path(filename):
    return os.path.join(ASSETS_DIR, filename)


def play_alert_sound():
    """Play a system alert sound cross-platform."""
    try:
        if sys.platform == "darwin":
            subprocess.Popen(
                ["afplay", "/System/Library/Sounds/Glass.aiff"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif sys.platform == "win32":
            import winsound
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
        else:
            subprocess.Popen(
                ["paplay", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
    except Exception:
        print("\a")


# ─── Easing Functions ────────────────────────────────────────────────────────
def ease_in_out_cubic(t):
    """Smooth easing for animations."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2


def ease_out_back(t):
    """Bouncy overshoot easing."""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def ease_out_elastic(t):
    """Elastic/springy easing."""
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


def lerp_color(c1, c2, t):
    """Linearly interpolate between two hex colors."""
    t = max(0, min(1, t))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ═══════════════════════════════════════════════════════════════════════════════
#  Animated Button
# ═══════════════════════════════════════════════════════════════════════════════
class AnimatedButton(tk.Canvas):
    """A button with smooth hover color fade, press scale, and ripple effect."""

    def __init__(self, parent, text, command, bg_color, fg_color=WHITE,
                 font=("Helvetica Neue", 12, "bold"), padx=20, pady=10, **kw):
        self.btn_width = kw.pop("width", 130)
        self.btn_height = kw.pop("height", 42)
        super().__init__(parent, width=self.btn_width, height=self.btn_height,
                         bg=parent.cget("bg") if isinstance(parent, tk.Frame) else PINK_PALE,
                         highlightthickness=0, **kw)

        self.text = text
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.font = font
        self._current_bg = bg_color
        self._hover = False
        self._pressed = False
        self._disabled = False
        self._anim_id = None
        self._ripples = []

        self._draw()

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self):
        self.delete("all")
        w, h = self.btn_width, self.btn_height
        r = 12  # corner radius

        # Draw rounded rectangle
        self._draw_rounded_rect(2, 2, w - 2, h - 2, r, self._current_bg)

        # Draw ripples
        for ripple in self._ripples:
            rx, ry, rr, alpha = ripple
            ripple_color = lerp_color(self._current_bg, WHITE, alpha * 0.3)
            self.create_oval(rx - rr, ry - rr, rx + rr, ry + rr,
                             fill="", outline=ripple_color, width=2, tags="ripple")

        # Draw text
        fg = self.fg_color if not self._disabled else GRAY_TEXT
        self.create_text(w / 2, h / 2, text=self.text, font=self.font,
                         fill=fg, tags="text")

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, fill):
        """Draw a rounded rectangle on canvas."""
        self.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90,
                        fill=fill, outline="", tags="bg")
        self.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90,
                        fill=fill, outline="", tags="bg")
        self.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90,
                        fill=fill, outline="", tags="bg")
        self.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90,
                        fill=fill, outline="", tags="bg")
        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="", tags="bg")
        self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="", tags="bg")

    def _on_enter(self, e):
        if self._disabled:
            return
        self._hover = True
        self.config(cursor="hand2")
        self._animate_color(self._current_bg, PINK_BTN_HOVER, 200)

    def _on_leave(self, e):
        if self._disabled:
            return
        self._hover = False
        self.config(cursor="")
        self._animate_color(self._current_bg, self.bg_color, 200)

    def _on_press(self, e):
        if self._disabled:
            return
        self._pressed = True
        self._current_bg = PINK_ACCENT
        self._draw()
        # Start ripple
        self._start_ripple(e.x, e.y)

    def _on_release(self, e):
        if self._disabled:
            return
        self._pressed = False
        target = PINK_BTN_HOVER if self._hover else self.bg_color
        self._animate_color(self._current_bg, target, 150)
        if self.command and 0 <= e.x <= self.btn_width and 0 <= e.y <= self.btn_height:
            self.command()

    def _animate_color(self, from_color, to_color, duration_ms):
        """Smooth color transition over duration."""
        if self._anim_id:
            self.after_cancel(self._anim_id)
        steps = max(1, duration_ms // 16)  # ~60fps
        step = [0]

        def tick():
            if step[0] > steps:
                return
            t = step[0] / steps
            t = ease_in_out_cubic(t)
            self._current_bg = lerp_color(from_color, to_color, t)
            self._draw()
            step[0] += 1
            self._anim_id = self.after(16, tick)

        tick()

    def _start_ripple(self, x, y):
        """Expanding circle ripple from click point."""
        max_r = max(self.btn_width, self.btn_height)
        step = [0]
        total = 20

        def tick():
            if step[0] > total:
                self._ripples.clear()
                self._draw()
                return
            t = step[0] / total
            r = max_r * ease_in_out_cubic(t)
            alpha = 1 - t
            self._ripples = [(x, y, r, alpha)]
            self._draw()
            step[0] += 1
            self.after(16, tick)

        tick()

    def set_text(self, text):
        self.text = text
        self._draw()

    def set_disabled(self, disabled):
        self._disabled = disabled
        if disabled:
            self._current_bg = lerp_color(self.bg_color, PINK_PALE, 0.6)
            self.config(cursor="")
        else:
            self._current_bg = self.bg_color
        self._draw()


# ═══════════════════════════════════════════════════════════════════════════════
#  Sparkle Particle System
# ═══════════════════════════════════════════════════════════════════════════════
class SparkleOverlay:
    """Canvas-based sparkle/confetti particles."""

    def __init__(self, canvas, cx, cy):
        self.canvas = canvas
        self.particles = []
        self.running = False
        colors = ["#FFD700", "#FF69B4", "#FF1493", "#FFC0CB", "#FFB6C1",
                  "#FF6B81", "#FF85C8", "#FFDAB9", "#FFF0F5"]
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            self.particles.append({
                "x": cx, "y": cy,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - random.uniform(1, 3),
                "size": random.uniform(3, 8),
                "color": random.choice(colors),
                "life": random.uniform(0.7, 1.0),
                "decay": random.uniform(0.015, 0.03),
                "shape": random.choice(["star", "circle", "diamond"]),
                "rotation": random.uniform(0, 360),
                "rot_speed": random.uniform(-10, 10),
            })

    def start(self):
        self.running = True
        self._tick()

    def _tick(self):
        if not self.running:
            return
        self.canvas.delete("sparkle")
        alive = False
        for p in self.particles:
            if p["life"] <= 0:
                continue
            alive = True
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.15  # gravity
            p["life"] -= p["decay"]
            p["rotation"] += p["rot_speed"]

            alpha = max(0, p["life"])
            size = p["size"] * alpha

            if p["shape"] == "star":
                self._draw_star(p["x"], p["y"], size, p["color"], p["rotation"])
            elif p["shape"] == "diamond":
                self._draw_diamond(p["x"], p["y"], size, p["color"], p["rotation"])
            else:
                self.canvas.create_oval(
                    p["x"] - size, p["y"] - size,
                    p["x"] + size, p["y"] + size,
                    fill=p["color"], outline="", tags="sparkle"
                )

        if alive:
            self.canvas.after(16, self._tick)
        else:
            self.running = False
            self.canvas.delete("sparkle")

    def _draw_star(self, x, y, size, color, rotation):
        points = []
        for i in range(10):
            angle = math.radians(rotation + i * 36)
            r = size if i % 2 == 0 else size * 0.4
            points.extend([x + r * math.cos(angle), y + r * math.sin(angle)])
        if len(points) >= 6:
            self.canvas.create_polygon(points, fill=color, outline="", tags="sparkle")

    def _draw_diamond(self, x, y, size, color, rotation):
        rad = math.radians(rotation)
        points = []
        for i in range(4):
            angle = rad + i * math.pi / 2
            points.extend([x + size * math.cos(angle), y + size * math.sin(angle)])
        self.canvas.create_polygon(points, fill=color, outline="", tags="sparkle")


# ═══════════════════════════════════════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════════════════════════════════════
class KittyTimerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🐱 Kitty Timer & Alarm")
        self.configure(bg=PINK_PALE)
        self.resizable(False, False)

        # ── Window size & centering ──
        win_w, win_h = 520, 780
        scr_w = self.winfo_screenwidth()
        scr_h = self.winfo_screenheight()
        x = (scr_w - win_w) // 2
        y = (scr_h - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")

        # ── Load cat images (2 sizes for bounce animation) ──
        self.cat_images = {}
        self.cat_images_small = {}
        self._load_cat_images()

        # ── Style ──
        self._setup_styles()

        # ── Timer State ──
        self.timer_running = False
        self.timer_paused = False
        self.timer_total_seconds = 0
        self.timer_remaining = 0
        self.timer_job = None
        self._ring_anim_fraction = 0.0  # for smooth ring interpolation

        # ── Alarm State ──
        self.alarms = []
        self.alarm_counter = 0
        self.alarm_check_running = True

        # ── Cat animation state ──
        self._cat_bob_phase = 0
        self._cat_current_state = "sleeping"
        self._cat_pulse_job = None

        # ── Build UI ──
        self._build_header()
        self._build_notebook()

        # ── Start background threads / loops ──
        self.alarm_thread = threading.Thread(target=self._alarm_checker, daemon=True)
        self.alarm_thread.start()
        self._update_clock()
        self._animate_cat_idle()
        self._animate_header_glow()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── Load Images ─────────────────────────────────────────────────────────
    def _load_cat_images(self):
        sizes = {"normal": (150, 150), "small": (140, 140)}
        for key, fname in [("sleeping", "cat_sleeping.png"),
                           ("alert", "cat_alert.png"),
                           ("celebrate", "cat_celebrate.png")]:
            path = resource_path(fname)
            try:
                img = Image.open(path).convert("RGBA")
                img_n = img.resize(sizes["normal"], Image.LANCZOS)
                img_s = img.resize(sizes["small"], Image.LANCZOS)
                self.cat_images[key] = ImageTk.PhotoImage(img_n)
                self.cat_images_small[key] = ImageTk.PhotoImage(img_s)
            except Exception:
                self.cat_images[key] = None
                self.cat_images_small[key] = None

    # ─── Styles ──────────────────────────────────────────────────────────────
    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Pink.TNotebook", background=PINK_PALE, borderwidth=0)
        style.configure("Pink.TNotebook.Tab",
                        background=PINK_LIGHT, foreground=DARK_TEXT,
                        padding=[22, 10], font=("Helvetica Neue", 13, "bold"))
        style.map("Pink.TNotebook.Tab",
                  background=[("selected", PINK_MAIN)],
                  foreground=[("selected", WHITE)])

        style.configure("Pink.TFrame", background=PINK_PALE)

    # ─── Header with animated glow ───────────────────────────────────────────
    def _build_header(self):
        self.header_frame = tk.Frame(self, bg=PINK_PALE)
        self.header_frame.pack(fill="x", pady=(18, 4))

        self.header_label = tk.Label(self.header_frame,
                                     text="🐱  Kitty Timer & Alarm",
                                     font=("Helvetica Neue", 22, "bold"),
                                     fg=PINK_DARK, bg=PINK_PALE)
        self.header_label.pack()

        self.sub_label = tk.Label(self.header_frame,
                                  text="Your purrfect time companion  ✨",
                                  font=("Helvetica Neue", 11), fg=PINK_TEXT, bg=PINK_PALE)
        self.sub_label.pack()

    def _animate_header_glow(self):
        """Subtle color cycling on the header text."""
        phase = (time.time() * 0.5) % 1.0
        # Oscillate between PINK_DARK and PINK_ACCENT
        t = (math.sin(phase * 2 * math.pi) + 1) / 2
        color = lerp_color(PINK_DARK, PINK_ACCENT, t * 0.4)
        self.header_label.config(fg=color)
        self.after(50, self._animate_header_glow)

    # ─── Notebook (Tabs) ─────────────────────────────────────────────────────
    def _build_notebook(self):
        self.notebook = ttk.Notebook(self, style="Pink.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=18, pady=(10, 18))

        self.timer_frame = ttk.Frame(self.notebook, style="Pink.TFrame")
        self.notebook.add(self.timer_frame, text="  ⏱  Timer  ")
        self._build_timer_tab()

        self.alarm_frame = ttk.Frame(self.notebook, style="Pink.TFrame")
        self.notebook.add(self.alarm_frame, text="  ⏰  Alarm  ")
        self._build_alarm_tab()

    # ═══════════════════════════════════════════════════════════════════════════
    #  TIMER TAB
    # ═══════════════════════════════════════════════════════════════════════════
    def _build_timer_tab(self):
        parent = self.timer_frame

        # ── Cat mascot on canvas (for animation) ──
        self.timer_cat_canvas = tk.Canvas(parent, width=160, height=170,
                                          bg=PINK_PALE, highlightthickness=0)
        self.timer_cat_canvas.pack(pady=(10, 0))

        self.timer_cat_text = tk.Label(parent, text="zzZ... Set a timer, I'll wake up!",
                                       font=("Helvetica Neue", 11, "italic"),
                                       fg=PINK_TEXT, bg=PINK_PALE)
        self.timer_cat_text.pack(pady=(0, 4))

        # ── Circular progress + time display (canvas) ──
        self.timer_canvas = tk.Canvas(parent, width=230, height=230,
                                      bg=PINK_PALE, highlightthickness=0)
        self.timer_canvas.pack(pady=(4, 8))
        self._draw_timer_ring(0)

        # ── Input row ──
        input_frame = tk.Frame(parent, bg=PINK_PALE)
        input_frame.pack(pady=(4, 6))

        for col, (label_text, var_name) in enumerate([("Hrs", "timer_h"),
                                                       ("Min", "timer_m"),
                                                       ("Sec", "timer_s")]):
            sub = tk.Frame(input_frame, bg=PINK_PALE)
            sub.grid(row=0, column=col, padx=10)
            tk.Label(sub, text=label_text, font=("Helvetica Neue", 10, "bold"),
                     fg=PINK_TEXT, bg=PINK_PALE).pack()
            var = tk.StringVar(value="0")
            setattr(self, var_name, var)
            sb = tk.Spinbox(sub, from_=0, to=59 if var_name != "timer_h" else 99,
                            textvariable=var, width=4, font=("Helvetica Neue", 18),
                            justify="center", wrap=True,
                            bg=WHITE, fg=DARK_TEXT, buttonbackground=PINK_LIGHT,
                            relief="flat", bd=2, highlightbackground=PINK_LIGHT,
                            highlightcolor=PINK_MAIN)
            sb.pack()

        # ── Animated Buttons ──
        btn_frame = tk.Frame(parent, bg=PINK_PALE)
        btn_frame.pack(pady=(8, 10))

        self.start_btn = AnimatedButton(btn_frame, "▶  Start",
                                        self._timer_start, PINK_MAIN, width=120, height=42)
        self.start_btn.grid(row=0, column=0, padx=6)

        self.pause_btn = AnimatedButton(btn_frame, "⏸  Pause",
                                        self._timer_pause, PINK_LIGHT,
                                        fg_color=DARK_TEXT, width=120, height=42)
        self.pause_btn.grid(row=0, column=1, padx=6)
        self.pause_btn.set_disabled(True)

        self.reset_btn = AnimatedButton(btn_frame, "↺  Reset",
                                        self._timer_reset, PINK_LIGHT,
                                        fg_color=DARK_TEXT, width=120, height=42)
        self.reset_btn.grid(row=0, column=2, padx=6)
        self.reset_btn.set_disabled(True)

    # ── Draw progress ring with glow ─────────────────────────────────────────
    def _draw_timer_ring(self, fraction):
        c = self.timer_canvas
        c.delete("all")
        cx, cy, r = 115, 115, 95

        # Outer glow
        for i in range(3):
            glow_r = r + 8 + i * 4
            glow_alpha = 0.08 - i * 0.025
            glow_color = lerp_color(PINK_PALE, PINK_LIGHT, glow_alpha * 5)
            c.create_arc(cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r,
                         outline=glow_color, width=2, style="arc",
                         start=0, extent=359.9)

        # Background ring
        c.create_arc(cx - r, cy - r, cx + r, cy + r,
                     outline=PINK_LIGHT, width=14, style="arc",
                     start=0, extent=359.9)

        # Progress arc with gradient effect
        if fraction > 0:
            extent = -359.9 * fraction
            # Multiple thin arcs for gradient feel
            for i in range(3):
                offset = i * 0.5
                shade = lerp_color(PINK_MAIN, PINK_ACCENT, i / 3)
                c.create_arc(cx - r, cy - r, cx + r, cy + r,
                             outline=shade, width=14 - i * 2, style="arc",
                             start=90, extent=extent)

            # Glowing tip dot
            angle_rad = math.radians(90 + 360 * fraction)
            dot_x = cx - r * math.cos(angle_rad)
            dot_y = cy - r * math.sin(angle_rad)
            # Glow behind dot
            for glow_i in range(3):
                gr = 12 - glow_i * 2
                gc = lerp_color(PINK_ACCENT, PINK_PALE, glow_i * 0.3)
                c.create_oval(dot_x - gr, dot_y - gr, dot_x + gr, dot_y + gr,
                              fill=gc, outline="")
            # Dot itself
            c.create_oval(dot_x - 7, dot_y - 7, dot_x + 7, dot_y + 7,
                          fill=WHITE, outline=PINK_ACCENT, width=2)

        # Centre text
        remaining = self.timer_remaining if hasattr(self, 'timer_remaining') else 0
        mins, secs = divmod(remaining, 60)
        hrs, mins = divmod(mins, 60)
        time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
        c.create_text(cx, cy - 8, text=time_str,
                      font=("Helvetica Neue", 30, "bold"), fill=PINK_DARK)

        # Status text under time
        if self.timer_running:
            status = "counting down..."
        elif self.timer_paused:
            status = "paused"
        elif remaining == 0 and self.timer_total_seconds > 0:
            status = "✨ done! ✨"
        else:
            status = "ready"
        c.create_text(cx, cy + 22, text=status,
                      font=("Helvetica Neue", 10), fill=PINK_TEXT)

    # ── Smooth ring animation (interpolate between frames) ───────────────────
    def _animate_ring_to(self, target_fraction, callback=None):
        """Smoothly animate the ring from current to target fraction."""
        start = self._ring_anim_fraction
        diff = target_fraction - start
        duration = 800  # ms
        steps = max(1, duration // 16)
        step = [0]

        def tick():
            if step[0] > steps:
                self._ring_anim_fraction = target_fraction
                self._draw_timer_ring(target_fraction)
                if callback:
                    callback()
                return
            t = ease_in_out_cubic(step[0] / steps)
            current = start + diff * t
            self._ring_anim_fraction = current
            self._draw_timer_ring(current)
            step[0] += 1
            self.after(16, tick)

        tick()

    # ── Timer controls ───────────────────────────────────────────────────────
    def _timer_start(self):
        if self.timer_paused:
            self.timer_paused = False
            self.timer_running = True
            self.pause_btn.set_text("⏸  Pause")
            self._timer_tick()
            self._set_cat_state("alert")
            self._animate_text(self.timer_cat_text, "Counting down... stay focused! ᓚᘏᗢ")
            return

        try:
            h = int(self.timer_h.get())
            m = int(self.timer_m.get())
            s = int(self.timer_s.get())
        except ValueError:
            return

        total = h * 3600 + m * 60 + s
        if total <= 0:
            return

        self.timer_total_seconds = total
        self.timer_remaining = total
        self.timer_running = True
        self.timer_paused = False
        self._ring_anim_fraction = 0.0

        self.start_btn.set_disabled(True)
        self.pause_btn.set_disabled(False)
        self.reset_btn.set_disabled(False)

        self._set_cat_state("alert")
        self._animate_text(self.timer_cat_text, "Counting down... stay focused! ᓚᘏᗢ")
        self._timer_tick()

    def _timer_tick(self):
        if not self.timer_running:
            return
        if self.timer_remaining <= 0:
            self._timer_complete()
            return

        fraction = 1 - (self.timer_remaining / self.timer_total_seconds)
        self._ring_anim_fraction = fraction
        self._draw_timer_ring(fraction)
        self.timer_remaining -= 1
        self.timer_job = self.after(1000, self._timer_tick)

    def _timer_complete(self):
        self.timer_running = False
        # Smooth ring fill to 100%
        self._animate_ring_to(1.0)
        self._set_cat_state("celebrate")
        self._animate_text(self.timer_cat_text, "✨ Time's up! Great job! ✨")
        self.start_btn.set_disabled(False)
        self.pause_btn.set_disabled(True)

        # Play sound
        for i in range(3):
            self.after(i * 800, play_alert_sound)

        # Sparkle explosion!
        self.after(200, lambda: SparkleOverlay(self.timer_canvas, 115, 115).start())
        self.after(600, lambda: SparkleOverlay(self.timer_canvas, 115, 115).start())

        # Flash effect
        self._flash_timer(0)

    def _flash_timer(self, count):
        if count >= 6:
            self.timer_canvas.configure(bg=PINK_PALE)
            return
        color = WHITE if count % 2 == 0 else PINK_PALE
        self.timer_canvas.configure(bg=color)
        self.after(250, self._flash_timer, count + 1)

    def _timer_pause(self):
        if self.timer_running and not self.timer_paused:
            self.timer_running = False
            self.timer_paused = True
            if self.timer_job:
                self.after_cancel(self.timer_job)
            self.pause_btn.set_text("▶  Resume")
            self.start_btn.set_disabled(False)
            self._animate_text(self.timer_cat_text, "Paused... take a break 😽")
        elif self.timer_paused:
            self._timer_start()

    def _timer_reset(self):
        self.timer_running = False
        self.timer_paused = False
        if self.timer_job:
            self.after_cancel(self.timer_job)
        self.timer_remaining = 0
        self.timer_total_seconds = 0
        # Smooth ring collapse
        self._animate_ring_to(0.0)
        self.start_btn.set_disabled(False)
        self.pause_btn.set_disabled(True)
        self.pause_btn.set_text("⏸  Pause")
        self.reset_btn.set_disabled(True)
        self._set_cat_state("sleeping")
        self._animate_text(self.timer_cat_text, "zzZ... Set a timer, I'll wake up!")

    # ═══════════════════════════════════════════════════════════════════════════
    #  ALARM TAB
    # ═══════════════════════════════════════════════════════════════════════════
    def _build_alarm_tab(self):
        parent = self.alarm_frame

        # ── Cat mascot on canvas ──
        self.alarm_cat_canvas = tk.Canvas(parent, width=160, height=170,
                                          bg=PINK_PALE, highlightthickness=0)
        self.alarm_cat_canvas.pack(pady=(10, 0))

        self.alarm_cat_text = tk.Label(parent, text="Set an alarm and I'll meow! 🐾",
                                       font=("Helvetica Neue", 11, "italic"),
                                       fg=PINK_TEXT, bg=PINK_PALE)
        self.alarm_cat_text.pack(pady=(0, 6))

        # ── Current time display ──
        clock_card = tk.Frame(parent, bg=WHITE, bd=0, highlightbackground=PINK_LIGHT,
                              highlightthickness=2)
        clock_card.pack(pady=(4, 10), padx=30, fill="x")

        tk.Label(clock_card, text="Current Time", font=("Helvetica Neue", 10, "bold"),
                 fg=GRAY_TEXT, bg=WHITE).pack(pady=(8, 0))
        self.clock_label = tk.Label(clock_card, text="--:--:-- --",
                                    font=("Helvetica Neue", 36, "bold"),
                                    fg=PINK_DARK, bg=WHITE)
        self.clock_label.pack(pady=(0, 8))

        # ── Set alarm row ──
        set_frame = tk.Frame(parent, bg=PINK_PALE)
        set_frame.pack(pady=(6, 4))

        tk.Label(set_frame, text="Set Alarm:", font=("Helvetica Neue", 12, "bold"),
                 fg=DARK_TEXT, bg=PINK_PALE).grid(row=0, column=0, padx=(0, 8))

        self.alarm_h = tk.StringVar(value="12")
        self.alarm_m = tk.StringVar(value="00")
        self.alarm_period = tk.StringVar(value="AM")

        h_sb = tk.Spinbox(set_frame, from_=1, to=12, textvariable=self.alarm_h,
                          width=3, font=("Helvetica Neue", 16), justify="center",
                          wrap=True, bg=WHITE, fg=DARK_TEXT, buttonbackground=PINK_LIGHT,
                          relief="flat", bd=2, highlightbackground=PINK_LIGHT,
                          highlightcolor=PINK_MAIN)
        h_sb.grid(row=0, column=1, padx=2)

        tk.Label(set_frame, text=":", font=("Helvetica Neue", 16, "bold"),
                 fg=DARK_TEXT, bg=PINK_PALE).grid(row=0, column=2)

        m_sb = tk.Spinbox(set_frame, from_=0, to=59, textvariable=self.alarm_m,
                          width=3, font=("Helvetica Neue", 16), justify="center",
                          wrap=True, format="%02.0f",
                          bg=WHITE, fg=DARK_TEXT, buttonbackground=PINK_LIGHT,
                          relief="flat", bd=2, highlightbackground=PINK_LIGHT,
                          highlightcolor=PINK_MAIN)
        m_sb.grid(row=0, column=3, padx=2)

        # AM / PM animated toggle
        self.period_btn = AnimatedButton(set_frame, "AM", self._toggle_period,
                                         PINK_MAIN, width=60, height=36)
        self.period_btn.grid(row=0, column=4, padx=(8, 0))

        # Set alarm button
        set_btn_frame = tk.Frame(parent, bg=PINK_PALE)
        set_btn_frame.pack(pady=(6, 6))
        set_alarm_btn = AnimatedButton(set_btn_frame, "🔔  Set Alarm",
                                       self._add_alarm, PINK_MAIN, width=160, height=42)
        set_alarm_btn.pack()

        # ── Alarm list ──
        tk.Label(parent, text="🔔  Active Alarms",
                 font=("Helvetica Neue", 12, "bold"),
                 fg=DARK_TEXT, bg=PINK_PALE).pack(pady=(6, 2))

        list_container = tk.Frame(parent, bg=PINK_PALE)
        list_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.alarm_canvas_list = tk.Canvas(list_container, bg=PINK_PALE,
                                           highlightthickness=0, height=140)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical",
                                  command=self.alarm_canvas_list.yview)
        self.alarm_list_frame = tk.Frame(self.alarm_canvas_list, bg=PINK_PALE)

        self.alarm_list_frame.bind("<Configure>",
            lambda e: self.alarm_canvas_list.configure(
                scrollregion=self.alarm_canvas_list.bbox("all")))
        self.alarm_canvas_list.create_window((0, 0), window=self.alarm_list_frame, anchor="nw")
        self.alarm_canvas_list.configure(yscrollcommand=scrollbar.set)

        self.alarm_canvas_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._no_alarm_label = tk.Label(self.alarm_list_frame,
                                         text="No alarms set yet 😴",
                                         font=("Helvetica Neue", 11, "italic"),
                                         fg=GRAY_TEXT, bg=PINK_PALE)
        self._no_alarm_label.pack(pady=20)

    def _toggle_period(self):
        if self.alarm_period.get() == "AM":
            self.alarm_period.set("PM")
            self.period_btn.set_text("PM")
        else:
            self.alarm_period.set("AM")
            self.period_btn.set_text("AM")

    def _add_alarm(self):
        try:
            h = int(self.alarm_h.get())
            m = int(self.alarm_m.get())
        except ValueError:
            return
        if h < 1 or h > 12 or m < 0 or m > 59:
            return

        period = self.alarm_period.get()
        time_str = f"{h:02d}:{m:02d} {period}"

        for a in self.alarms:
            if a["time"] == time_str:
                messagebox.showinfo("Kitty says...", f"Alarm for {time_str} already exists! 😺")
                return

        self.alarm_counter += 1
        alarm = {"time": time_str, "id": self.alarm_counter, "h": h, "m": m, "period": period}
        self.alarms.append(alarm)

        self._no_alarm_label.pack_forget()
        self._render_alarm_item(alarm)

        self._set_cat_state("alert", target="alarm")
        self._animate_text(self.alarm_cat_text, f"Alarm set for {time_str}! I'll meow! 🐾")

    def _render_alarm_item(self, alarm):
        """Create an alarm card with slide-in animation."""
        card = tk.Frame(self.alarm_list_frame, bg=WHITE, bd=0,
                        highlightbackground=PINK_LIGHT, highlightthickness=2)
        card.pack(fill="x", pady=3, padx=4)
        card.alarm_id = alarm["id"]

        tk.Label(card, text=f"⏰  {alarm['time']}",
                 font=("Helvetica Neue", 14, "bold"),
                 fg=DARK_TEXT, bg=WHITE).pack(side="left", padx=(12, 0), pady=8)

        # Animated delete button
        del_canvas = tk.Canvas(card, width=30, height=30, bg=WHITE, highlightthickness=0)
        del_canvas.pack(side="right", padx=(0, 8), pady=6)
        del_canvas.create_text(15, 15, text="✕", font=("Helvetica Neue", 14, "bold"),
                               fill=PINK_DARK)

        def on_del_enter(e):
            del_canvas.delete("all")
            del_canvas.create_oval(2, 2, 28, 28, fill=PINK_LIGHT, outline="")
            del_canvas.create_text(15, 15, text="✕", font=("Helvetica Neue", 14, "bold"),
                                   fill=PINK_ACCENT)

        def on_del_leave(e):
            del_canvas.delete("all")
            del_canvas.create_text(15, 15, text="✕", font=("Helvetica Neue", 14, "bold"),
                                   fill=PINK_DARK)

        del_canvas.bind("<Enter>", on_del_enter)
        del_canvas.bind("<Leave>", on_del_leave)
        del_canvas.bind("<Button-1>",
                        lambda e, aid=alarm["id"], w=card: self._delete_alarm(aid, w))
        del_canvas.config(cursor="hand2")

        # Slide-in animation (fade from right)
        self._slide_in_widget(card)

    def _slide_in_widget(self, widget):
        """Animate widget sliding in from right with opacity-like effect."""
        # We simulate by briefly highlighting the background
        steps = [0]
        total = 8

        def tick():
            if steps[0] > total:
                widget.config(highlightbackground=PINK_LIGHT)
                return
            t = steps[0] / total
            color = lerp_color(PINK_ACCENT, PINK_LIGHT, ease_in_out_cubic(t))
            widget.config(highlightbackground=color, highlightthickness=2)
            steps[0] += 1
            self.after(30, tick)

        widget.config(highlightbackground=PINK_ACCENT, highlightthickness=3)
        self.after(30, tick)

    def _delete_alarm(self, alarm_id, widget):
        # Fade-out animation
        self._fade_out_widget(widget, lambda: self._remove_alarm(alarm_id, widget))

    def _fade_out_widget(self, widget, callback):
        """Shrink/fade animation before removing."""
        steps = [0]
        total = 6

        def tick():
            if steps[0] > total:
                callback()
                return
            t = steps[0] / total
            color = lerp_color(WHITE, PINK_PALE, ease_in_out_cubic(t))
            try:
                widget.config(bg=color, highlightthickness=max(0, int(2 * (1 - t))))
                for child in widget.winfo_children():
                    try:
                        child.config(bg=color)
                    except Exception:
                        pass
            except Exception:
                pass
            steps[0] += 1
            self.after(25, tick)

        tick()

    def _remove_alarm(self, alarm_id, widget):
        self.alarms = [a for a in self.alarms if a["id"] != alarm_id]
        widget.destroy()
        if not self.alarms:
            self._no_alarm_label.pack(pady=20)
            self._set_cat_state("sleeping", target="alarm")
            self._animate_text(self.alarm_cat_text, "Set an alarm and I'll meow! 🐾")

    # ── Alarm checker (background thread) ────────────────────────────────────
    def _alarm_checker(self):
        triggered = set()
        while self.alarm_check_running:
            now = time.localtime()
            current_h = now.tm_hour
            current_m = now.tm_min
            current_s = now.tm_sec

            for alarm in self.alarms[:]:
                ah = alarm["h"]
                if alarm["period"] == "AM":
                    if ah == 12:
                        ah = 0
                else:
                    if ah != 12:
                        ah += 12

                key = f"{alarm['id']}_{ah}_{alarm['m']}"
                if current_h == ah and current_m == alarm["m"] and current_s < 2:
                    if key not in triggered:
                        triggered.add(key)
                        self.after(0, self._alarm_triggered, alarm)
                else:
                    triggered.discard(key)

            time.sleep(0.5)

    def _alarm_triggered(self, alarm):
        self._set_cat_state("celebrate", target="alarm")
        self._animate_text(self.alarm_cat_text, f"🔔 MEOW! It's {alarm['time']}! 🔔")

        for i in range(5):
            self.after(i * 600, play_alert_sound)

        self._flash_clock(0)

        self.after(500, lambda: messagebox.showinfo(
            "🐱 Kitty Alarm!",
            f"⏰ It's {alarm['time']}!\n\nMEOW MEOW MEOW! 🐾\nTime to get up!"
        ))

        self.after(600, lambda: self._set_cat_state("alert", target="alarm"))
        self.after(600, lambda: self._animate_text(
            self.alarm_cat_text,
            f"{len(self.alarms)} alarm(s) active 🐾" if self.alarms else "Set an alarm! 🐾"))

    def _flash_clock(self, count):
        if count >= 8:
            self.clock_label.configure(fg=PINK_DARK)
            return
        color = PINK_ACCENT if count % 2 == 0 else PINK_DARK
        self.clock_label.configure(fg=color)
        self.after(200, self._flash_clock, count + 1)

    # ── Live clock with smooth colon blink ───────────────────────────────────
    def _update_clock(self):
        now = time.strftime("%I:%M:%S %p")
        self.clock_label.config(text=now)
        self.after(500, self._update_clock)

    # ═══════════════════════════════════════════════════════════════════════════
    #  CAT MASCOT ANIMATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    def _set_cat_state(self, state, target="timer"):
        """Change cat state with a bounce transition."""
        self._cat_current_state = state
        canvas = self.timer_cat_canvas if target == "timer" else self.alarm_cat_canvas
        self._bounce_cat(canvas, state)

    def _bounce_cat(self, canvas, state, step=0, total=15):
        """Bounce/scale animation when cat changes state."""
        if step > total:
            # Final draw at normal size
            self._draw_cat_on_canvas(canvas, state, offset_y=0, use_small=False)
            return

        t = step / total
        # Elastic-style bounce
        scale = ease_out_elastic(t)
        # Translate scale to y-offset (bounce up then settle)
        offset_y = -15 * (1 - scale)
        use_small = t < 0.3

        self._draw_cat_on_canvas(canvas, state, offset_y=offset_y, use_small=use_small)
        self.after(25, self._bounce_cat, canvas, state, step + 1, total)

    def _draw_cat_on_canvas(self, canvas, state, offset_y=0, use_small=False):
        """Draw the cat image on the given canvas."""
        canvas.delete("all")
        img_dict = self.cat_images_small if use_small else self.cat_images
        img = img_dict.get(state)
        if img:
            canvas.create_image(80, 85 + offset_y, image=img, anchor="center")
        else:
            fallback = {"sleeping": "😴🐱", "alert": "😺🐱", "celebrate": "🎉🐱✨"}
            canvas.create_text(80, 85 + offset_y, text=fallback.get(state, "🐱"),
                               font=("Helvetica Neue", 40))

    def _animate_cat_idle(self):
        """Subtle bobbing animation for the cat when idle."""
        self._cat_bob_phase += 0.08
        offset_y = math.sin(self._cat_bob_phase) * 4  # gentle 4px bob

        # Only animate idle cats (sleeping or alert, not mid-bounce)
        for canvas, target in [(self.timer_cat_canvas, "timer"),
                               (self.alarm_cat_canvas, "alarm")]:
            state = self._cat_current_state
            img = self.cat_images.get(state)
            if img:
                canvas.delete("all")
                canvas.create_image(80, 85 + offset_y, image=img, anchor="center")

                # Add floating "zzZ" particles for sleeping state
                if state == "sleeping":
                    z_phase = (self._cat_bob_phase * 2) % (2 * math.pi)
                    for i, char in enumerate(["z", "Z", "z"]):
                        zx = 130 + i * 10 + math.sin(z_phase + i) * 5
                        zy = 40 - i * 14 + math.cos(z_phase + i * 0.5) * 3
                        alpha_t = (math.sin(z_phase + i * 1.2) + 1) / 2
                        color = lerp_color(PINK_LIGHT, PINK_ACCENT, alpha_t * 0.5)
                        canvas.create_text(zx, zy, text=char,
                                           font=("Helvetica Neue", 10 + i * 2, "bold"),
                                           fill=color)

                # Add sparkle particles for celebrate state
                if state == "celebrate":
                    for i in range(5):
                        sx = random.randint(10, 150)
                        sy = random.randint(10, 150)
                        ss = random.randint(2, 5)
                        sc = random.choice(["#FFD700", "#FF69B4", "#FF1493", "#FFC0CB"])
                        canvas.create_oval(sx - ss, sy - ss, sx + ss, sy + ss,
                                           fill=sc, outline="")

        self.after(50, self._animate_cat_idle)

    # ═══════════════════════════════════════════════════════════════════════════
    #  TEXT ANIMATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    def _animate_text(self, label, new_text):
        """Typewriter-style text reveal with color fade."""
        label.config(text="")
        step = [0]
        total = len(new_text)

        def tick():
            if step[0] > total:
                label.config(fg=PINK_TEXT)
                return
            displayed = new_text[:step[0]]
            label.config(text=displayed)
            # Color transition during typing
            t = step[0] / max(total, 1)
            color = lerp_color(PINK_ACCENT, PINK_TEXT, ease_in_out_cubic(t))
            label.config(fg=color)
            step[0] += 1
            speed = max(15, 40 - total)  # faster for longer texts
            self.after(speed, tick)

        tick()

    # ═══════════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════════════════════
    def _on_close(self):
        self.alarm_check_running = False
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
#  Entry Point
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = KittyTimerApp()
    app.mainloop()
