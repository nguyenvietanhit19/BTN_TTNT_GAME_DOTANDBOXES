# main.py
"""
Điểm khởi chạy game Dots and Boxes.
Chạy: python main.py
"""
import sys
import pygame

from config      import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE
from ui.screens  import ScreenManager


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock  = pygame.time.Clock()

    manager = ScreenManager()

    while True:
        dt = clock.tick(FPS) / 1000.0  # delta time (giây)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            manager.handle_event(event)

        manager.update(dt)
        manager.draw(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
