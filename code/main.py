import pygame
import random
import sys

# --- Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
TILE_SIZE = 48
FPS = 60

# Colors
GREEN      = (34, 139, 34)
WHITE      = (255, 255, 255)
BLACK      = (0, 0, 0)
RED        = (200, 0, 0)
DARK_RED   = (120, 0, 0)
GOLD       = (255, 215, 0)
GRAY       = (80, 80, 80)
LIGHT_GRAY = (160, 160, 160)
DARK_BLUE  = (20, 20, 80)
TEAL       = (0, 180, 160)
PURPLE     = (120, 0, 180)
HEAL_GREEN = (0, 200, 80)


# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------
class Entity:
    def __init__(self, name, pos, dialogue, sprite_index=0, is_enemy=False,
                 hp=0, accuracy=1.0, is_boss=False):
        self.name         = name
        self.pos          = list(pos)
        self.dialogue     = dialogue
        self.is_enemy     = is_enemy
        self.sprite_index = sprite_index
        self.hp           = hp
        self.max_hp       = hp
        self.alive        = True
        self.accuracy     = accuracy   # 0.0 – 1.0 hit chance
        self.is_boss      = is_boss
        self.rect         = pygame.Rect(pos[0], pos[1], TILE_SIZE, TILE_SIZE)

    def reset(self):
        self.hp    = self.max_hp
        self.alive = True


# ---------------------------------------------------------------------------
# Sprite sheet helper
# ---------------------------------------------------------------------------
def load_sprite_sheet(filename, frame_width, frame_height):
    try:
        sheet   = pygame.image.load(filename).convert_alpha()
        sprites = []
        for y in range(0, sheet.get_height(), frame_height):
            for x in range(0, sheet.get_width(), frame_width):
                rect  = pygame.Rect(x, y, frame_width, frame_height)
                image = pygame.Surface(rect.size, pygame.SRCALPHA)
                image.blit(sheet, (0, 0), rect)
                sprites.append(image)
        return sprites
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


