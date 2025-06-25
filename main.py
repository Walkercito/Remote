import sys
import pygame
from config import (
    WIDTH,
    HEIGHT,
    WHITE,
    MAX_GAMETAG_LENGHT
)
from src.player import Player


class Game:
    def __init__(self, gametag: str):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Remote")
        self.clock = pygame.time.Clock()
        self.player = Player(100, 100, 50, gametag = gametag)

    
    def update(self):
        delta_time = self.clock.tick(60) / 1000
        keys = pygame.key.get_pressed()

        # Updates
        self.player.update(keys, delta_time)

        # Draw
        self.screen.fill(WHITE)
        self.player.render(self.screen)
        pygame.display.flip()


    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            self.update()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        gametag = sys.argv[1]
    else:
        gametag = str(input("Gametag: ")).strip()
        
        while len(gametag) > MAX_GAMETAG_LENGHT or len(gametag) == 0:
            print(f"Gametag must be between 1 and {MAX_GAMETAG_LENGHT} characters.")
            gametag = str(input("Gametag: ")).strip()
    
    game = Game(gametag)
    game.run()