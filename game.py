import sys
import math
import pygame
from pygame.event import Event
from pygame.font import Font
from typing import NoReturn

from menu import Menu
from parser import Global, ParseMaps
from generator_map import GraphRenderer, Buttom_Gm, VisualDrone, VisualNode
from solver import TrafficController
from converter import GifConverter
from structure import Connection
from simulation_output import print_simulation_output


class SimpleGame:
    """Manages the main game loop, rendering, and interaction.

    Handles camera movement (pan), UI overlays, tooltips, and the visual
    advancement of drone animations based on the solved flight plan.
    """

    def __init__(
        self, game_map: Global, map_path: str, simulation_state: bool
    ) -> None:
        """Initializes the SimpleGame environment for a specific map.

        Args:
            game_map: The parsed map model containing all nodes.
            map_path: The file path to the loaded map text file.
            simulation_state: Initial state for the simulation pause/play.
        """
        self.game_map: Global = game_map
        self.map_path: str = map_path
        self.simulation_state: bool = simulation_state

        self.world_surface: pygame.Surface = pygame.Surface(
            (2832, 1504), pygame.SRCALPHA
        )
        self.font: Font = pygame.font.SysFont("arial", 80, bold=True)
        self.font_btn: Font = pygame.font.SysFont("arial", 40, bold=True)

        self.camera_x: float = 0.0
        self.camera_y: float = 0.0
        self.is_dragging: bool = False
        self.sim_speed: int = 1
        self.bg_scroll_active: bool = False

        self.renderer: GraphRenderer = GraphRenderer(self.game_map)

        self.is_finished: bool = False
        self.total_turns: int = 0

        self.init_ui_components()
        self.init_backgrounds()
        self.init_simulation()

    def init_ui_components(self) -> None:
        """Initializes the interactive buttons and menus for the game."""
        self.return_btn: Buttom_Gm = Buttom_Gm(
            10, 10, 90, 90, "MENU", (50, 50, 50)
        )
        self.quit_btn: Buttom_Gm = Buttom_Gm(
            110, 10, 90, 90, "EXIT", (50, 50, 50)
        )

        popup_w: int = 1000
        popup_h: int = 800
        popup_x: int = (2832 - popup_w) // 2
        popup_y: int = (1504 - popup_h) // 2

        self.popup_menu_btn: Buttom_Gm = Buttom_Gm(
            popup_x + 200, popup_y + 650, 250, 80, "MENU", (50, 50, 50)
        )
        self.popup_restart_btn: Buttom_Gm = Buttom_Gm(
            popup_x + 550, popup_y + 650, 250, 80, "RESTART", (50, 50, 50)
        )

    def init_backgrounds(self) -> None:
        """Loads and prepares the background images and animated GIFs."""
        self.map_gif: GifConverter = GifConverter(
            "assets/map.gif", (80, 80)
        )
        self.drone_gif: GifConverter = GifConverter(
            "assets/blue_drone.gif", (80, 80)
        )
        self.spin_gif: GifConverter = GifConverter(
            "assets/spin.gif", (80, 80)
        )

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

        self.bg_images: list[pygame.Surface] = [
            img5, img4, img3, img2, img1
        ]
        self.bg_frame: float = 0.0
        self.bg_speed: float = 0.25

    def init_simulation(self) -> None:
        """Solves the map and creates the visual drone entities."""
        start_name: str = self.game_map.glb_start.name
        start_x: int
        start_y: int
        start_x, start_y = self.renderer.hub_info[start_name]

        node: VisualNode | None = self.renderer.nodes.get(start_name)
        if node is None:
            raise ValueError(f"Node {start_name} not found")

        self.traffic_controller: TrafficController = TrafficController(
            self.game_map
        )
        tarmac: TrafficController = self.traffic_controller

        wp_name: str
        node_a: str
        node_b: str
        fraction: float
        for wp_name, node_a, node_b, fraction in tarmac.generated_waypoints:
            x_a: int
            y_a: int
            x_b: int
            y_b: int
            x_a, y_a = self.renderer.hub_info[node_a]
            x_b, y_b = self.renderer.hub_info[node_b]
            self.renderer.hub_info[wp_name] = (
                int(x_a + (x_b - x_a) * fraction),
                int(y_a + (y_b - y_a) * fraction)
            )

        flight_plan: dict[str, list[str]] = tarmac.get_traffic_plan()
        print_simulation_output(flight_plan, self.map_path)

        self.total_turns = tarmac.get_total_turns()

        drone_id: str
        plan: list[str]
        for drone_id, plan in flight_plan.items():
            drones: VisualDrone = VisualDrone(
                drone_id,
                float(start_x),
                float(start_y),
                self.renderer.dict_x,
                self.renderer.dict_y,
                node.radius,
                plan,
                self.renderer.hub_info
            )
            self.renderer.drones_sprites.add(drones)

    def update(self, events: list[Event]) -> str | None:
        """Updates simulation logic and handles inputs each frame.

        Args:
            events: A list of pygame events detected this frame.

        Returns:
            A string indicating a state change ("MENU", "RESTART"),
            or None if the state should not change.
        """
        if self.simulation_state:
            for _ in range(self.sim_speed):
                self.renderer.drones_sprites.update()

        all_finished: bool = True
        drone: VisualDrone
        for drone in self.renderer.drones_sprites:
            if drone.step < len(drone.flight_plan):
                all_finished = False
                break

        if all_finished and len(self.renderer.drones_sprites) > 0:
            self.simulation_state = False
            self.is_finished = True

        event: Event
        for event in events:
            mouse_result: str | None = self.handle_mouse_events(event)
            if mouse_result is not None:
                return mouse_result

            self.handle_keyboard_events(event)

        return None

    def handle_mouse_events(self, event: Event) -> str | None:
        """Processes mouse clicks and drags.

        Args:
            event: A single Pygame event.

        Returns:
            A string indicating a state change if a button was clicked,
            or None otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if getattr(self, 'is_finished', False):
                if self.popup_menu_btn.rect.collidepoint(event.pos):
                    return "MENU"
                if self.popup_restart_btn.rect.collidepoint(event.pos):
                    return "RESTART"

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

        return None

    def handle_keyboard_events(self, event: Event) -> None:
        """Processes keyboard inputs to control simulation speed and state.

        Args:
            event: A single Pygame event.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.simulation_state = not self.simulation_state
            elif event.key == pygame.K_RIGHT:
                if self.sim_speed == 1:
                    self.sim_speed = 2
                elif self.sim_speed == 2:
                    self.sim_speed = 4
                elif self.sim_speed == 4:
                    self.sim_speed = 8
            elif event.key == pygame.K_LEFT:
                if self.sim_speed == 8:
                    self.sim_speed = 4
                elif self.sim_speed == 4:
                    self.sim_speed = 2
                elif self.sim_speed == 2:
                    self.sim_speed = 1
            elif event.key == pygame.K_w:
                self.bg_scroll_active = not self.bg_scroll_active

    def draw(self, screen: pygame.Surface) -> None:
        """Renders the entire game screen.

        Args:
            screen: The main Pygame surface to draw everything on.
        """
        self.draw_background(screen)
        self.draw_network()
        screen.blit(self.world_surface, (self.camera_x, self.camera_y))

        self.draw_ui(screen)

        if getattr(self, 'is_finished', False):
            self.draw_finished_popup(screen)

    def draw_background(self, screen: pygame.Surface) -> None:
        """Draws the animated background clouds.

        Args:
            screen: The main Pygame surface.
        """
        any_moving: bool = any(
            0 < d.current_frame < d.frames_per_turn
            for d in self.renderer.drones_sprites
        )
        if self.simulation_state and self.bg_scroll_active and any_moving:
            self.bg_frame += self.bg_speed
        if self.bg_frame >= len(self.bg_images):
            self.bg_frame = 0.0

        current_bg: pygame.Surface = self.bg_images[int(self.bg_frame)]
        screen.blit(current_bg, (0, 0))

    def draw_network(self) -> None:
        """Draws the nodes, connections, and drones to the world surface."""
        self.world_surface.fill((0, 0, 0, 0))
        self.renderer.draw_connections(self.world_surface)
        self.renderer.all_sprites.draw(self.world_surface)
        self.renderer.drones_sprites.draw(self.world_surface)

    def draw_ui(self, screen: pygame.Surface) -> None:
        """Draws all persistent UI components on top of the world.

        Args:
            screen: The main Pygame surface.
        """
        self.return_btn.draw(screen)
        self.quit_btn.draw(screen)
        self.draw_legend(screen)
        self.draw_turn_counter(screen)
        self.draw_tooltip(screen)

    def get_hovered_element(
        self, world_x: float, world_y: float
    ) -> tuple[str | None, VisualNode | None, 'Connection | None']:
        """Finds if the mouse is hovering over a hub or a connection.

        Args:
            world_x: Mouse X position adjusted by camera.
            world_y: Mouse Y position adjusted by camera.

        Returns:
            A tuple containing the hovered node name, the node object,
            and the hovered connection object.
        """
        hovered_node: str | None = None
        node_obj: VisualNode | None = None

        name: str
        node: VisualNode
        for name, node in self.renderer.nodes.items():
            dist: float = math.hypot(
                node.rect.centerx - world_x, node.rect.centery - world_y
            )
            if dist <= node.rect.width / 2:
                hovered_node = name
                node_obj = node
                break

        hovered_conn: 'Connection | None' = None
        if not hovered_node:
            conn: Connection
            for conn in self.game_map.glb_connection:
                node_a: VisualNode | None = self.renderer.nodes.get(
                    conn.connection_a
                )
                node_b: VisualNode | None = self.renderer.nodes.get(
                    conn.connection_b
                )
                if not node_a or not node_b:
                    continue
                x1: int = node_a.rect.centerx
                y1: int = node_a.rect.centery
                x2: int = node_b.rect.centerx
                y2: int = node_b.rect.centery

                line_len_sq: int = (x2 - x1)**2 + (y2 - y1)**2
                if line_len_sq == 0:
                    continue
                num: float = (
                    (world_x - x1) * (x2 - x1)
                    + (world_y - y1) * (y2 - y1)
                )
                t: float = max(0.0, min(1.0, num / line_len_sq))
                proj_x: float = x1 + t * (x2 - x1)
                proj_y: float = y1 + t * (y2 - y1)
                dist_proj: float = math.hypot(
                    world_x - proj_x, world_y - proj_y
                )
                if dist_proj <= 15.0:
                    hovered_conn = conn
                    break

        return hovered_node, node_obj, hovered_conn

    def draw_tooltip(self, screen: pygame.Surface) -> None:
        """Draws the capacity tooltip when hovering elements.

        Args:
            screen: The main Pygame surface.
        """
        mouse_x: int
        mouse_y: int
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x: float = mouse_x - self.camera_x
        world_y: float = mouse_y - self.camera_y

        hovered_node: str | None
        node_obj: VisualNode | None
        hovered_conn: 'Connection | None'
        hovered_node, node_obj, hovered_conn = self.get_hovered_element(
            world_x, world_y
        )

        if not hovered_node and not hovered_conn:
            return

        current_turn: int = 0
        if self.renderer.drones_sprites:
            current_turn = max(d.step for d in self.renderer.drones_sprites)
            if current_turn > self.total_turns:
                current_turn = self.total_turns

        drone_count: int = 0
        cap: int = 0
        if hovered_node and node_obj:
            log_entry: tuple[int, int] | None = (
                self.traffic_controller.hub_usage_log.get(
                    (hovered_node, current_turn)
                )
            )
            if log_entry is not None:
                drone_count = log_entry[0]
                cap = log_entry[1]
            else:
                cap = node_obj.capacity
        elif hovered_conn:
            ca: str = hovered_conn.connection_a
            cb: str = hovered_conn.connection_b
            canonical: tuple[str, str] = (min(ca, cb), max(ca, cb))
            log_entry = self.traffic_controller.link_usage_log.get(
                (canonical, current_turn)
            )
            if log_entry is not None:
                drone_count = log_entry[0]
                cap = log_entry[1]
            else:
                cap = hovered_conn.max_link_capacity

        font: pygame.font.Font = pygame.font.SysFont(None, 36)
        label: str
        if hovered_node and node_obj:
            label = f"Hub: {hovered_node}"
        elif hovered_conn:
            ca = hovered_conn.connection_a
            cb = hovered_conn.connection_b
            label = f"Conn: {ca} <-> {cb}"
        else:
            label = "Unknown"

        text1: pygame.Surface = font.render(label, True, (255, 255, 255))
        text2: pygame.Surface = font.render(
            f"Drones: {drone_count} / {cap}", True, (255, 255, 255)
        )

        tw: int = max(text1.get_width(), text2.get_width())
        tw += 20

        th: int = text1.get_height() + text2.get_height() + 20

        box_x: int = mouse_x + 15
        box_y: int = mouse_y + 15
        if box_x + tw > screen.get_width():
            box_x = mouse_x - tw - 15
        if box_y + th > screen.get_height():
            box_y = mouse_y - th - 15

        tooltip_bg: pygame.Surface = pygame.Surface(
            (tw, th), pygame.SRCALPHA
        )
        tooltip_bg.fill((20, 20, 20, 220))
        screen.blit(tooltip_bg, (box_x, box_y))
        pygame.draw.rect(screen, (100, 100, 100), (box_x, box_y, tw, th), 2)

        screen.blit(text1, (box_x + 10, box_y + 10))
        screen.blit(text2, (box_x + 10, box_y + 10 + text1.get_height()))

    def draw_turn_counter(self, screen: pygame.Surface) -> None:
        """Draws the current turn counter in the bottom-left corner.

        Args:
            screen: The main Pygame surface.
        """
        current_turn: int = 0
        if self.renderer.drones_sprites:
            current_turn = max(d.step for d in self.renderer.drones_sprites)
        display_turn: int = min(current_turn, self.total_turns)
        label: str = f"{display_turn} / {self.total_turns}"

        font_counter: pygame.font.Font = pygame.font.SysFont(
            "arial", 42, bold=True
        )

        text_surface: pygame.Surface = font_counter.render(
            label, True, (255, 255, 255)
        )
        text_w: int = text_surface.get_width()
        text_h: int = text_surface.get_height()

        padding: int = 18
        box_w: int = text_w + padding * 2
        box_h: int = text_h + padding * 2
        box_x: int = 20
        box_y: int = screen.get_height() - box_h - 20

        box_bg: pygame.Surface = pygame.Surface(
            (box_w, box_h), pygame.SRCALPHA
        )
        box_bg.fill((20, 20, 20, 200))
        screen.blit(box_bg, (box_x, box_y))

        pygame.draw.rect(
            screen,
            (150, 150, 200),
            (box_x, box_y, box_w, box_h),
            width=2,
            border_radius=10
        )

        screen.blit(
            text_surface,
            (box_x + padding, box_y + padding)
        )

    def draw_legend(self, screen: pygame.Surface) -> None:
        """Draws the informational legend explaining zones and controls.

        Args:
            screen: The main Pygame surface.
        """
        font_title: Font = pygame.font.SysFont("arial", 28, bold=True)
        font_text: Font = pygame.font.SysFont("arial", 22)

        legend_w: int = 320
        legend_h: int = 350
        legend_x: int = screen.get_width() - legend_w - 20
        legend_y: int = 20

        overlay: pygame.Surface = pygame.Surface(
            (legend_w, legend_h), pygame.SRCALPHA
        )
        overlay.fill((40, 40, 40, 210))
        screen.blit(overlay, (legend_x, legend_y))
        pygame.draw.rect(
            screen,
            (200, 200, 200),
            (legend_x, legend_y, legend_w, legend_h),
            2,
            border_radius=10
        )

        y_offset: int = legend_y + 15

        title_controls: pygame.Surface = font_title.render(
            "Controls", True, (255, 255, 255)
        )
        screen.blit(title_controls, (legend_x + 15, y_offset))
        y_offset += 35

        bg_state: str = "ON" if self.bg_scroll_active else "OFF"
        controls: list[tuple[str, str]] = [
            ("SPACE", "Play / Pause"),
            ("LEFT / RIGHT", "Change Speed"),
            ("W", f"Background ({bg_state})"),
            ("Right Click", "Move Camera")
        ]
        key: str
        desc: str
        for key, desc in controls:
            text: pygame.Surface = font_text.render(
                f"{key}: {desc}", True, (200, 200, 200)
            )
            screen.blit(text, (legend_x + 15, y_offset))
            y_offset += 25

        y_offset += 15

        title_zones: pygame.Surface = font_title.render(
            "Hub Zones", True, (255, 255, 255)
        )
        screen.blit(title_zones, (legend_x + 15, y_offset))
        y_offset += 35

        zones: list[tuple[str, tuple[int, int, int], str]] = [
            ("Normal", (150, 150, 150), "No badge"),
            ("Priority (P)", (0, 150, 255), "Cost: 1 turn"),
            ("Restricted (!)", (255, 165, 0), "Cost: 2 turns"),
            ("Blocked (X)", (220, 20, 60), "Cost: Inaccessible")
        ]

        zone_name: str
        color: tuple[int, int, int]
        for zone_name, color, desc in zones:
            pygame.draw.circle(
                screen, color, (legend_x + 25, y_offset + 12), 8
            )
            text_z: pygame.Surface = font_text.render(
                f"{zone_name} - {desc}", True, (200, 200, 200)
            )
            screen.blit(text_z, (legend_x + 45, y_offset))
            y_offset += 28

    def draw_finished_popup(self, screen: pygame.Surface) -> None:
        """Draws the final statistics popup when simulation finishes.

        Args:
            screen: The main Pygame surface.
        """
        map_name: str = self.map_path.split('/')[-1]
        drone_count: int = self.game_map.glb_drones.drone_count

        popup_w: int = 1000
        popup_h: int = 800
        popup_x: int = (screen.get_width() - popup_w) // 2
        popup_y: int = (screen.get_height() - popup_h) // 2

        overlay: pygame.Surface = pygame.Surface(
            (screen.get_width(), screen.get_height()),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(
            screen, (30, 30, 40),
            (popup_x, popup_y, popup_w, popup_h),
            border_radius=20
        )
        pygame.draw.rect(
            screen, (100, 100, 150),
            (popup_x, popup_y, popup_w, popup_h),
            width=4, border_radius=20
        )

        font_title: pygame.font.Font = pygame.font.SysFont(None, 80)
        font_text: pygame.font.Font = pygame.font.SysFont(None, 50)

        text_title: pygame.Surface = font_title.render(
            "Simulation Finished", True, (255, 255, 255)
        )
        text_map: pygame.Surface = font_text.render(
            f"Map: {map_name}", True, (200, 200, 200)
        )
        text_drones: pygame.Surface = font_text.render(
            f"Total Drones: {drone_count}", True, (200, 200, 200)
        )
        text_turns: pygame.Surface = font_text.render(
            f"Total Turns: {self.total_turns}",
            True, (200, 200, 200)
        )

        tx_x: int = popup_x + (popup_w - text_title.get_width()) // 2
        screen.blit(text_title, (tx_x, popup_y + 80))

        tm_x: int = popup_x + (popup_w - text_map.get_width()) // 2
        screen.blit(text_map, (tm_x, popup_y + 220))
        screen.blit(self.map_gif.get_frame(), (tm_x - 100, popup_y + 200))

        td_x: int = popup_x + (popup_w - text_drones.get_width()) // 2
        screen.blit(text_drones, (td_x, popup_y + 340))
        screen.blit(
            self.drone_gif.get_frame(), (td_x - 100, popup_y + 320)
        )

        tu_x: int = popup_x + (popup_w - text_turns.get_width()) // 2
        screen.blit(text_turns, (tu_x, popup_y + 460))
        screen.blit(self.spin_gif.get_frame(), (tu_x - 100, popup_y + 440))

        self.popup_menu_btn.draw(screen)
        self.popup_restart_btn.draw(screen)


class GameApp:
    """Main application controller managing states between menus and game.

    Initializes the Pygame window and handles the high-level transition
    between the 'MENU', 'PARSING', and 'GAME' states.
    """

    def __init__(self) -> None:
        """Initializes the Pygame application, window, and main menu."""
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
        """Executes the main application loop.

        Continuously processes events, updates the active state logic,
        and renders the screen until the user quits the application.
        """
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
                    elif next_state == "RESTART":
                        self.state = "PARSING"
                    self.game.draw(self.screen)

            pygame.display.update()
            self.clock.tick(30)

        pygame.quit()
        sys.exit()