# ---------------------------------------------------------------------------
# Main Game Class
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Post-Apoc RPG")
        self.clock      = pygame.time.Clock()
        self.font       = pygame.font.SysFont("Courier", 20, bold=True)
        self.small_font = pygame.font.SysFont("Courier", 16)
        self.big_font   = pygame.font.SysFont("Courier", 42, bold=True)
        self.title_font = pygame.font.SysFont("Courier", 56, bold=True)

        # Backgrounds
        self.bg_explore = self.load_background("background grass(not finished).png")
        self.bg_battle  = self.load_background("forest(background during fight).png")
        self.bg_menu    = self.load_background("menu_background.png")   # optional

        # Sprite sheets
        self.player_sprites = load_sprite_sheet("player_sheet.png", 64, 64)
        self.enemy_sprites  = load_sprite_sheet("enemy_sheet.png",  32, 32)

        # Menu state
        self.menu_selected = 0                       # 0 = New Game, 1 = Quit
        self.menu_options  = ["NEW GAME", "QUIT"]

        # World entities
        self.world_entities = [
            Entity("Old Scavenger", [150, 150],
                   ["Welcome to the wasteland, stranger.",
                    "The mutants have taken over the eastern woods.",
                    "Be careful out there... and check your skills!"],
                   sprite_index=0),
            Entity("Wounded Traveler", [400, 450],
                   ["*cough* They got me good...",
                    "There's a boss mutant deeper in. Watch yourself."],
                   sprite_index=0),
            Entity("Feral Mutant",  [300, 250],
                   ["GRAAAH! FRESH MEAT!"],
                   sprite_index=0, is_enemy=True, hp=80,  accuracy=0.75),
            Entity("Mutant Brute",  [550, 200],
                   ["You dare enter my territory?!", "I'll crush your bones!"],
                   sprite_index=1, is_enemy=True, hp=120, accuracy=0.65),
            Entity("Mutant Boss",   [650, 400],
                   ["Finally... a worthy challenger.",
                    "Let's see what you're made of, human!"],
                   sprite_index=1, is_enemy=True, hp=200, accuracy=0.85,
                   is_boss=True),
        ]

        self._init_game_state()

    # -----------------------------------------------------------------------
    # State initialisation (called on New Game and Game Over)
    # -----------------------------------------------------------------------
    def _init_game_state(self):
        self.state          = "MENU"
        self.turn           = "PLAYER"
        self.current_target = None
        self.dialogue_index = 0

        # Player stats
        self.player_pos     = [100, 300]
        self.player_hp      = 100
        self.player_max_hp  = 100
        self.ult_meter      = 0
        self.scrap          = 0
        self.victories      = 0

        # Battle state
        self.enemy_in_battle = None
        self.battle_log      = ""

        # Ultimate mini-game
        self.cursor_x      = 200
        self.cursor_speed  = 8
        self.target_zone   = (480, 520)

        # Coin-flip mini-game state
        self.coin_flip_active  = False
        self.coin_flip_result  = None     # "HEADS" | "TAILS"
        self.coin_flip_timer   = 0        # frames to display result
        self.coin_flip_pending_dmg = 0

        # Heal flash
        self.heal_flash_timer = 0

        # Boss victory screen
        self.boss_win_timer = 0           # counts down after boss is slain

        # Reset enemies
        for ent in self.world_entities:
            if ent.is_enemy:
                ent.reset()

    # -----------------------------------------------------------------------
    # Utilities
    # -----------------------------------------------------------------------
    def load_background(self, filename):
        try:
            raw = pygame.image.load(filename).convert()
            return pygame.transform.scale(raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            print(f"Background '{filename}' not found, using solid color.")
            return None

    def draw_text_centered(self, surface, text, font, color, cx, cy):
        surf = font.render(text, True, color)
        surface.blit(surf, (cx - surf.get_width() // 2, cy - surf.get_height() // 2))

    def draw_panel(self, x, y, w, h, fill=DARK_BLUE, border=WHITE, border_w=2):
        pygame.draw.rect(self.screen, fill,   (x, y, w, h))
        pygame.draw.rect(self.screen, border, (x, y, w, h), border_w)

    # -----------------------------------------------------------------------
    # MENU
    # -----------------------------------------------------------------------
    def draw_menu(self):
        if self.bg_menu:
            self.screen.blit(self.bg_menu, (0, 0))
        else:
            self.screen.fill((10, 10, 30))

        # Title
        self.draw_text_centered(self.screen, "POST-APOC RPG",
                                self.title_font, GOLD,
                                SCREEN_WIDTH // 2, 140)
        self.draw_text_centered(self.screen, "Survive the Wasteland",
                                self.font, LIGHT_GRAY,
                                SCREEN_WIDTH // 2, 205)

        # Options
        for i, opt in enumerate(self.menu_options):
            y       = 310 + i * 70
            is_sel  = (i == self.menu_selected)
            box_col = GOLD if is_sel else GRAY
            txt_col = BLACK if is_sel else WHITE
            fill    = GOLD if is_sel else (30, 30, 60)
            pygame.draw.rect(self.screen, fill,    (280, y - 22, 240, 48))
            pygame.draw.rect(self.screen, box_col, (280, y - 22, 240, 48), 3)
            self.draw_text_centered(self.screen, opt, self.font, txt_col,
                                    SCREEN_WIDTH // 2, y + 2)

        # Controls hint
        self.draw_text_centered(self.screen,
                                "W/S or UP/DOWN: Navigate   ENTER: Select",
                                self.small_font, LIGHT_GRAY,
                                SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30)

    def handle_menu_input(self, key):
        if key in (pygame.K_w, pygame.K_UP):
            self.menu_selected = (self.menu_selected - 1) % len(self.menu_options)
        elif key in (pygame.K_s, pygame.K_DOWN):
            self.menu_selected = (self.menu_selected + 1) % len(self.menu_options)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
            if self.menu_selected == 0:
                self._init_game_state()
                self.state = "EXPLORE"
            elif self.menu_selected == 1:
                pygame.quit()
                sys.exit()

    # -----------------------------------------------------------------------
    # EXPLORE
    # -----------------------------------------------------------------------
    def draw_explore(self):
        if self.bg_explore:
            self.screen.blit(self.bg_explore, (0, 0))
        else:
            self.screen.fill(GREEN)

        for ent in self.world_entities:
            if not ent.alive:
                continue
            if self.enemy_sprites and ent.sprite_index < len(self.enemy_sprites):
                self.screen.blit(self.enemy_sprites[ent.sprite_index], ent.pos)
            else:
                color = RED if ent.is_enemy else DARK_BLUE
                pygame.draw.rect(self.screen, color, ent.rect)
            name_surf = self.small_font.render(ent.name, True, WHITE)
            self.screen.blit(name_surf, (ent.pos[0] - 10, ent.pos[1] - 20))

        if self.player_sprites:
            self.screen.blit(self.player_sprites[0], self.player_pos)
        else:
            pygame.draw.rect(self.screen, WHITE,
                             (self.player_pos[0], self.player_pos[1], TILE_SIZE, TILE_SIZE))

        self.draw_hud()
        inst = self.small_font.render(
            "WASD: Move  |  E: Interact  |  ESC: Menu", True, WHITE)
        self.screen.blit(inst, (10, SCREEN_HEIGHT - 25))

    def draw_hud(self):
        self.draw_panel(10, 10, 200, 70)
        self.screen.blit(
            self.font.render(f"HP: {self.player_hp}/{self.player_max_hp}", True, WHITE),
            (20, 15))
        self.screen.blit(
            self.font.render(f"Scrap: {self.scrap}", True, GOLD),
            (20, 40))

    # -----------------------------------------------------------------------
    # DIALOGUE
    # -----------------------------------------------------------------------
    def draw_dialogue(self):
        self.draw_explore()
        if not self.current_target:
            return

        self.draw_panel(25, 400, 750, 180)
        name_surf = self.font.render(self.current_target.name, True, GOLD)
        self.screen.blit(name_surf, (50, 415))

        if self.dialogue_index < len(self.current_target.dialogue):
            text  = self.current_target.dialogue[self.dialogue_index]
            words = text.split(' ')
            lines, current_line = [], ""
            for word in words:
                test = current_line + word + " "
                if self.font.size(test)[0] < 700:
                    current_line = test
                else:
                    lines.append(current_line)
                    current_line = word + " "
            lines.append(current_line)
            for i, line in enumerate(lines):
                self.screen.blit(self.font.render(line, True, WHITE), (50, 450 + i * 25))

        if self.dialogue_index < len(self.current_target.dialogue) - 1:
            prompt = "[E] Continue"
        elif self.current_target.is_enemy:
            prompt = "[E] Fight!"
        else:
            prompt = "[E] Close"
        self.screen.blit(self.font.render(prompt, True, GOLD), (50, 550))

    # -----------------------------------------------------------------------
    # BATTLE
    # -----------------------------------------------------------------------
    def draw_battle(self):
        if self.bg_battle:
            self.screen.blit(self.bg_battle, (0, 0))
        else:
            self.screen.fill(BLACK)

        # Player sprite
        if self.player_sprites:
            self.screen.blit(self.player_sprites[0], (100, 280))
        else:
            pygame.draw.rect(self.screen, WHITE, (100, 280, 64, 64))

        # Enemy sprite
        if self.enemy_sprites and self.enemy_in_battle:
            idx    = self.enemy_in_battle.sprite_index
            if idx < len(self.enemy_sprites):
                en_img = pygame.transform.scale(self.enemy_sprites[idx], (96, 96))
                self.screen.blit(en_img, (580, 250))
        else:
            pygame.draw.rect(self.screen, RED, (580, 250, 96, 96))

        # --- HP bars ---
        # Player
        pygame.draw.rect(self.screen, GRAY, (50, 50, 200, 20))
        hp_w = int((self.player_hp / self.player_max_hp) * 200)
        bar_color = HEAL_GREEN if self.heal_flash_timer > 0 else RED
        pygame.draw.rect(self.screen, bar_color, (50, 50, hp_w, 20))
        pygame.draw.rect(self.screen, WHITE, (50, 50, 200, 20), 2)
        self.screen.blit(
            self.font.render(f"YOU: {self.player_hp}/{self.player_max_hp}", True, WHITE),
            (50, 75))

        # Ult meter
        pygame.draw.rect(self.screen, GRAY,   (50, 100, 100, 15))
        pygame.draw.rect(self.screen, GOLD,   (50, 100, self.ult_meter, 15))
        pygame.draw.rect(self.screen, WHITE,  (50, 100, 100, 15), 2)
        self.screen.blit(
            self.small_font.render(f"ULT: {self.ult_meter}%", True, GOLD),
            (50, 118))

        # Enemy
        if self.enemy_in_battle:
            pygame.draw.rect(self.screen, GRAY,  (550, 50, 200, 20))
            e_w = int((self.enemy_in_battle.hp / self.enemy_in_battle.max_hp) * 200)
            pygame.draw.rect(self.screen, DARK_RED, (550, 50, max(0, e_w), 20))
            pygame.draw.rect(self.screen, WHITE, (550, 50, 200, 20), 2)
            self.screen.blit(
                self.font.render(
                    f"{self.enemy_in_battle.name}: {self.enemy_in_battle.hp}",
                    True, WHITE),
                (550, 75))

        # Battle log
        self.draw_panel(50, 375, 700, 55, fill=GRAY)
        self.screen.blit(
            self.font.render(self.battle_log, True, GOLD),
            (60, 393))

        # Coin flip overlay (shown during resolution pause)
        if self.coin_flip_active:
            self._draw_coin_flip_overlay()

        # Skill menu
        if self.turn == "PLAYER" and self.state == "BATTLE" and not self.coin_flip_active:
            self._draw_battle_menu()

    def _draw_battle_menu(self):
        self.draw_panel(50, 440, 700, 145)
        self.screen.blit(
            self.font.render("─── ACTIONS ───", True, GOLD), (55, 448))

        menu_options = [
            ("1: Lucky Shot",
             "Coin flip! HEADS=double dmg, TAILS=half", TEAL),
            ("2: Heavy Slug",
             "High damage, 60% accuracy", WHITE),
            ("3: Chem-Buff",
             "Heal 25 HP, +35% Ult", HEAL_GREEN),
            ("4: ULTIMATE",
             "Nuclear Strike (100% Ult req)",
             GOLD if self.ult_meter >= 100 else LIGHT_GRAY),
        ]
        for i, (name, desc, color) in enumerate(menu_options):
            x = 70  + (i % 2) * 345
            y = 468 + (i // 2) * 55
            self.screen.blit(self.font.render(name, True, color),         (x, y))
            self.screen.blit(self.small_font.render(desc, True, LIGHT_GRAY), (x, y + 22))

    def _draw_coin_flip_overlay(self):
        """Semi-transparent overlay showing the coin flip result."""
        overlay = pygame.Surface((320, 160), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (240, 210))
        pygame.draw.rect(self.screen, GOLD, (240, 210, 320, 160), 3)

        title = self.font.render("── COIN FLIP ──", True, GOLD)
        self.screen.blit(title, (400 - title.get_width() // 2, 225))

        if self.coin_flip_result == "HEADS":
            result_color = GOLD
            result_text  = "HEADS!"
            sub_text     = "DOUBLE DAMAGE!"
        else:
            result_color = RED
            result_text  = "TAILS..."
            sub_text     = "Half damage..."

        res  = self.big_font.render(result_text,  True, result_color)
        sub  = self.font.render   (sub_text,       True, WHITE)
        dmg  = self.font.render   (f"Deals: {self.coin_flip_pending_dmg} dmg", True, WHITE)
        cx   = 400
        self.screen.blit(res, (cx - res.get_width() // 2, 258))
        self.screen.blit(sub, (cx - sub.get_width() // 2, 308))
        self.screen.blit(dmg, (cx - dmg.get_width() // 2, 333))

    # -----------------------------------------------------------------------
    # ULTIMATE mini-game
    # -----------------------------------------------------------------------
    def draw_ultimate_minigame(self):
        self.draw_battle()

        self.draw_panel(190, 190, 420, 90, fill=(10, 10, 40))
        # Bar
        pygame.draw.rect(self.screen, GRAY, (200, 210, 400, 40))
        pygame.draw.rect(self.screen, WHITE, (200, 210, 400, 40), 2)
        # Target zone
        pygame.draw.rect(self.screen, GOLD,
                         (self.target_zone[0], 210,
                          self.target_zone[1] - self.target_zone[0], 40))
        # Cursor
        pygame.draw.rect(self.screen, WHITE, (self.cursor_x, 205, 5, 50))
        # Instruction
        inst = self.font.render("Press SPACE inside the GOLD zone!", True, WHITE)
        self.screen.blit(inst, (400 - inst.get_width() // 2, 260))

    # -----------------------------------------------------------------------
    # BOSS WIN SCREEN
    # -----------------------------------------------------------------------
    def draw_boss_win(self):
        self.screen.fill((5, 5, 20))

        # Animated gold shimmer (alpha pulse using timer)
        pulse = abs((self.boss_win_timer % 60) - 30) / 30.0   # 0.0 → 1.0
        shimmer = (
            int(180 + 75 * pulse),
            int(140 + 75 * pulse),
            0,
        )

        # Trophy / crown art (simple ASCII-style drawn with text)
        crown_lines = [
            r"  * * * * *  ",
            r" *|* * * *|* ",
            r"  \       /  ",
            r"   |     |   ",
            r"   |     |   ",
            r"   +-----+   ",
        ]
        for i, line in enumerate(crown_lines):
            surf = self.font.render(line, True, shimmer)
            self.screen.blit(surf, (400 - surf.get_width() // 2, 80 + i * 26))

        # Main congratulations text
        self.draw_text_centered(
            self.screen,
            "CONGRATULATIONS!",
            self.title_font, GOLD,
            SCREEN_WIDTH // 2, 270,
        )
        self.draw_text_centered(
            self.screen,
            "You defeated the Mutant Boss!",
            self.big_font, WHITE,
            SCREEN_WIDTH // 2, 330,
        )

        # Stats summary
        stat_lines = [
            f"Victories : {self.victories}",
            f"Scrap collected : {self.scrap}",
            f"HP remaining : {self.player_hp} / {self.player_max_hp}",
        ]
        for i, line in enumerate(stat_lines):
            self.draw_text_centered(
                self.screen, line, self.font, LIGHT_GRAY,
                SCREEN_WIDTH // 2, 390 + i * 30,
            )

        # Prompt (blink every second)
        if (self.boss_win_timer // 40) % 2 == 0:
            self.draw_text_centered(
                self.screen,
                "Press ENTER to return to the Main Menu",
                self.font, GOLD,
                SCREEN_WIDTH // 2, 510,
            )

    # -----------------------------------------------------------------------
    # Interaction / Dialogue
    # -----------------------------------------------------------------------
    def check_interaction(self):
        p_rect = pygame.Rect(self.player_pos[0], self.player_pos[1], TILE_SIZE, TILE_SIZE)
        for ent in self.world_entities:
            if not ent.alive:
                continue
            if p_rect.inflate(40, 40).colliderect(ent.rect):
                self.current_target = ent
                self.dialogue_index = 0
                self.state          = "DIALOGUE"
                return

    def advance_dialogue(self):
        if not self.current_target:
            self.state = "EXPLORE"
            return
        self.dialogue_index += 1
        if self.dialogue_index >= len(self.current_target.dialogue):
            if self.current_target.is_enemy:
                self.start_battle(self.current_target)
            else:
                self.state          = "EXPLORE"
                self.current_target = None

    # -----------------------------------------------------------------------
    # Battle logic
    # -----------------------------------------------------------------------
    def start_battle(self, enemy):
        self.state           = "BATTLE"
        self.turn            = "PLAYER"
        self.enemy_in_battle = enemy
        self.battle_log      = f"A wild {enemy.name} attacks!"
        self.coin_flip_active = False

    def handle_player_move(self, key):
        if self.turn != "PLAYER" or not self.enemy_in_battle:
            return
        if self.coin_flip_active:
            return                       # ignore input during coin-flip display

        dmg   = 0
        acted = False

        # --- Skill 1: Lucky Shot (coin flip) ---
        if key == pygame.K_1:
            base_hits = random.randint(1, 4)
            base_dmg  = base_hits * 8    # slightly buffed base

            # Coin flip
            result = random.choice(["HEADS", "TAILS"])
            if result == "HEADS":
                final_dmg = base_dmg * 2
            else:
                final_dmg = max(1, base_dmg // 2)

            self.coin_flip_result      = result
            self.coin_flip_pending_dmg = final_dmg
            self.coin_flip_active      = True
            self.coin_flip_timer       = 90   # ~1.5 seconds at 60fps
            self.battle_log = (
                f"Lucky Shot – {base_hits} hit(s)! "
                f"Coin says {result}!"
            )
            # Damage is applied after the timer (in update loop)
            return

        # --- Skill 2: Heavy Slug ---
        elif key == pygame.K_2:
            if random.random() < 0.6:
                dmg = 40
                self.battle_log = "DIRECT HIT! Heavy Slug deals 40 damage!"
            else:
                self.battle_log = "Heavy Slug missed!"
            acted = True

        # --- Skill 3: Chem-Buff (FIXED) ---
        elif key == pygame.K_3:
            heal_amount     = 25                              # buffed from 15
            prev_hp         = self.player_hp
            self.player_hp  = min(self.player_max_hp, self.player_hp + heal_amount)
            actual_heal     = self.player_hp - prev_hp
            self.ult_meter  = min(100, self.ult_meter + 35)
            self.heal_flash_timer = 45                        # green bar flash
            self.battle_log = (
                f"Injected Chems! Healed +{actual_heal} HP | Ult +35%"
            )
            # End player turn explicitly (do NOT touch enemy hp)
            self.turn = "ENEMY"
            return                                            # early return

        # --- Skill 4: Ultimate ---
        elif key == pygame.K_4:
            if self.ult_meter >= 100:
                self.state    = "BATTLE_ULT"
                self.cursor_x = 200
                return
            else:
                self.battle_log = "Ultimate not ready! (Need 100%)"

        if acted:
            self.enemy_in_battle.hp -= dmg
            if dmg > 0:
                self.ult_meter = min(100, self.ult_meter + 12)
            if self.enemy_in_battle.hp <= 0:
                self.victory()
            else:
                self.turn = "ENEMY"

    def _apply_coin_flip_damage(self):
        """Called once the coin-flip display timer runs out."""
        dmg = self.coin_flip_pending_dmg
        self.enemy_in_battle.hp -= dmg
        self.ult_meter = min(100, self.ult_meter + 15)
        self.coin_flip_active = False
        if self.enemy_in_battle.hp <= 0:
            self.victory()
        else:
            self.turn = "ENEMY"

    def enemy_turn(self):
        if not self.enemy_in_battle or self.enemy_in_battle.hp <= 0:
            return

        # Redraw so the player can see the updated HP before enemy acts
        self.draw_battle()
        pygame.display.flip()
        pygame.time.delay(700)

        enemy = self.enemy_in_battle
        if random.random() < enemy.accuracy:
            damage          = random.randint(8, 20)
            self.player_hp -= damage
            self.battle_log = (
                f"{enemy.name} attacks for {damage} damage! "
                f"(ACC {int(enemy.accuracy*100)}%)"
            )
        else:
            self.battle_log = f"{enemy.name} swings wildly... and MISSES!"

        self.turn = "PLAYER"

        if self.player_hp <= 0:
            self.player_hp  = 0
            self.battle_log = "You were defeated..."
            self.draw_battle()
            pygame.display.flip()
            pygame.time.delay(2000)
            self.game_over()

    def victory(self):
        self.enemy_in_battle.hp    = 0
        self.enemy_in_battle.alive = False
        scrap_gain      = random.randint(20, 50)
        self.scrap     += scrap_gain
        self.victories += 1
        self.battle_log = f"Victory! Gained {scrap_gain} scrap."

        was_boss = self.enemy_in_battle.is_boss

        self.draw_battle()
        pygame.display.flip()
        pygame.time.delay(1500)

        if was_boss:
            self.state           = "BOSS_WIN"
            self.boss_win_timer  = 0
            self.enemy_in_battle = None
            self.current_target  = None
            self.coin_flip_active = False
        else:
            self.state           = "EXPLORE"
            self.enemy_in_battle = None
            self.current_target  = None
            self.coin_flip_active = False

    def game_over(self):
        self.player_hp      = self.player_max_hp
        self.player_pos     = [100, 300]
        self.ult_meter      = 0
        self.state          = "MENU"        # Return to menu on death
        self.menu_selected  = 0
        self.enemy_in_battle = None
        self.coin_flip_active = False
        for ent in self.world_entities:
            if ent.is_enemy:
                ent.reset()

    # -----------------------------------------------------------------------
    # Main loop
    # -----------------------------------------------------------------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)

            # ---- Events ----
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:
                        if self.state in ("EXPLORE", "BATTLE", "BATTLE_ULT"):
                            # Pause → go back to menu (soft escape)
                            self.state = "MENU"
                        elif self.state == "BOSS_WIN":
                            self._init_game_state()
                        else:
                            running = False

                    if self.state == "MENU":
                        self.handle_menu_input(event.key)

                    elif self.state == "BOSS_WIN":
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            self._init_game_state()   # back to main menu

                    elif self.state == "EXPLORE":
                        if event.key == pygame.K_e:
                            self.check_interaction()

                    elif self.state == "DIALOGUE":
                        if event.key == pygame.K_e:
                            self.advance_dialogue()

                    elif self.state == "BATTLE":
                        if not self.coin_flip_active:
                            self.handle_player_move(event.key)

                    elif self.state == "BATTLE_ULT":
                        if event.key == pygame.K_SPACE:
                            if self.target_zone[0] <= self.cursor_x <= self.target_zone[1]:
                                self.enemy_in_battle.hp -= 70
                                self.battle_log = "CRITICAL NUCLEAR STRIKE! 70 damage!"
                            else:
                                self.enemy_in_battle.hp -= 25
                                self.battle_log = "Nuclear Strike glanced... 25 damage."
                            self.ult_meter = 0
                            self.state     = "BATTLE"
                            if self.enemy_in_battle.hp <= 0:
                                self.victory()
                            else:
                                self.turn = "ENEMY"

            # ---- Per-frame updates ----

            # Movement (explore)
            if self.state == "EXPLORE":
                keys  = pygame.key.get_pressed()
                speed = 4
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    self.player_pos[0] = max(0, self.player_pos[0] - speed)
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    self.player_pos[0] = min(SCREEN_WIDTH - TILE_SIZE,
                                             self.player_pos[0] + speed)
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    self.player_pos[1] = max(0, self.player_pos[1] - speed)
                if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    self.player_pos[1] = min(SCREEN_HEIGHT - TILE_SIZE,
                                             self.player_pos[1] + speed)

            # Coin flip countdown
            if self.coin_flip_active and self.state == "BATTLE":
                self.coin_flip_timer -= 1
                if self.coin_flip_timer <= 0:
                    self._apply_coin_flip_damage()

            # Heal flash countdown
            if self.heal_flash_timer > 0:
                self.heal_flash_timer -= 1

            # Boss win timer (drives animations on the victory screen)
            if self.state == "BOSS_WIN":
                self.boss_win_timer += 1

            # Enemy turn
            if self.state == "BATTLE" and self.turn == "ENEMY" and not self.coin_flip_active:
                self.enemy_turn()

            # Ultimate cursor
            if self.state == "BATTLE_ULT":
                self.cursor_x += self.cursor_speed
                if self.cursor_x > 600 or self.cursor_x < 200:
                    self.cursor_speed *= -1

            # ---- Render ----
            if self.state == "MENU":
                self.draw_menu()
            elif self.state == "EXPLORE":
                self.draw_explore()
            elif self.state == "DIALOGUE":
                self.draw_dialogue()
            elif self.state == "BATTLE":
                self.draw_battle()
            elif self.state == "BATTLE_ULT":
                self.draw_ultimate_minigame()
            elif self.state == "BOSS_WIN":
                self.draw_boss_win()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
