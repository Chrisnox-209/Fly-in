import pygame
import sys
from pygame.event import Event
from pygame.font import Font
from menu import Menu
from parser import Global, ParseMaps
from typing import List, NoReturn, Any
from generator_map import GraphRenderer, Buttom_Gm, VisualDrone, VisualNode
from solver import TrafficController


class SimpleGame:
    def __init__(self, game_map: Global, map_path: str,
                 simulation_state: bool) -> None:
        self.game_map: Global = game_map
        self.map_path: str = map_path
        self.font: Font = pygame.font.SysFont("arial", 80, bold=True)

        self.font_btn: Font = pygame.font.SysFont("arial", 40, bold=True)
        self.return_btn: Buttom_Gm = Buttom_Gm(
            10, 10, 90, 90, "MENU", (50, 50, 50))
        self.quit_btn: Buttom_Gm = Buttom_Gm(
            110, 10, 90, 90, "EXIT", (50, 50, 50))
        self.renderer: GraphRenderer = GraphRenderer(self.game_map)

        self.simulation_state: bool = simulation_state
        self.zoom: float = 1.0

        start_x: Any
        start_y: Any
        start_name: str = self.game_map.glb_start.name
        start_x, start_y = self.renderer.infos_hub[start_name]
        node: VisualNode | None = self.renderer.nodes.get(start_name)
        if node is None:
            raise ValueError(f"Node {start_name} introuvable")

        tarmac = TrafficController(game_map)
        flight_plan: dict = tarmac.trafic_drones()

        for id_drone, plan in flight_plan.items():
            drones = VisualDrone(start_x, start_y,
                                 self.renderer.dict_x, self.renderer.dict_y,
                                 node.radius,
                                 plan,
                                 self.renderer.infos_hub)
            self.renderer.drones_sprites.add(drones)

    def update(self, events: list[pygame.event.Event]) -> str | None:
        if self.simulation_state:
            self.renderer.drones_sprites.update()

        for event in events:
            # 1. Les clics de souris
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.return_btn.rect.collidepoint(event.pos):
                    return "MENU"
                if self.quit_btn.rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.simulation_state = not self.simulation_state

                if event.key == pygame.K_r:
                    pass

            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.zoom += 0.1
                elif event.y < 0:
                    self.zoom -= 0.1

                if self.zoom < 0.2:
                    self.zoom = 0.2

        return None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((80, 160, 220))

        self.renderer.draw_connections(screen)
        self.renderer.all_sprites.draw(screen)
        self.renderer.drones_sprites.draw(screen)

        self.return_btn.draw(screen)
        self.quit_btn.draw(screen)


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
                    game_map: Global = ParseMaps.parse(self.map_to_load)
                    self.game = SimpleGame(game_map, self.map_to_load, False)
                    # self.menu.video.release()
                    self.state = "GAME"
                except Exception as error:
                    print(error)
                    self.menu.set_error(str(error))
                    self.state = "MENU"

            elif self.state == "GAME":
                if self.game is not None:
                    next_state: str | None = self.game.update(events)
                    if next_state == "MENU":
                        self.state = "MENU"
                    self.game.draw(self.screen)

            pygame.display.update()
            self.clock.tick(30)

        pygame.quit()
        sys.exit()
