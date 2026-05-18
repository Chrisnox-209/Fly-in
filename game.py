import pygame
import sys
from menu import Menu
from parser import parse


class SimpleGame:
    def __init__(self, map_path):
        self.map_path = map_path
        self.font = pygame.font.SysFont("arial", 80, bold=True)

    def update(self, events):
        pass

    def draw(self, screen):
        screen.fill((20, 20, 20))
        text_surf = self.font.render("GAME IN PROGRESS", True, (0, 255, 0))
        path_surf = self.font.render(f"File: {self.map_path}",
                                     True, (255, 255, 255))

        screen.blit(text_surf, (200, 200))
        screen.blit(path_surf, (200, 350))


class GameApp:
    def __init__(self):
        pygame.init()
        self.width, self.height = 2832, 1504
        self.screen = pygame.display.set_mode((self.width, self.height))

        icon = pygame.image.load("assets/icon.png").convert_alpha()
        pygame.display.set_icon(icon)

        pygame.display.set_caption("Fly_In")
        self.clock = pygame.time.Clock()

        self.menu = Menu(self.width, self.height)
        self.game = None
        self.state = "MENU"

    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

            if self.state == "MENU":
                selected_map = self.menu.update(events)
                self.menu.draw(self.screen)

                if selected_map:
                    self.state = "PARSING"
                    self.map_to_load = selected_map

            elif self.state == "PARSING":
                try:
                    game_map = parse(self.map_to_load)
                    self.game = SimpleGame(game_map)
                    self.menu.video.release()
                    self.state = "GAME"
                except Exception as error:
                    print(error)
                    self.menu.set_error(str(error))
                    self.state = "MENU"

            elif self.state == "GAME":
                self.game.update(events)
                self.game.draw(self.screen)

            pygame.display.update()
            self.clock.tick(30)

        pygame.quit()
        sys.exit()
