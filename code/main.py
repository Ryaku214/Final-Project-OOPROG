import pygame
import random
import sys

# --- Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
TILE_SIZE = 48
FPS = 60

# Colors
GREEN = (34, 139, 34)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
GOLD = (255, 215, 0)
GRAY = (50, 50, 50)
DARK_BLUE = (20, 20, 80)


class Entity:
    def __init__(self, name, pos, dialogue, sprite_index=0, is_enemy=False, hp=0):
        self.name = name
        self.pos = list(pos)
        self.dialogue = dialogue
        self.is_enemy = is_enemy
        self.sprite_index = sprite_index
        self.hp = hp
        self.max_hp = hp
        self.alive = True
        self.rect = pygame.Rect(pos[0], pos[1], TILE_SIZE, TILE_SIZE)

    def reset(self):
        self.hp = self.max_hp
        self.alive = True


def load_sprite_sheet(filename, frame_width, frame_height):
    try:
        sheet = pygame.image.load(filename).convert_alpha()
        sprites = []
        for y in range(0, sheet.get_height(), frame_height):
            for x in range(0, sheet.get_width(), frame_width):
                rect = pygame.Rect(x, y, frame_width, frame_height)
                image = pygame.Surface(rect.size, pygame.SRCALPHA)
                image.blit(sheet, (0, 0), rect)
                sprites.append(image)
        return sprites
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Post-Apoc RPG")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier", 20, bold=True)
        self.small_font = pygame.font.SysFont("Courier", 16)

        # Background loading
        self.bg_explore = self.load_background("background grass(not finished).png")
        self.bg_battle = self.load_background("forest(background during fight).png")

        # Sprite sheets
        self.player_sprites = load_sprite_sheet("player_sheet.png", 64, 64)
        self.enemy_sprites = load_sprite_sheet("enemy_sheet.png", 32, 32)

        # World entities - always created
        self.world_entities = [
            Entity("Old Scavenger", [150, 150], 
                   ["Welcome to the wasteland, stranger.",
                    "The mutants have taken over the eastern woods.",
                    "Be careful out there... and check the shop for Lucky Coins!"],
                   sprite_index=0),
            Entity("Wounded Traveler", [400, 450],
                   ["*cough* They got me good...",
                    "There's a boss mutant deeper in. Watch yourself."],
                   sprite_index=0),
            Entity("Feral Mutant", [300, 250], 
                   ["GRAAAH! FRESH MEAT!"], 
                   sprite_index=0, is_enemy=True, hp=80),
            Entity("Mutant Brute", [550, 200], 
                   ["You dare enter my territory?!", 
                    "I'll crush your bones!"], 
                   sprite_index=1, is_enemy=True, hp=120),
            Entity("Mutant Boss", [650, 400], 
                   ["Finally... a worthy challenger.",
                    "Let's see what you're made of, human!"], 
                   sprite_index=1, is_enemy=True, hp=200)
        ]

        # Game state
        self.state = "EXPLORE"
        self.turn = "PLAYER"
        self.current_target = None
        self.dialogue_index = 0

        # Player stats
        self.player_pos = [100, 300]
        self.player_hp = 100
        self.player_max_hp = 100
        self.ult_meter = 0
        self.scrap = 0
        self.victories = 0

        # Battle state
        self.enemy_in_battle = None
        self.battle_log = ""

        # Ultimate minigame
        self.cursor_x = 200
        self.cursor_speed = 8
        self.target_zone = (480, 520)

    def load_background(self, filename):
        try:
            raw = pygame.image.load(filename).convert()
            return pygame.transform.scale(raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            print(f"Background '{filename}' not found, using solid color.")
            return None

    def draw_explore(self):
        if self.bg_explore:
            self.screen.blit(self.bg_explore, (0, 0))
        else:
            self.screen.fill(GREEN)

        # Draw entities
        for ent in self.world_entities:
            if not ent.alive:
                continue
            if self.enemy_sprites and ent.sprite_index < len(self.enemy_sprites):
                self.screen.blit(self.enemy_sprites[ent.sprite_index], ent.pos)
            else:
                color = RED if ent.is_enemy else DARK_BLUE
                pygame.draw.rect(self.screen, color, ent.rect)
            # Draw name above entity
            name_surf = self.small_font.render(ent.name, True, WHITE)
            self.screen.blit(name_surf, (ent.pos[0] - 10, ent.pos[1] - 20))

        # Draw player
        if self.player_sprites:
            self.screen.blit(self.player_sprites[0], self.player_pos)
        else:
            pygame.draw.rect(self.screen, WHITE, 
                           (self.player_pos[0], self.player_pos[1], TILE_SIZE, TILE_SIZE))

        # HUD
        self.draw_hud()

        # Instructions
        inst = self.small_font.render("WASD: Move | E: Interact | ESC: Quit", True, WHITE)
        self.screen.blit(inst, (10, SCREEN_HEIGHT - 25))

    def draw_hud(self):
        # Player stats in corner
        pygame.draw.rect(self.screen, (0, 0, 0, 180), (10, 10, 180, 70))
        pygame.draw.rect(self.screen, WHITE, (10, 10, 180, 70), 2)
        self.screen.blit(self.font.render(f"HP: {self.player_hp}/{self.player_max_hp}", True, WHITE), (20, 15))
        self.screen.blit(self.font.render(f"Scrap: {self.scrap}", True, GOLD), (20, 40))

    def draw_dialogue(self):
        self.draw_explore()
        if not self.current_target:
            return

        # Dialogue box
        pygame.draw.rect(self.screen, DARK_BLUE, (25, 400, 750, 180))
        pygame.draw.rect(self.screen, WHITE, (25, 400, 750, 180), 3)

        # Speaker name
        name_surf = self.font.render(self.current_target.name, True, GOLD)
        self.screen.blit(name_surf, (50, 415))

        # Dialogue text
        if self.dialogue_index < len(self.current_target.dialogue):
            text = self.current_target.dialogue[self.dialogue_index]
            # Word wrap
            words = text.split(' ')
            lines = []
            current_line = ""
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

        # Prompt
        if self.dialogue_index < len(self.current_target.dialogue) - 1:
            prompt = "[E] Continue"
        elif self.current_target.is_enemy:
            prompt = "[E] Fight!"
        else:
            prompt = "[E] Close"
        self.screen.blit(self.font.render(prompt, True, GOLD), (50, 550))

    def draw_battle(self):
        if self.bg_battle:
            self.screen.blit(self.bg_battle, (0, 0))
        else:
            self.screen.fill(BLACK)

        # Draw combatants
        if self.player_sprites:
            self.screen.blit(self.player_sprites[0], (100, 280))
        else:
            pygame.draw.rect(self.screen, WHITE, (100, 280, 64, 64))

        if self.enemy_sprites and self.enemy_in_battle:
            idx = self.enemy_in_battle.sprite_index
            if idx < len(self.enemy_sprites):
                en_img = pygame.transform.scale(self.enemy_sprites[idx], (96, 96))
                self.screen.blit(en_img, (580, 250))
        else:
            pygame.draw.rect(self.screen, RED, (580, 250, 96, 96))

        # HP bars
        # Player
        pygame.draw.rect(self.screen, GRAY, (50, 50, 200, 20))
        hp_width = int((self.player_hp / self.player_max_hp) * 200)
        pygame.draw.rect(self.screen, RED, (50, 50, hp_width, 20))
        pygame.draw.rect(self.screen, WHITE, (50, 50, 200, 20), 2)
        self.screen.blit(self.font.render(f"YOU: {self.player_hp}/{self.player_max_hp}", True, WHITE), (50, 75))

        # Ult meter
        pygame.draw.rect(self.screen, GRAY, (50, 100, 100, 15))
        ult_width = self.ult_meter
        pygame.draw.rect(self.screen, GOLD, (50, 100, ult_width, 15))
        pygame.draw.rect(self.screen, WHITE, (50, 100, 100, 15), 2)
        self.screen.blit(self.small_font.render(f"ULT: {self.ult_meter}%", True, GOLD), (50, 118))

        # Enemy
        if self.enemy_in_battle:
            pygame.draw.rect(self.screen, GRAY, (550, 50, 200, 20))
            enemy_hp_width = int((self.enemy_in_battle.hp / self.enemy_in_battle.max_hp) * 200)
            pygame.draw.rect(self.screen, RED, (550, 50, max(0, enemy_hp_width), 20))
            pygame.draw.rect(self.screen, WHITE, (550, 50, 200, 20), 2)
            self.screen.blit(self.font.render(
                f"{self.enemy_in_battle.name}: {self.enemy_in_battle.hp}", True, WHITE), (550, 75))

        # Battle log
        pygame.draw.rect(self.screen, GRAY, (50, 380, 700, 50))
        pygame.draw.rect(self.screen, WHITE, (50, 380, 700, 50), 2)
        self.screen.blit(self.font.render(self.battle_log, True, GOLD), (60, 395))

        # Menu
        if self.turn == "PLAYER" and self.state == "BATTLE":
            pygame.draw.rect(self.screen, DARK_BLUE, (50, 440, 700, 140))
            pygame.draw.rect(self.screen, WHITE, (50, 440, 700, 140), 2)

            menu_options = [
                ("1: Scrapshot", "Multi-hit (1-4 hits × 6 dmg)", WHITE),
                ("2: Heavy Slug", "High damage, 60% accuracy", WHITE),
                ("3: Chem-Buff", "Heal 15 HP, +35% Ult", WHITE),
                ("4: ULTIMATE", "Nuclear Strike (100% Ult req)", GOLD if self.ult_meter >= 100 else GRAY)
            ]
            for i, (name, desc, color) in enumerate(menu_options):
                x = 70 + (i % 2) * 340
                y = 460 + (i // 2) * 50
                self.screen.blit(self.font.render(name, True, color), (x, y))
                self.screen.blit(self.small_font.render(desc, True, GRAY), (x, y + 22))

    def draw_ultimate_minigame(self):
        self.draw_battle()

        # Minigame bar
        pygame.draw.rect(self.screen, GRAY, (200, 200, 400, 40))
        pygame.draw.rect(self.screen, WHITE, (200, 200, 400, 40), 2)

        # Target zone (gold)
        pygame.draw.rect(self.screen, GOLD, (self.target_zone[0], 200, 40, 40))

        # Cursor
        pygame.draw.rect(self.screen, WHITE, (self.cursor_x, 195, 5, 50))

        # Instructions
        inst = self.font.render("Press SPACE in the gold zone!", True, WHITE)
        self.screen.blit(inst, (250, 250))

    def check_interaction(self):
        p_rect = pygame.Rect(self.player_pos[0], self.player_pos[1], TILE_SIZE, TILE_SIZE)
        for ent in self.world_entities:
            if not ent.alive:
                continue
            if p_rect.inflate(40, 40).colliderect(ent.rect):
                self.current_target = ent
                self.dialogue_index = 0
                self.state = "DIALOGUE"
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
                self.state = "EXPLORE"
                self.current_target = None

    def start_battle(self, enemy):
        self.state = "BATTLE"
        self.turn = "PLAYER"
        self.enemy_in_battle = enemy
        self.battle_log = f"A wild {enemy.name} attacks!"

    def enemy_turn(self):
        if not self.enemy_in_battle or self.enemy_in_battle.hp <= 0:
            return

        pygame.display.flip()
        pygame.time.delay(800)

        damage = random.randint(8, 20)
        self.player_hp -= damage
        self.battle_log = f"{self.enemy_in_battle.name} attacks for {damage} damage!"
        self.turn = "PLAYER"

        if self.player_hp <= 0:
            self.player_hp = 0
            self.battle_log = "You were defeated..."
            pygame.display.flip()
            pygame.time.delay(2000)
            self.game_over()

    def game_over(self):
        # Reset player
        self.player_hp = self.player_max_hp
        self.player_pos = [100, 300]
        self.ult_meter = 0
        self.state = "EXPLORE"
        self.enemy_in_battle = None
        # Enemies respawn
        for ent in self.world_entities:
            if ent.is_enemy:
                ent.reset()

    def handle_player_move(self, key):
        if self.turn != "PLAYER" or not self.enemy_in_battle:
            return

        dmg = 0
        acted = False

        if key == pygame.K_1:
            hits = random.randint(1, 4)
            dmg = hits * 6
            self.battle_log = f"Scrapshot hits {hits} time(s) for {dmg} damage!"
            acted = True

        elif key == pygame.K_2:
            if random.random() < 0.6:
                dmg = 40
                self.battle_log = "DIRECT HIT! Heavy Slug deals 40 damage!"
            else:
                self.battle_log = "Heavy Slug missed!"
            acted = True

        elif key == pygame.K_3:
            self.player_hp = min(self.player_max_hp, self.player_hp + 15)
            self.ult_meter = min(100, self.ult_meter + 35)
            self.battle_log = "Injected Chems! HP +15, Ult rising!"
            acted = True

        elif key == pygame.K_4:
            if self.ult_meter >= 100:
                self.state = "BATTLE_ULT"
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

    def victory(self):
        self.enemy_in_battle.hp = 0
        self.enemy_in_battle.alive = False
        scrap_gain = random.randint(20, 50)
        self.scrap += scrap_gain
        self.victories += 1
        self.battle_log = f"Victory! Gained {scrap_gain} scrap."

        pygame.display.flip()
        pygame.time.delay(1500)

        self.state = "EXPLORE"
        self.enemy_in_battle = None
        self.current_target = None

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    if self.state == "EXPLORE":
                        if event.key == pygame.K_e:
                            self.check_interaction()

                    elif self.state == "DIALOGUE":
                        if event.key == pygame.K_e:
                            self.advance_dialogue()

                    elif self.state == "BATTLE":
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
                            self.state = "BATTLE"
                            if self.enemy_in_battle.hp <= 0:
                                self.victory()
                            else:
                                self.turn = "ENEMY"

            # Movement
            if self.state == "EXPLORE":
                keys = pygame.key.get_pressed()
                speed = 4
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    self.player_pos[0] = max(0, self.player_pos[0] - speed)
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    self.player_pos[0] = min(SCREEN_WIDTH - TILE_SIZE, self.player_pos[0] + speed)
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    self.player_pos[1] = max(0, self.player_pos[1] - speed)
                if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    self.player_pos[1] = min(SCREEN_HEIGHT - TILE_SIZE, self.player_pos[1] + speed)

            # Enemy turn
            if self.state == "BATTLE" and self.turn == "ENEMY":
                self.enemy_turn()

            # Ultimate cursor movement
            if self.state == "BATTLE_ULT":
                self.cursor_x += self.cursor_speed
                if self.cursor_x > 600 or self.cursor_x < 200:
                    self.cursor_speed *= -1

            # Render
            if self.state == "EXPLORE":
                self.draw_explore()
            elif self.state == "DIALOGUE":
                self.draw_dialogue()
            elif self.state == "BATTLE":
                self.draw_battle()
            elif self.state == "BATTLE_ULT":
                self.draw_ultimate_minigame()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
