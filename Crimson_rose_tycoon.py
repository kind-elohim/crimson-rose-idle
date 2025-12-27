#Import

import pygame
import sys
import time
import math
import json
import os
import random

WIDTH = 1280
HEIGHT = 720

pygame.init()
pygame.mixer.init()



screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crimson Rose Idle Tycoon")

def show_loading_screen():
    base_path = os.path.dirname(os.path.abspath(__file__))
    loading_path = os.path.join(base_path, "assets", "Image", "loading_screen.jpg")

    # Load the image
    if os.path.exists(loading_path):
        loading_img = pygame.image.load(loading_path).convert()
        loading_img = pygame.transform.scale(loading_img, (WIDTH, HEIGHT))
    else:
        loading_img = None
        print("Loading screen image not found:", loading_path)

    # Draw image or fallback
    if loading_img:
        screen.blit(loading_img, (0, 0))
    else:
        screen.fill((0, 0, 0))

    pygame.display.update()
    pygame.time.delay(2000)
show_loading_screen()


# ============================
# DISPLAY MODE MANAGER
# ============================

def set_display_mode(mode):
    global screen, WIDTH, HEIGHT

    if mode == "fullscreen":
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    elif mode == "windowed":
        screen = pygame.display.set_mode((1280, 720))  # or 1920x1080

    elif mode == "borderless":
        info = pygame.display.Info()
        screen = pygame.display.set_mode(
            (info.current_w, info.current_h),
            pygame.NOFRAME
        )

    elif mode == "minimize":
        pygame.display.iconify()
        return  # no need to update WIDTH/HEIGHT

    elif mode == "exit":
        pygame.quit()
        sys.exit()

    # Update width/height after mode change
    WIDTH, HEIGHT = screen.get_size()

SAVE_FILE = "crimson_rose_save.json"

# ========== FULLSCREEN SETUP ==========
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("CRIMSON ROSE IDLE TYCOON")
WIDTH, HEIGHT = screen.get_size()
FPS = 60

# ========== THEME SYSTEM ==========

class Theme:
    def __init__(self):
        self.bg_color = (0, 0, 0)
        self.panel_color = (10, 10, 15)
        self.text_primary = (230, 230, 240)
        self.text_secondary = (160, 160, 190)

        self.crimson = (180, 0, 40)
        self.crimson_dark = (120, 0, 25)
        self.crimson_soft = (90, 0, 20)

        self.button_color = self.crimson
        self.button_hover = (220, 40, 80)
        self.button_text = (245, 245, 255)

        self.border_color = self.crimson
        self.border_glow_color = (255, 60, 120)

        self.font_big = self._load_font("fonts/Orbitron-Regular.ttf", 36, fallback=("consolas", 36))
        self.font_med = self._load_font("fonts/Orbitron-Regular.ttf", 26, fallback=("consolas", 26))
        self.font_small = self._load_font("fonts/Orbitron-Regular.ttf", 18, fallback=("consolas", 18))

    @staticmethod
    def _load_font(path, size, fallback=("consolas", 20)):
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                pass
        return pygame.font.SysFont(fallback[0], fallback[1])

theme = Theme()






# ========== SOUND SYSTEM ==========

# Global volume (0.0 to 1.0)
VOLUME = 0.5

def load_click_sound():
    base_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_path, "assets", "audio", "retro-arcade.wav")

    if os.path.exists(path):
        try:
            snd = pygame.mixer.Sound(path)
            snd.set_volume(VOLUME)
            return snd
        except Exception as e:
            print("Error loading sound:", e)
            return None

    print("Click sound not found at:", path)
    return None


CLICK_SOUND = load_click_sound()


def play_click():
    if CLICK_SOUND:
        CLICK_SOUND.play()


# ========== VOLUME CONTROL ==========

def set_volume(value):
    """Set volume between 0.0 and 1.0"""
    global VOLUME, CLICK_SOUND
    VOLUME = max(0.0, min(1.0, value))  # clamp
    if CLICK_SOUND:
        CLICK_SOUND.set_volume(VOLUME)
    print(f"Volume set to {int(VOLUME * 100)}%")


def volume_up():
    set_volume(VOLUME + 0.1)


def volume_down():
    set_volume(VOLUME - 0.1)

# ========== EVENT IMAGE (POPUP) ==========

def load_event_image():
    base_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_path, "assets", "Image", "blackrose.jpg")

    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()

            h_target = HEIGHT // 4
            scale = h_target / img.get_height()
            w_target = int(img.get_width() * scale)

            return pygame.transform.smoothscale(img, (w_target, h_target))

        except Exception as e:
            print("Error loading event image:", e)
            return None

    else:
        print("Event image not found at:", path)
        return None


