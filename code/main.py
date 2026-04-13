import pygame
import sys

pygame.init()

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 600)) 
        pygame.display.set_caption("FINAL APOCALYPSE")  
        self.clock = pygame.time.Clock() 
        self.running = True 
        # State can be 'MENU' or 'PLAY'
        self.state = "MENU"

        # --- BACKGROUND LOADING ---
        try:
            # Ensure "s.png" exists in your folder
            self.background_image = pygame.image.load("s.png").convert()
            self.background_image = pygame.transform.scale(self.background_image, (800, 600))
        except:
            print("Warning: Image not found. Using solid color fallback.")
            self.background_image = pygame.Surface((800, 600))
            self.background_image.fill((50, 0, 0)) 

    def draw_text(self, text, font_size, color, x, y):
        # Using a standard font since get_font wasn't defined
        font = pygame.font.SysFont("Arial", font_size)
        img = font.render(text, True, color)
        # Center logic if needed: 
        rect = img.get_rect(center=(x, y))
        self.screen.blit(img, rect)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.state == "MENU":
                    # Simple click detection for a "Start" button area
                    if 300 < mouse_pos[0] < 500 and 250 < mouse_pos[1] < 350:
                        self.state = "PLAY"
                elif self.state == "PLAY":
                    # Simple click detection for "Back" button area
                    if 350 < mouse_pos[0] < 450 and 440 < mouse_pos[1] < 480:
                        self.state = "MENU"

    def run(self):
        while self.running:
            self.handle_events()

            if self.state == "MENU":
                self.screen.blit(self.background_image, (0, 0))
                self.draw_text("FINAL APOCALYPSE", 60, (255, 255, 255), 400, 150)
                self.draw_text("CLICK HERE TO START", 30, (200, 200, 200), 400, 300)

            elif self.state == "PLAY":
                self.screen.fill((255, 255, 255))
                self.draw_text("WELCOME.", 45, (0, 0, 0), 400, 260)
                
                # Back Button visual
                self.draw_text("BACK", 40, (255, 0, 0), 400, 460)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
