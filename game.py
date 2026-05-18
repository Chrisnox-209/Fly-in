import pygame
import sys
from pygame.event import Event
from pygame.font import Font
from menu import Menu
from parser import Global, parse
from typing import Any, List, NoReturn


class SimpleGame:
    def __init__(self, map_path) -> None:
        self.map_path: Any = map_path
        self.font: Font = pygame.font.SysFont("arial", 80, bold=True)

    def update(self, events) -> None:
        pass

    def draw(self, screen) -> None:
        screen.fill((20, 20, 20))
        text_surf: pygame.Surface = self.font.render("GAME IN PROGRESS",
                                                     True, (0, 255, 0))
        path_surf: pygame.Surface = self.font.render(f"File: {self.map_path}",
                                                     True, (255, 255, 255))

        screen.blit(text_surf, (200, 200))
        screen.blit(path_surf, (200, 350))


class GameApp:
    def __init__(self) -> None:
        pygame.init()
        self.width, self.height = 2832, 1504
        self.screen: pygame.Surface = pygame.display.set_mode(
            (self.width, self.height))

        icon: pygame.Surface = pygame.image.load(
            "assets/icon.png").convert_alpha()
        pygame.display.set_icon(icon)

        pygame.display.set_caption("Fly_In")
        self.clock = pygame.time.Clock()

        self.menu: Menu = Menu(self.width, self.height)
        self.game: SimpleGame | None = None
        self.state = "MENU"

    def run(self) -> NoReturn:
        running = True
        while running:
            events: List[Event] = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

            if self.state == "MENU":
                selected_map: str | None = self.menu.update(events)
                self.menu.draw(self.screen)

                if selected_map:
                    self.state = "PARSING"
                    self.map_to_load: str = selected_map

            elif self.state == "PARSING":
                try:
                    game_map: Global = parse(self.map_to_load)
                    self.game = SimpleGame(game_map)
                    self.menu.video.release()
                    self.state = "GAME"
                except Exception as error:
                    print(error)
                    self.menu.set_error(str(error))
                    self.state = "MENU"

            elif self.state == "GAME":
                if self.game is not None:
                    self.game.update(events)
                    self.game.draw(self.screen)

            pygame.display.update()
            self.clock.tick(30)

        pygame.quit()
        sys.exit()