EVENT_IMAGE = load_event_image()

# ========== GAME DATA MODEL ==========

class Building:
    def __init__(self, name, base_cost, base_income, unlocked=True, unlock_tech=None):
        self.name = name
        self.base_cost = base_cost
        self.base_income = base_income
        self.amount = 0
        self.unlocked = unlocked
        self.unlock_tech = unlock_tech  # None or tech key

    @property
    def cost(self):
        return int(self.base_cost * (1.15 ** self.amount))

    @property
    def income_per_second(self):
        return self.amount * self.base_income

    def to_dict(self):
        return {
            "name": self.name,
            "base_cost": self.base_cost,
            "base_income": self.base_income,
            "amount": self.amount,
            "unlocked": self.unlocked,
            "unlock_tech": self.unlock_tech,
        }

    @staticmethod
    def from_dict(data):
        b = Building(
            data["name"],
            data["base_cost"],
            data["base_income"],
            unlocked=data.get("unlocked", True),
            unlock_tech=data.get("unlock_tech", None),
        )
        b.amount = data["amount"]
        return b


class Upgrade:
    def __init__(self, name, description, cost, multiplier_resource, multiplier_amount):
        self.name = name
        self.description = description
        self.cost = cost
        self.multiplier_resource = multiplier_resource  # "click" or "building"
        self.multiplier_amount = multiplier_amount
        self.bought = False

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "cost": self.cost,
            "multiplier_resource": self.multiplier_resource,
            "multiplier_amount": self.multiplier_amount,
            "bought": self.bought,
        }

    @staticmethod
    def from_dict(data):
        u = Upgrade(
            data["name"],
            data["description"],
            data["cost"],
            data["multiplier_resource"],
            data["multiplier_amount"],
        )
        u.bought = data["bought"]
        return u


class Tech:
    def __init__(self, key, name, description, cost_credits, cost_roses, unlocks_buildings=None):
        self.key = key
        self.name = name
        self.description = description
        self.cost_credits = cost_credits
        self.cost_roses = cost_roses
        self.unlocked = False
        self.unlocks_buildings = unlocks_buildings or []

    def to_dict(self):
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "cost_credits": self.cost_credits,
            "cost_roses": self.cost_roses,
            "unlocked": self.unlocked,
            "unlocks_buildings": self.unlocks_buildings,
        }

    @staticmethod
    def from_dict(data):
        t = Tech(
            data["key"],
            data["name"],
            data["description"],
            data["cost_credits"],
            data["cost_roses"],
            unlocks_buildings=data.get("unlocks_buildings", []),
        )
        t.unlocked = data.get("unlocked", False)
        return t


