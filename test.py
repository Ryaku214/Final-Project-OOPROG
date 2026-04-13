import pygame

pygame.init()

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 600)) 
        pygame.display.set_caption("FINAL APOCALYPSE")  
        self.clock = pygame.time.Clock() 
        self.running = True 

        self.background_image = pygame.image.load("bg apo.jpg").convert()
        self.background_image = pygame.transform.scale(self.background_image, (800, 600))

    def draw_text(self, text, font_size, color, x, y):
        font = pygame.font.SysFont(None, font_size)
        img = font.render(text, True, color)
        self.screen.blit(img, (x, y))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
 
            self.screen.blit(self.background_image, (0, 0))

            self.draw_text("Welcome to the Final Apocalypse!", 40, (255, 255, 255), 150, 250)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


game = Game()
game.run()
