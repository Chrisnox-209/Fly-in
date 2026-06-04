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
from convertisseur import GifConverter


def print_simulation_output(flight_plan: dict[str, list[str]]) -> None:
    if not flight_plan:
        return

    print("\n=== SIMULATION OUTPUT ===")
    max_turns = max(len(plan) for plan in flight_plan.values())

    for step in range(1, max_turns):
        line = ""
        for drone_id, plan in flight_plan.items():
            if step < len(plan):
                if plan[step] != plan[step - 1]:
                    dest = plan[step]
                    if dest.startswith("wp_"):
                        dest = dest[3:].replace("_", "-")
                    line += f"{drone_id}-{dest} "
        if line:
            print(line.strip())


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
        self.speed_btn: Buttom_Gm = Buttom_Gm(
            110, 10, 90, 90, "x1", (50, 50, 50)
        )
        self.bg_btn: Buttom_Gm = Buttom_Gm(
            210, 10, 90, 90, "OFF", (50, 50, 50)
        )
        self.quit_btn: Buttom_Gm = Buttom_Gm(
            310, 10, 90, 90, "EXIT", (50, 50, 50)
        )
        self.sim_speed: int = 1
        self.bg_scroll_active: bool = False

        self.map_gif: GifConverter = GifConverter("assets/map.gif", (80, 80))
        self.drone_gif: GifConverter = GifConverter(
            "assets/blue_drone.gif", (80, 80)
        )
        self.spin_gif: GifConverter = GifConverter("assets/spin.gif", (80, 80))

        popup_w = 1000
        popup_h = 800
        popup_x = (2832 - popup_w) // 2
        popup_y = (1504 - popup_h) // 2
        self.popup_menu_btn: Buttom_Gm = Buttom_Gm(
            popup_x + 200, popup_y + 650, 250, 80, "MENU", (50, 50, 50)
        )
        self.popup_restart_btn: Buttom_Gm = Buttom_Gm(
            popup_x + 550, popup_y + 650, 250, 80, "RESTART", (50, 50, 50)
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
        self.bg_speed: float = 0.5

        start_name: str = self.game_map.glb_start.name
        start_x: int
        start_y: int
        start_x, start_y = self.renderer.hub_info[start_name]

        node: VisualNode | None = self.renderer.nodes.get(start_name)
        if node is None:
            raise ValueError(f"Node {start_name} not found")

        tarmac: TrafficController = TrafficController(game_map)
        for wp_name, node_a, node_b, fraction in tarmac.generated_waypoints:
            x_a, y_a = self.renderer.hub_info[node_a]
            x_b, y_b = self.renderer.hub_info[node_b]
            self.renderer.hub_info[wp_name] = (
                int(x_a + (x_b - x_a) * fraction),
                int(y_a + (y_b - y_a) * fraction)
            )

        flight_plan: dict[str, list[str]] = tarmac.get_traffic_plan()
        print_simulation_output(flight_plan)

        self.is_finished: bool = False
        self.total_turns: int = 0
        if flight_plan:
            self.total_turns = max(
                len(plan) for plan in flight_plan.values()
            ) - 1

        id_drone: str
        plan: list[str]
        for id_drone, plan in flight_plan.items():
            drones: VisualDrone = VisualDrone(
                id_drone,
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
                if self.speed_btn.rect.collidepoint(event.pos):
                    if self.sim_speed == 1:
                        self.sim_speed = 2
                    elif self.sim_speed == 2:
                        self.sim_speed = 4
                    elif self.sim_speed == 4:
                        self.sim_speed = 8
                    else:
                        self.sim_speed = 1
                    self.speed_btn.text = f"x{self.sim_speed}"
                if self.bg_btn.rect.collidepoint(event.pos):
                    self.bg_scroll_active = not self.bg_scroll_active
                    if self.bg_scroll_active:
                        self.bg_btn.text = "ON"
                    else:
                        self.bg_btn.text = "OFF"
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

            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.zoom += 0.1
                elif event.y < 0:
                    self.zoom -= 0.1

                if self.zoom < 0.2:
                    self.zoom = 0.2

        return None

    def draw(self, screen: pygame.Surface) -> None:
        if self.simulation_state and getattr(self, 'bg_scroll_active', True):
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
        self.speed_btn.draw(screen)
        self.bg_btn.draw(screen)
        self.quit_btn.draw(screen)

        self.draw_tooltip(screen)

        if getattr(self, 'is_finished', False):

            map_name: str = self.map_path.split('/')[-1]
            nb_drones: int = self.game_map.glb_drones.nb_drone

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
                f"Total Drones: {nb_drones}", True, (200, 200, 200)
            )
            text_turns: pygame.Surface = font_text.render(
                f"Total Turns: {self.total_turns}",
                True, (200, 200, 200)
            )

            tx_x = popup_x + (popup_w - text_title.get_width()) // 2
            screen.blit(text_title, (tx_x, popup_y + 80))

            # Map line
            tm_x = popup_x + (popup_w - text_map.get_width()) // 2
            screen.blit(text_map, (tm_x, popup_y + 220))
            screen.blit(self.map_gif.get_frame(), (tm_x - 100, popup_y + 200))

            # Drones line
            td_x = popup_x + (popup_w - text_drones.get_width()) // 2
            screen.blit(text_drones, (td_x, popup_y + 340))
            screen.blit(
                self.drone_gif.get_frame(), (td_x - 100, popup_y + 320)
            )

            # Turns line
            tu_x = popup_x + (popup_w - text_turns.get_width()) // 2
            screen.blit(text_turns, (tu_x, popup_y + 460))
            screen.blit(self.spin_gif.get_frame(), (tu_x - 100, popup_y + 440))

            self.popup_menu_btn.draw(screen)
            self.popup_restart_btn.draw(screen)

    def draw_tooltip(self, screen: pygame.Surface) -> None:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x = (mouse_x - self.camera_x) / self.zoom
        world_y = (mouse_y - self.camera_y) / self.zoom

        hovered_node = None
        node_obj = None
        for name, node in self.renderer.nodes.items():
            dist = math.hypot(
                node.rect.centerx - world_x, node.rect.centery - world_y
            )
            if dist <= node.rect.width / 2:
                hovered_node = name
                node_obj = node
                break

        hovered_conn = None
        if not hovered_node:
            for conn in self.game_map.glb_connection:
                node_a = self.renderer.nodes.get(conn.connection_a)
                node_b = self.renderer.nodes.get(conn.connection_b)
                if not node_a or not node_b:
                    continue
                x1, y1 = node_a.rect.centerx, node_a.rect.centery
                x2, y2 = node_b.rect.centerx, node_b.rect.centery
                line_len_sq = (x2 - x1)**2 + (y2 - y1)**2
                if line_len_sq == 0:
                    continue
                num = (world_x - x1) * (x2 - x1) + (world_y - y1) * (y2 - y1)
                t = max(0, min(1, num / line_len_sq))
                proj_x = x1 + t * (x2 - x1)
                proj_y = y1 + t * (y2 - y1)
                dist_proj = math.hypot(world_x - proj_x, world_y - proj_y)
                if dist_proj <= 15 / self.zoom:
                    hovered_conn = conn
                    break

        if not hovered_node and not hovered_conn:
            return

        drones_list: list[str] = []
        for d in self.renderer.drones_sprites:
            if d.step >= len(d.flight_plan):
                continue
            curr = d.flight_plan[d.step]
            next_h = d.flight_plan[min(d.step + 1, len(d.flight_plan) - 1)]

            if d.current_frame >= d.frames_per_turn:
                curr = next_h

            if hovered_node and node_obj:
                if curr == next_h and curr == hovered_node:
                    drones_list.append(d.name)
            elif hovered_conn:
                ca = hovered_conn.connection_a
                cb = hovered_conn.connection_b
                if curr != next_h:
                    def get_nodes(name: str) -> list[str]:
                        if name.startswith("wp_"):
                            return name[3:].split('_')
                        return [name]

                    involved = set(get_nodes(curr) + get_nodes(next_h))
                    if ca in involved and cb in involved:
                        drones_list.append(d.name)
                else:
                    wp1 = f"wp_{ca}_{cb}"
                    wp2 = f"wp_{cb}_{ca}"
                    if curr == wp1 or curr == wp2:
                        drones_list.append(d.name)

        drone_count = len(drones_list)

        font = pygame.font.SysFont(None, 36)
        if hovered_node and node_obj:
            label = f"Hub: {hovered_node}"
            cap = node_obj.capacity
        elif hovered_conn:
            ca = hovered_conn.connection_a
            cb = hovered_conn.connection_b
            label = f"Conn: {ca} <-> {cb}"
            cap = hovered_conn.max_link_capacity
        else:
            label = "Unknown"
            cap = 0

        text1 = font.render(label, True, (255, 255, 255))
        text2 = font.render(
            f"Drones: {drone_count} / {cap}", True, (255, 255, 255)
        )

        names_text = ""
        if drone_count > 0:
            names_text = ", ".join(drones_list)

        text3 = None
        if names_text:
            text3 = font.render(
                f"[{names_text}]", True, (150, 200, 255)
            )

        tw = max(text1.get_width(), text2.get_width())
        if text3:
            tw = max(tw, text3.get_width())
        tw += 20

        th = text1.get_height() + text2.get_height() + 20
        if text3:
            th += text3.get_height()

        box_x = mouse_x + 15
        box_y = mouse_y + 15
        if box_x + tw > screen.get_width():
            box_x = mouse_x - tw - 15
        if box_y + th > screen.get_height():
            box_y = mouse_y - th - 15

        pygame.draw.rect(
            screen, (30, 30, 40), (box_x, box_y, tw, th), border_radius=10
        )
        pygame.draw.rect(
            screen, (200, 200, 200), (box_x, box_y, tw, th),
            width=2, border_radius=10
        )

        screen.blit(text1, (box_x + 10, box_y + 10))
        screen.blit(text2, (box_x + 10, box_y + 10 + text1.get_height()))
        if text3:
            y_offset = box_y + 10 + text1.get_height() + text2.get_height()
            screen.blit(text3, (box_x + 10, y_offset))


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
                    elif next_state == "RESTART":
                        self.state = "PARSING"
                    self.game.draw(self.screen)

            pygame.display.update()
            self.clock.tick(30)

        pygame.quit()
        sys.exit()
