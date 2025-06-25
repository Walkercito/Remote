import math
import pygame
from typing import Tuple



class Player:
    def __init__(self, x_pos: int, y_pos: int, size: int, color: Tuple[int, int, int] = (255, 0, 0), gametag: str = "Player"):
        self.x_pos = float(x_pos)
        self.y_pos = float(y_pos)
        self.size = size
        self.color = color
        self.speed = 300 
        self.gametag = gametag
        self.font = pygame.font.SysFont(None, 24)


    def update(self, keys, delta_time: float):
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1

        if dx != 0 or dy != 0:
            magnitude = math.hypot(dx, dy)  # √(dx² + dy²)
            dx /= magnitude
            dy /= magnitude

            self.x_pos += dx * self.speed * delta_time
            self.y_pos += dy * self.speed * delta_time


    def render(self, screen: pygame.Surface):
        pygame.draw.rect(
            screen,
            self.color,
            (int(self.x_pos), int(self.y_pos), self.size, self.size)
        )

        text_surface: pygame.Surface = self.font.render(self.gametag, True, (0, 0, 0))
        text_rect: pygame.Rect = text_surface.get_rect(
            center = (self.x_pos + self.size / 2 , self.y_pos - 10)
        )
        screen.blit(text_surface, text_rect)