class Game:
    def __init__(self):
        self.money = 0.0
        self.money_per_click = 1.0
        self.global_income_multiplier = 1.0

        self.black_roses = 0
        self.rose_multiplier = 0.05

        self.total_earned = 0.0
        self.last_time = time.time()

        # Buildings: some locked behind tech
        self.buildings = [
            Building("Assistant", base_cost=10, base_income=0.5, unlocked=True),
            Building("Server Rack", base_cost=100, base_income=5, unlocked=True),
            Building("Data Center", base_cost=1000, base_income=40, unlocked=True),
            Building("AI Forge", base_cost=5000, base_income=200, unlocked=False, unlock_tech="ai_forge"),
            Building("Quantum Reactor", base_cost=25000, base_income=1200, unlocked=False, unlock_tech="quantum_reactor"),
            Building("Rose Harvester", base_cost=100000, base_income=5000, unlocked=False, unlock_tech="rose_harvester"),
        ]

        self.upgrades = [
            Upgrade(
                "Better Mouse",
                "Double money per click.",
                cost=50,
                multiplier_resource="click",
                multiplier_amount=2.0,
            ),
            Upgrade(
                "Automation Suite",
                "Increase building income by 50%.",
                cost=200,
                multiplier_resource="building",
                multiplier_amount=1.5,
            ),
        ]

        # Tech tree (simple)
        self.techs = {
            "ai_forge": Tech(
                "ai_forge",
                "AI Forge Protocols",
                "Unlock AI Forge (high income).",
                cost_credits=5000,
                cost_roses=0,
                unlocks_buildings=["AI Forge"],
            ),
            "quantum_reactor": Tech(
                "quantum_reactor",
                "Quantum Reactor Theory",
                "Unlock Quantum Reactor (huge income).",
                cost_credits=20000,
                cost_roses=2,
                unlocks_buildings=["Quantum Reactor"],
            ),
            "rose_harvester": Tech(
                "rose_harvester",
                "Rose Harvester Rituals",
                "Unlock Rose Harvester (massive income).",
                cost_credits=75000,
                cost_roses=5,
                unlocks_buildings=["Rose Harvester"],
            ),
        }

        self.event_cooldown = 15.0
        self.last_event_time = time.time()
        self.fullscreen = False

    # ---- ECONOMY ----

    def click(self):
        self.money += self.money_per_click
        self.total_earned += self.money_per_click

    def buy_building(self, index):
        if 0 <= index < len(self.buildings):
            b = self.buildings[index]
            if not b.unlocked:
                return
            if self.money >= b.cost:
                self.money -= b.cost
                b.amount += 1

    def buy_upgrade(self, index):
        if 0 <= index < len(self.upgrades):
            u = self.upgrades[index]
            if u.bought:
                return
            if self.money >= u.cost:
                self.money -= u.cost
                u.bought = True
                if u.multiplier_resource == "click":
                    self.money_per_click *= u.multiplier_amount
                elif u.multiplier_resource == "building":
                    self.global_income_multiplier *= u.multiplier_amount

    def buy_tech(self, key):
        tech = self.techs.get(key)
        if not tech or tech.unlocked:
            return False
        if self.money < tech.cost_credits or self.black_roses < tech.cost_roses:
            return False
        self.money -= tech.cost_credits
        self.black_roses -= tech.cost_roses
        tech.unlocked = True
        for b in self.buildings:
            if b.name in tech.unlocks_buildings:
                b.unlocked = True
        return True

    def income_per_second(self):
        base = sum(b.income_per_second for b in self.buildings if b.unlocked)
        prestige_mult = 1 + self.black_roses * self.rose_multiplier
        return base * self.global_income_multiplier * prestige_mult

    def update_income(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        inc = self.income_per_second()
        self.money += inc * dt
        self.total_earned += inc * dt

    # ---- PRESTIGE ----

    def can_prestige(self):
        return self.total_earned >= 5000

    def prestige_gain(self):
        return int(self.total_earned // 500)

    def do_prestige(self):
        gained = self.prestige_gain()
        if gained <= 0:
            return 0
        self.black_roses += gained
        self.money = 0.0
        self.money_per_click = 1.0
        self.global_income_multiplier = 1.0
        self.total_earned = 0.0
        for b in self.buildings:
            b.amount = 0
        for u in self.upgrades:
            u.bought = False
        return gained

    # ---- SAVE / LOAD ----

    def to_dict(self):
        return {
            "money": self.money,
            "money_per_click": self.money_per_click,
            "global_income_multiplier": self.global_income_multiplier,
            "black_roses": self.black_roses,
            "rose_multiplier": self.rose_multiplier,
            "total_earned": self.total_earned,
            "buildings": [b.to_dict() for b in self.buildings],
            "upgrades": [u.to_dict() for u in self.upgrades],
            "techs": {k: t.to_dict() for k, t in self.techs.items()},

            # ⭐ ADD THIS ⭐
            "display": {
                "fullscreen": self.fullscreen
            }
        }

    def save(self):
        data = self.to_dict()
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not os.path.exists(SAVE_FILE):
            return
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        self.money = data.get("money", 0.0)
        self.money_per_click = data.get("money_per_click", 1.0)
        self.global_income_multiplier = data.get("global_income_multiplier", 1.0)
        self.black_roses = data.get("black_roses", 0)
        self.rose_multiplier = data.get("rose_multiplier", 0.05)
        self.total_earned = data.get("total_earned", 0.0)

        b_list = data.get("buildings", [])
        if b_list:
            self.buildings = [Building.from_dict(d) for d in b_list]

        u_list = data.get("upgrades", [])
        if u_list:
            self.upgrades = [Upgrade.from_dict(d) for d in u_list]

        t_dict = data.get("techs", {})
        if t_dict:
            self.techs = {k: Tech.from_dict(v) for k, v in t_dict.items()}

        # Re-apply tech unlocks to buildings
        for tech in self.techs.values():
            if tech.unlocked:
                for b in self.buildings:
                    if b.name in tech.unlocks_buildings:
                        b.unlocked = True

        # ⭐ Load display settings ⭐
        self.fullscreen = data.get("display", {}).get("fullscreen", False)

    # ---- EVENTS ----

    def ready_for_event(self):
        return time.time() - self.last_event_time >= self.event_cooldown

    def mark_event(self):
        self.last_event_time = time.time()


# ========== PARTICLES ==========

class Particle:
    def __init__(self, x, y, color, lifetime, vx=0, vy=-50, size=4):
        self.x = x
        self.y = y
        self.color = color
        self.lifetime = lifetime
        self.age = 0
        self.vx = vx
        self.vy = vy
        self.size = size

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy -= 20 * dt

    def draw(self, surf):
        if self.age >= self.lifetime:
            return
        alpha = max(0, 255 * (1 - self.age / self.lifetime))
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(alpha)), (self.size, self.size), self.size)
        surf.blit(s, (self.x - self.size, self.y - self.size))

    def is_dead(self):
        return self.age >= self.lifetime


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def click_burst(self, x, y):
        for _ in range(10):
            angle = random.uniform(-math.pi / 4, math.pi / 4)
            speed = random.uniform(60, 120)
            vx = math.cos(angle) * speed
            vy = -abs(math.sin(angle) * speed)
            p = Particle(
                x, y,
                color=(255, 80, 140),
                lifetime=0.5,
                vx=vx,
                vy=vy,
                size=3
            )
            self.particles.append(p)

    def prestige_burst(self, x, y):
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 140)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            p = Particle(
                x, y,
                color=(80, 0, 0),
                lifetime=1.2,
                vx=vx,
                vy=vy,
                size=5
            )
            self.particles.append(p)

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.is_dead()]

    def draw(self, surf):
        for p in self.particles:
            p.draw(surf)


