import sys
import pygame
from pygame.event import Event
from pygame.font import Font
from typing import NoReturn

from menu import Menu
from parser import Global, ParseMaps
from generator_map import GraphRenderer, Buttom_Gm, VisualDrone, VisualNode
from solver import TrafficController


class SimpleGame:
    def __init__(
        self, game_map: Global, map_path: str, simulation_state: bool
    ) -> None:
        self.game_map: Global = game_map
        self.map_path: str = map_path
        self.world_surface: pygame.Surface = pygame.Surface(
            (2832, 1504), pygame.SRCALPHA
        )
        self.font: Font = pygame.font.SysFont("arial", 80, bold=True)
        self.font_btn: Font = pygame.font.SysFont("arial", 40, bold=True)

        self.return_btn: Buttom_Gm = Buttom_Gm(
            10, 10, 90, 90, "MENU", (50, 50, 50)
        )
        self.quit_btn: Buttom_Gm = Buttom_Gm(
            110, 10, 90, 90, "EXIT", (50, 50, 50)
        )

        self.renderer: GraphRenderer = GraphRenderer(self.game_map)
        self.simulation_state: bool = simulation_state
        self.zoom: float = 1.0
        self.camera_x: float = 0.0
        self.camera_y: float = 0.0
        self.is_dragging: bool = False

        img1: pygame.Surface = pygame.transform.scale(
            pygame.image.load("assets/cloud1.png").convert_alpha(),
            (2832, 1504)
        )
        img2: pygame.Surface = pygame.transform.scale(
            pygame.image.load("assets/cloud2.png").convert_alpha(),
            (2832, 1504)
        )
        img3: pygame.Surface = pygame.transform.scale(
            pygame.image.load("assets/cloud3.png").convert_alpha(),
            (2832, 1504)
        )
        img4: pygame.Surface = pygame.transform.scale(
            pygame.image.load("assets/cloud4.png").convert_alpha(),
            (2832, 1504)
        )
        img5: pygame.Surface = pygame.transform.scale(
            pygame.image.load("assets/cloud5.png").convert_alpha(),
            (2832, 1504)
        )

        self.bg_images: list[pygame.Surface] = [img5, img4, img3, img2, img1]
        self.bg_frame: float = 0.0
        self.bg_speed: float = 0.0

        start_name: str = self.game_map.glb_start.name
        start_x: int
        start_y: int
        start_x, start_y = self.renderer.infos_hub[start_name]

        node: VisualNode | None = self.renderer.nodes.get(start_name)
        if node is None:
            raise ValueError(f"Node {start_name} introuvable")

        tarmac: TrafficController = TrafficController(game_map)
        flight_plan: dict[str, list[str]] = tarmac.trafic_drones()

        id_drone: str
        plan: list[str]
        for id_drone, plan in flight_plan.items():
            drones: VisualDrone = VisualDrone(
                start_x,
                start_y,
                self.renderer.dict_x,
                self.renderer.dict_y,
                node.radius,
                plan,
                self.renderer.infos_hub
            )
            self.renderer.drones_sprites.add(drones)

    def update(self, events: list[Event]) -> str | None:
        if self.simulation_state:
            self.renderer.drones_sprites.update()

        end: bool = True
        drone: VisualDrone
        for drone in self.renderer.drones_sprites:
            if drone.step < len(drone.flight_plan):
                end = False
                break

        if end and len(self.renderer.drones_sprites) > 0:
            self.simulation_state = False

        event: Event
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    self.is_dragging = True
                if self.return_btn.rect.collidepoint(event.pos):
                    return "MENU"
                if self.quit_btn.rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    self.is_dragging = False

            if event.type == pygame.MOUSEMOTION:
                if self.is_dragging:
                    self.camera_x += event.rel[0]
                    self.camera_y += event.rel[1]

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
        if self.simulation_state:
            self.bg_frame += self.bg_speed
        if self.bg_frame >= len(self.bg_images):
            self.bg_frame = 0.0

        current_bg: pygame.Surface = self.bg_images[int(self.bg_frame)]
        screen.blit(current_bg, (0, 0))

        self.world_surface.fill((0, 0, 0, 0))

        self.renderer.draw_connections(self.world_surface)
        self.renderer.all_sprites.draw(self.world_surface)
        self.renderer.drones_sprites.draw(self.world_surface)

        new_w: int = int(2832 * self.zoom)
        new_h: int = int(1504 * self.zoom)
        zoomed_surface: pygame.Surface = pygame.transform.smoothscale(
            self.world_surface, (new_w, new_h)
        )

        screen.blit(zoomed_surface, (self.camera_x, self.camera_y))

        self.return_btn.draw(screen)
        self.quit_btn.draw(screen)


class GameApp:
    def __init__(self) -> None:
        pygame.init()
        self.width: int = 2832
        self.height: int = 1504
        self.screen: pygame.Surface = pygame.display.set_mode(
            (self.width, self.height)
        )

        icon: pygame.Surface = pygame.image.load(
            "assets/icon.png"
        ).convert_alpha()
        pygame.display.set_icon(icon)

        pygame.display.set_caption("Fly_In")
        self.clock: pygame.time.Clock = pygame.time.Clock()

        self.menu: Menu = Menu(self.width, self.height)
        self.game: SimpleGame | None = None
        self.state: str = "MENU"
        self.map_to_load: str = ""

    def run(self) -> NoReturn:
        running: bool = True
        while running:
            events: list[Event] = pygame.event.get()

            event: Event
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

            if self.state == "MENU":
                selected_map: str | None = self.menu.update(events)
                self.menu.draw(self.screen)

                if selected_map:
                    self.state = "PARSING"
                    self.map_to_load = selected_map

            elif self.state == "PARSING":
                try:
                    game_map: Global = ParseMaps.parse(self.map_to_load)
                    self.game = SimpleGame(game_map, self.map_to_load, False)
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
