from numpy import dtype, floating, integer, ndarray
import pygame
import cv2  # type: ignore
import os
from typing import Any, Literal, Never, Tuple
from pygame.font import Font


class Button:
    def __init__(self, x, y, width, height, text, font,
                 action_value=None) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.text: Any = text
        self.font: Any = font
        self.action_value: None | Any = action_value
        self.error_message: Literal[''] = ""

        self.color_normal = (60, 60, 60)
        self.color_hover = (255, 255, 255)
        self.thickness = 3

    def draw(self, surface, offset_y=0) -> None:
        draw_rect: pygame.Rect = self.rect.copy()
        draw_rect.y -= offset_y

        mouse_pos: Tuple[int, int] = pygame.mouse.get_pos()
        is_hovered: bool = self.rect.collidepoint(mouse_pos[0],
                                                  mouse_pos[1] + offset_y)
        current_color: tuple[int, int, int] = (
                self.color_hover if is_hovered else self.color_normal)

        pygame.draw.rect(surface, current_color, draw_rect,
                         width=self.thickness, border_radius=12)

        text_surf: Any = self.font.render(self.text, True, current_color)
        text_rect: Any = text_surf.get_rect(center=draw_rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event, offset_y=0) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            adjusted_pos: tuple = (event.pos[0], event.pos[1] + offset_y)
            if self.rect.collidepoint(adjusted_pos):
                return True
        return False


class Menu:
    def __init__(self, width, height) -> None:
        self.width: Any = width
        self.height: Any = height

        # Video
        self.video = cv2.VideoCapture("assets/final_drone.mp4")
        self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.direction = 1

        # Fonts
        self.font_title: Font = pygame.font.SysFont("arial", 80, bold=True)
        self.font_btn: Font = pygame.font.SysFont("arial", 50)
        self.font_subtitle: Font = pygame.font.SysFont("arial", 25, bold=True)

        # Error Handling
        self.font_error: Font = pygame.font.SysFont("arial", 40, bold=True)
        self.error_msg: Literal[''] = ""
        self.error_time: int = 0

        # Menu States
        self.state = "CATEGORIES"
        self.current_category: Literal[''] = ""
        self.scroll_y: int = 0

        self.category_buttons: list = []
        self.map_buttons: list = []
        self.back_btn: Button | None = None
        self.setup_categories()

    def set_error(self, message) -> None:
        """ Triggers the display of an error message """
        self.error_msg = message
        self.error_time = pygame.time.get_ticks()

    def setup_categories(self) -> None:
        self.category_buttons = []
        categories: list[str] = ["easy", "medium", "hard",
                                 "challenger", "custom"]
        x, y, w, h = 200, 650, 950, 90
        for cat in categories:
            self.category_buttons.append(Button(x, y, w, h, cat,
                                                self.font_btn, cat))
            y += 120

    def load_maps_from_folder(self,
                              category_name) -> Tuple[
                                  Literal[False], str] | Tuple[
                                      Literal[True], Literal['Success']]:
        """ Loads maps and returns (Success_Boolean, Error_Message) """
        self.map_buttons = []
        self.scroll_y = 0
        path: str = os.path.join("maps", category_name)

        self.back_btn = Button(150, 1300, 500, 90, "< BACK",
                               self.font_btn)

        # Check if directory exists
        if not os.path.exists(path):
            return False, f"[Error]: Directory '{path}' not found!"

        files: list[str] = [f for f in os.listdir(path) if f.endswith(".txt")]

        # Check if directory is empty
        if not files:
            return False, f"[Error]: No .txt files found in '{category_name}'!"

        x, y, w, h = 200, 670, 1200, 90
        for f in files:
            self.map_buttons.append(Button(x, y, w, h, f, self.font_btn, f))
            y += 120

        return True, "Success"

    def update_video(self) -> None | pygame.Surface:
        curr = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
        if curr >= self.total_frames - 1:
            self.direction = -1
        if curr <= 0:
            self.direction = 1

        ret: bool
        frame: (cv2.Mat | ndarray[Any, dtype[integer[Any] | floating[Any]]])

        ret, frame = self.video.read()
        if not ret:
            return None
        self.video.set(cv2.CAP_PROP_POS_FRAMES, curr + self.direction)

        frame = (
            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            .swapaxes(0, 1)
        )
        surf: pygame.Surface = pygame.surfarray.make_surface(frame)
        return pygame.transform.scale(surf, (self.width, self.height))

    def update(self, events) -> str | None:
        max_scroll: int = 0
        if self.state == "MAPS" and len(self.map_buttons) > 0:
            last_btn_bottom: Any = self.map_buttons[-1].rect.bottom
            max_scroll = max(0, last_btn_bottom - 1190)

        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                self.scroll_y -= event.y * 60
                self.scroll_y = max(0, min(self.scroll_y, max_scroll))

            if self.state == "CATEGORIES":
                for btn in self.category_buttons:
                    if btn.is_clicked(event):
                        self.current_category = btn.action_value

                        success: bool
                        error_msg: str
                        success, error_msg = self.load_maps_from_folder(
                            self.current_category)
                        if success:
                            self.state = "MAPS"
                        else:
                            self.set_error(error_msg)

            elif self.state == "MAPS":
                if self.back_btn and self.back_btn.is_clicked(event):
                    self.state = "CATEGORIES"

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if 650 <= event.pos[1] <= 1210:
                        for btn in self.map_buttons:
                            if btn.is_clicked(event, self.scroll_y):
                                return os.path.join("maps",
                                                    self.current_category,
                                                    btn.action_value)
        return None

    def draw(self, screen) -> None:
        video_surf: None | pygame.Surface = self.update_video()
        if video_surf:
            screen.blit(video_surf, (0, 0))

        top_text_surf: pygame.Surface = self.font_subtitle.render(
            "CPIETRZA - POWERED BY: 42", True, (50, 50, 50))
        screen.blit(top_text_surf, (2440, 1460))

        if self.state == "CATEGORIES":
            title_surf: pygame.Surface = self.font_title.render(
                "SELECT DIFFICULTY", True, (70, 75, 80))
            screen.blit(title_surf, (200, 550))
            for btn in self.category_buttons:
                btn.draw(screen)

        elif self.state == "MAPS":
            title_surf = self.font_title.render(
                f"MAPS: {self.current_category.upper()}", True, (70, 75, 80))
            screen.blit(title_surf, (200, 550))

            bg_panel = pygame.Surface((1280, 560), pygame.SRCALPHA)
            pygame.draw.rect(bg_panel,
                             (127, 134, 144, 180), bg_panel.get_rect())
            screen.blit(bg_panel, (140, 650))

            scroll_area = pygame.Rect(0, 650, self.width, 560)
            screen.set_clip(scroll_area)
            for btn in self.map_buttons:
                btn.draw(screen, self.scroll_y)
            screen.set_clip(None)

            if self.back_btn:
                self.back_btn.draw(screen)

        # --- Display Error Message ---
        if self.error_msg:
            current_time: int = pygame.time.get_ticks()
            if current_time - self.error_time < 3000:
                lines: Never = self.error_msg.splitlines()
                for i, line in enumerate(lines):
                    surf: pygame.Surface = self.font_error.render(
                        line, True, (255, 255, 255))
                    bg_rect: pygame.Rect = surf.get_rect(
                        center=(self.width//2, 60 + i * 70))
                    bg_rect.inflate_ip(40, 20)
                    pygame.draw.rect(screen, (220, 50, 50),
                                     bg_rect, border_radius=10)
                    screen.blit(surf, surf.get_rect(center=bg_rect.center))
            else:
                self.error_msg = ""