particles = ParticleSystem()

# ========== UI / VISUAL HELPERS ==========

class Button:
    def __init__(self, rect, text, callback, font=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.hovered = False
        self.font = font or theme.font_small

    def draw(self, surf, t):
        pulse = 0.5 + 0.5 * math.sin(t * 2)
        base_color = theme.button_hover if self.hovered else theme.button_color
        color = (
            min(255, int(base_color[0] + 25 * pulse)),
            min(255, int(base_color[1] + 10 * pulse)),
            min(255, int(base_color[2] + 10 * pulse)),
        )
        pygame.draw.rect(surf, color, self.rect, border_radius=10)
        border_thickness = 2 + int(1 * pulse)
        pygame.draw.rect(surf, theme.border_glow_color, self.rect, border_thickness, border_radius=10)

        label = self.font.render(self.text, True, theme.button_text)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                play_click()


def draw_vertical_gradient(surf, top_color, bottom_color):
    h = surf.get_height()
    for y in range(h):
        ratio = y / h
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        pygame.draw.line(surf, (r, g, b), (0, y), (surf.get_width(), y))


def draw_animated_panel(surf, rect, t, border_color, bg_color):
    panel_rect = pygame.Rect(rect)
    pygame.draw.rect(surf, bg_color, panel_rect, border_radius=10)
    pulse = 0.5 + 0.5 * math.sin(t * 1.5)
    glow_color = (
        min(255, int(border_color[0] + 60 * pulse)),
        min(255, int(border_color[1] + 10 * pulse)),
        min(255, int(border_color[2] + 10 * pulse)),
    )
    thickness = 2 + int(1 * pulse)
    pygame.draw.rect(surf, glow_color, panel_rect, thickness, border_radius=10)


def draw_title_bar(surf, t, game: Game):
    rect = (0, 0, WIDTH, int(HEIGHT * 0.12))
    draw_animated_panel(surf, rect, t, theme.border_color, theme.panel_color)

    title = "CRIMSON ROSE TYCOON"
    subtitle = "Build a neon empire. Harvest Black Roses."

    for offset in [(0, 0), (1, 1)]:
        title_surf = theme.font_big.render(title, True, theme.border_glow_color)
        surf.blit(title_surf, (20 + offset[0], 20 + offset[1]))

    subtitle_surf = theme.font_small.render(subtitle, True, theme.text_secondary)
    surf.blit(subtitle_surf, (22, 20 + title_surf.get_height() + 4))

    roses_text = theme.font_small.render(
        f"Black Roses: {game.black_roses}  (+{int(game.black_roses * game.rose_multiplier * 100)}% income)",
        True,
        theme.text_secondary,
    )
    surf.blit(roses_text, (WIDTH - roses_text.get_width() - 20, rect[1] + 10))


def draw_tech_panel(surf, game: Game, rect, t):
    draw_animated_panel(surf, rect, t, theme.border_color, theme.panel_color)
    x, y, w, h = rect
    title = theme.font_med.render("Tech Tree", True, theme.text_primary)
    surf.blit(title, (x + 15, y + 10))

    yy = y + 50
    for tech in game.techs.values():
        status = "[UNLOCKED]" if tech.unlocked else ""
        name = theme.font_small.render(f"{tech.name} {status}", True, theme.text_primary)
        desc = theme.font_small.render(tech.description, True, theme.text_secondary)
        cost = theme.font_small.render(
            f"Cost: ${tech.cost_credits} + {tech.cost_roses} Black Roses",
            True,
            theme.text_secondary,
        )
        surf.blit(name, (x + 15, yy))
        surf.blit(desc, (x + 15, yy + 20))
        surf.blit(cost, (x + 15, yy + 40))
        yy += 70


def draw_game_ui(surf, game: Game, buttons, t):
    draw_vertical_gradient(surf, theme.crimson_soft, theme.bg_color)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surf.blit(overlay, (0, 0))

    draw_title_bar(surf, t, game)

    top_bar_height = int(HEIGHT * 0.12)
    money_y = top_bar_height + 10

    money_text = theme.font_big.render(f"${game.money:,.1f}", True, theme.text_primary)
    surf.blit(money_text, (WIDTH // 2 - money_text.get_width() // 2, money_y))

    income = game.income_per_second()
    info_y = money_y + money_text.get_height() + 5
    income_text = theme.font_small.render(f"Income/sec: ${income:.1f}", True, theme.text_secondary)
    click_text = theme.font_small.render(f"Per click: ${game.money_per_click:.1f}", True, theme.text_secondary)
    surf.blit(income_text, (WIDTH // 2 - income_text.get_width() - 20, info_y))
    surf.blit(click_text, (WIDTH // 2 + 20, info_y))

    margin = 30
    panel_height = HEIGHT - info_y - 120
    left_width = int(WIDTH * 0.35)
    right_width = int(WIDTH * 0.3)
    tech_width = int(WIDTH * 0.25)

    left_rect = (margin, info_y + 50, left_width, panel_height)
    right_rect = (WIDTH - margin - right_width, info_y + 50, right_width, panel_height)
    tech_rect = (WIDTH // 2 - tech_width // 2, info_y + 50, tech_width, panel_height)

    draw_animated_panel(surf, left_rect, t, theme.border_color, theme.panel_color)
    draw_animated_panel(surf, right_rect, t, theme.border_color, theme.panel_color)
    draw_tech_panel(surf, game, tech_rect, t)

    lx, ly, lw, lh = left_rect
    title = theme.font_med.render("Buildings", True, theme.text_primary)
    surf.blit(title, (lx + 15, ly + 10))
    y = ly + 50
    line_spacing = 50

    for b in game.buildings:
        lock_str = "" if b.unlocked else "[LOCKED]"
        name = theme.font_small.render(f"{b.name} (x{b.amount}) {lock_str}", True, theme.text_primary)
        cost = theme.font_small.render(f"Cost: ${b.cost}", True, theme.text_secondary)
        income_line = theme.font_small.render(f"+${b.base_income}/s each", True, theme.text_secondary)

        surf.blit(name, (lx + 20, y))
        surf.blit(cost, (lx + 20, y + 20))
        surf.blit(income_line, (lx + lw // 2, y + 20))
        y += line_spacing

    rx, ry, rw, rh = right_rect
    title_u = theme.font_med.render("Upgrades", True, theme.text_primary)
    surf.blit(title_u, (rx + 15, ry + 10))
    y = ry + 50
    for u in game.upgrades:
        color = (120, 220, 160) if u.bought else theme.text_primary
        name_str = u.name + (" [BOUGHT]" if u.bought else "")
        name = theme.font_small.render(name_str, True, color)
        desc = theme.font_small.render(u.description, True, theme.text_secondary)
        cost = theme.font_small.render(f"Cost: ${u.cost}", True, theme.text_secondary)

        surf.blit(name, (rx + 20, y))
        surf.blit(desc, (rx + 20, y + 20))
        surf.blit(cost, (rx + 20, y + 40))
        y += 70

    for btn in buttons:
        btn.draw(surf, t)


# ========== POPUP EVENTS WITH CHOICES ==========

class ChoicePopup:
    def __init__(self, title, text, choice_a, choice_b, on_a, on_b, image=None):
        self.title = title
        self.text = text
        self.choice_a = choice_a
        self.choice_b = choice_b
        self.on_a = on_a
        self.on_b = on_b
        self.image = image
        self.active = True

        w = WIDTH * 0.65
        h = HEIGHT * 0.5
        self.rect = pygame.Rect(
            (WIDTH - w) // 2,
            (HEIGHT - h) // 2,
            w,
            h,
        )

        btn_w, btn_h = 190, 50
        spacing = 30
        center_y = self.rect.bottom - btn_h - 30

        self.button_a = Button(
            rect=(self.rect.centerx - btn_w - spacing // 2, center_y, btn_w, btn_h),
            text=self.choice_a,
            callback=self.choose_a,
            font=theme.font_small,
        )
        self.button_b = Button(
            rect=(self.rect.centerx + spacing // 2, center_y, btn_w, btn_h),
            text=self.choice_b,
            callback=self.choose_b,
            font=theme.font_small,
        )

    def choose_a(self):
        self.active = False
        if self.on_a:
            self.on_a()

    def choose_b(self):
        self.active = False
        if self.on_b:
            self.on_b()

    def handle_event(self, event):
        if not self.active:
            return
        self.button_a.handle_event(event)
        self.button_b.handle_event(event)

    def draw(self, surf, t):
        if not self.active:
            return

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surf.blit(overlay, (0, 0))

        draw_animated_panel(surf, self.rect, t, theme.border_color, theme.panel_color)

        title_s = theme.font_med.render(self.title, True, theme.text_primary)
        surf.blit(title_s, (self.rect.x + 20, self.rect.y + 20))

        y_text = self.rect.y + 70
        lines = self.text.split("\n")
        for line in lines:
            line_s = theme.font_small.render(line, True, theme.text_secondary)
            surf.blit(line_s, (self.rect.x + 20, y_text))
            y_text += line_s.get_height() + 5

        if self.image:
            img_rect = self.image.get_rect()
            img_rect.midright = (self.rect.right - 20, self.rect.y + self.rect.height // 2)
            surf.blit(self.image, img_rect)

        self.button_a.draw(surf, t)
        self.button_b.draw(surf, t)


class Popup:
    def __init__(self, title, text, effect_text=None, on_close=None, image=None):
        self.title = title
        self.text = text
        self.effect_text = effect_text
        self.on_close = on_close
        self.image = image
        self.active = True

        w = WIDTH * 0.6
        h = HEIGHT * 0.5
        self.rect = pygame.Rect(
            (WIDTH - w) // 2,
            (HEIGHT - h) // 2,
            w,
            h,
        )

        btn_w, btn_h = 160, 50
        self.button = Button(
            rect=(self.rect.centerx - btn_w // 2, self.rect.bottom - btn_h - 20, btn_w, btn_h),
            text="OK",
            callback=self.close,
            font=theme.font_med,
        )

    def close(self):
        self.active = False
        if self.on_close:
            self.on_close()

    def handle_event(self, event):
        if not self.active:
            return
        self.button.handle_event(event)

    def draw(self, surf, t):
        if not self.active:
            return

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surf.blit(overlay, (0, 0))

        draw_animated_panel(surf, self.rect, t, theme.border_color, theme.panel_color)

        title_s = theme.font_med.render(self.title, True, theme.text_primary)
        surf.blit(title_s, (self.rect.x + 20, self.rect.y + 20))

        y_text = self.rect.y + 70
        lines = self.text.split("\n")
        for line in lines:
            line_s = theme.font_small.render(line, True, theme.text_secondary)
            surf.blit(line_s, (self.rect.x + 20, y_text))
            y_text += line_s.get_height() + 5

        if self.effect_text:
            eff_s = theme.font_small.render(self.effect_text, True, theme.border_glow_color)
            surf.blit(eff_s, (self.rect.x + 20, y_text + 10))

        if self.image:
            img_rect = self.image.get_rect()
            img_rect.midright = (self.rect.right - 20, self.rect.y + self.rect.height // 2)
            surf.blit(self.image, img_rect)

        self.button.draw(surf, t)


def generate_random_event(game: Game):
    roll = random.random()

    # Event with choice: high-risk data heist
    if roll < 0.4:
        stolen_amount = round(random.uniform(200, 800), 1)
        fine_amount = round(random.uniform(300, 1000), 1)

        def accept():
            if random.random() < 0.6:
                game.money += stolen_amount
                game.total_earned += stolen_amount
            else:
                game.money = max(0, game.money - fine_amount)

        def decline():
            pass

        title = "DATA HEIST OFFER"
        text = (
            "A rogue netrunner offers to breach a corporate vault.\n"
            "Success: you get quick credits.\n"
            "Failure: you get traced and fined."
        )
        return ChoicePopup(
            title,
            text,
            choice_a=f"Accept (Potential +${stolen_amount})",
            choice_b="Decline (Stay safe)",
            on_a=accept,
            on_b=decline,
            image=EVENT_IMAGE,
        )

    # Event with choice: sell your data lake
    elif roll < 0.8:
        gain = round(random.uniform(100, 400), 1)
        rose_loss = random.randint(1, 2)

        def accept():
            game.money += gain
            game.total_earned += gain
            game.black_roses = max(0, game.black_roses - rose_loss)

        def decline():
            pass

        title = "CORPORATE DATA BUYOUT"
        text = (
            "A megacorp wants to buy access to your data lakes.\n"
            "They pay well, but the deal poisons your Rose network."
        )
        return ChoicePopup(
            title,
            text,
            choice_a=f"Sell (Gain ${gain}, lose {rose_loss} Roses)",
            choice_b="Refuse (Keep your roots clean)",
            on_a=accept,
            on_b=decline,
            image=EVENT_IMAGE,
        )

    # Simple positive popup
    else:
        roses = random.randint(1, 3)

        def effect():
            game.black_roses += roses

        title = "SILENT BLOOM"
        text = "In the undercity, a patch of Black Roses blooms without warning."
        effect_text = f"You gain {roses} Black Roses."
        return Popup(title, text, effect_text, on_close=effect, image=EVENT_IMAGE)


# ========== MAIN LOOP ==========

def main():
    clock = pygame.time.Clock()
    game = Game()
    game.load()

    # ⭐ Apply fullscreen setting
    if game.fullscreen:
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))


    click_button = Button(
        rect=(WIDTH // 2 - 150, HEIGHT - 100, 300, 60),
        text="COLLECT CREDITS",
        callback=lambda: (
            game.click(),
            particles.click_burst(WIDTH // 2, HEIGHT - 100 + 30)
        ),
        font=theme.font_med,
    )

    margin = 30
    top_bar_height = int(HEIGHT * 0.12)
    money_y = top_bar_height + 10
    info_y = money_y + theme.font_big.get_height() + 25
    panel_height = HEIGHT - info_y - 120
    left_width = int(WIDTH * 0.35)
    left_rect_y = info_y + 50
    line_spacing = 50

    building_buttons = []
    for i in range(len(game.buildings)):
        bx = margin + left_width - 90
        by = left_rect_y + 40 + i * line_spacing
        rect = (bx, by, 70, 30)
        btn = Button(rect, "BUY", callback=lambda idx=i: game.buy_building(idx))
        building_buttons.append(btn)

    right_width = int(WIDTH * 0.3)
    right_x = WIDTH - margin - right_width
    right_rect_y = left_rect_y
    upgrade_buttons = []
    for i in range(len(game.upgrades)):
        ux = right_x + right_width - 110
        uy = right_rect_y + 40 + i * 70
        rect = (ux, uy, 90, 30)
        btn = Button(rect, "INSTALL", callback=lambda idx=i: game.buy_upgrade(idx))
        upgrade_buttons.append(btn)

    tech_width = int(WIDTH * 0.25)
    tech_rect_x = WIDTH // 2 - tech_width // 2
    tech_rect_y = left_rect_y
    tech_buttons = []
    for idx, key in enumerate(game.techs.keys()):
        tx = tech_rect_x + tech_width - 120
        ty = tech_rect_y + 40 + idx * 70
        rect = (tx, ty, 100, 30)
        def make_cb(k=key):
            return lambda: game.buy_tech(k)
        btn = Button(rect, "UNLOCK", callback=make_cb())
        tech_buttons.append(btn)

    prestige_button = Button(
        rect=(20, HEIGHT - 80, 220, 45),
        text="ASCEND (Prestige)",
        callback=lambda: None,
        font=theme.font_small,
    )

    buttons = [click_button, prestige_button] + building_buttons + upgrade_buttons + tech_buttons

    popup = None
    running = True
    start_time = time.time()
    autosave_timer = time.time()

    def do_prestige_popup():
        nonlocal popup
        if not game.can_prestige():
            gained = game.prestige_gain()
            title = "NOT READY"
            text = "The Black Roses are not ready to bloom.\nYou need to earn more in this cycle."
            effect_text = f"Current potential roses: {gained}"
            popup = Popup(title, text, effect_text=effect_text, image=EVENT_IMAGE)
            return

        gained = game.prestige_gain()

        def effect():
            actual = game.do_prestige()
            particles.prestige_burst(WIDTH // 2, HEIGHT // 2)

        title = "ASCENSION RITUAL"
        text = (
            "You burn your current empire in crimson light.\n"
            "Its ashes feed the roots of the Black Roses."
        )
        effect_text = f"You will gain {gained} Black Roses."
        popup = Popup(title, text, effect_text=effect_text, on_close=effect, image=EVENT_IMAGE)

    prestige_button.callback = do_prestige_popup
    # Settings menu buttons
    settings_buttons = [
        Button((WIDTH // 2 - 100, HEIGHT // 2 - 120, 200, 40), "Fullscreen", lambda: set_display_mode("fullscreen")),
        Button((WIDTH // 2 - 100, HEIGHT // 2 - 70, 200, 40), "Windowed", lambda: set_display_mode("windowed")),
        Button((WIDTH // 2 - 100, HEIGHT // 2 - 20, 200, 40), "Borderless", lambda: set_display_mode("borderless")),
        Button((WIDTH // 2 - 100, HEIGHT // 2 + 30, 200, 40), "Minimize", lambda: set_display_mode("minimize")),
        Button((WIDTH // 2 - 100, HEIGHT // 2 + 80, 200, 40), "Exit Game", lambda: set_display_mode("exit")),
    ]
    settings_open = False
    gear_rect = pygame.Rect(WIDTH - 70, 10, 48, 48)

    def draw_gear_icon(surface, x, y, hover=False):
        color = (200, 200, 200) if not hover else (255, 255, 255)
        pygame.draw.circle(surface, color, (x + 24, y + 24), 20, 3)

        # Simple gear spokes
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            sx = x + 24 + math.cos(rad) * 28
            sy = y + 24 + math.sin(rad) * 28
            ex = x + 24 + math.cos(rad) * 18
            ey = y + 24 + math.sin(rad) * 18
            pygame.draw.line(surface, color, (sx, sy), (ex, ey), 3)

    while running:
        dt_ms = clock.tick(FPS)
        dt = dt_ms / 1000.0
        t = time.time() - start_time

        if not popup or not popup.active:
            game.update_income()
        particles.update(dt)

        for event in pygame.event.get():

            # Quit event
            if event.type == pygame.QUIT:
                game.save()
                running = False


            # Keyboard shortcuts
            elif event.type == pygame.KEYDOWN:

                # ⭐ Toggle fullscreen with F11 ⭐
                if event.key == pygame.K_F11:
                    game.fullscreen = not game.fullscreen

                    if game.fullscreen:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT))

                    game.save()

                # Volume Up (+ or =)
                if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    volume_up()

                # Volume Down (-)
                if event.key == pygame.K_MINUS:
                    volume_down()
                if event.key == pygame.K_ESCAPE:
                    game.save()
                    running = False

                if event.key == pygame.K_F11:
                    set_display_mode("fullscreen")
                if event.key == pygame.K_F10:
                    set_display_mode("windowed")
                if event.key == pygame.K_F9:
                    set_display_mode("borderless")
                if event.key == pygame.K_F8:
                    set_display_mode("minimize")

            # Mouse click events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                # 1. Handle gear click FIRST
                if gear_rect.collidepoint(mx, my):
                    settings_open = not settings_open
                    continue

                # 2. If settings menu is open, handle ONLY settings buttons
                if settings_open:
                    for btn in settings_buttons:
                        btn.handle_event(event)
                    continue

                # 3. Otherwise handle normal buttons
                for btn in buttons:
                    btn.handle_event(event)
            elif event.type == pygame.KEYDOWN:

                # === DISPLAY MODE SHORTCUTS ===
                if event.key == pygame.K_F11:
                    set_display_mode("fullscreen")

                if event.key == pygame.K_F10:
                    set_display_mode("windowed")

                if event.key == pygame.K_F9:
                    set_display_mode("borderless")

                if event.key == pygame.K_F8:
                    set_display_mode("minimize")
                # ===============================

                # Escape still exits your game
                if event.key == pygame.K_ESCAPE:
                    game.save()
                    running = False

            if popup and popup.active:
                popup.handle_event(event)
            else:
                for btn in buttons:
                    btn.handle_event(event)
            if settings_open:
                for btn in settings_buttons:
                    btn.handle_event(event)

        mouse_pos = pygame.mouse.get_pos()
        for btn in buttons:
            btn.hovered = btn.rect.collidepoint(mouse_pos)

        if (not popup or not popup.active) and game.ready_for_event():
            if random.random() < 0.25:
                popup = generate_random_event(game)
                game.mark_event()

        if time.time() - autosave_timer > 20:
            game.save()
            autosave_timer = time.time()

        draw_game_ui(screen, game, buttons, t)
        particles.draw(screen)

        # Draw popup if active
        if popup and popup.active:
            popup.draw(screen, t)

        # Draw gear icon (ALWAYS visible)
        mouse_pos = pygame.mouse.get_pos()
        gear_hover = gear_rect.collidepoint(mouse_pos)
        draw_gear_icon(screen, WIDTH - 60, 12, hover=gear_hover)

        # Draw settings popup (only when open)
        if settings_open:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            for btn in settings_buttons:
                btn.hovered = btn.rect.collidepoint(mouse_pos)
                btn.draw(screen, t)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()