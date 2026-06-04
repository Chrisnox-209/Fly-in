import cv2  # type: ignore[import-untyped, unused-ignore]
import os
import sys
from typing import Optional, Any
import pygame
from pygame.font import Font


class Button:
    """A clickable Pygame button with hover effects and custom actions.

    Attributes:
        rect (pygame.Rect): The rectangular area of the button.
        text (str): The text displayed on the button.
        font (Font): The Pygame font used to render the text.
        action_value (Optional[str]): A specific value tied
        to the button's action.
        color_normal (tuple[int, int, int]): The button's default color.
        color_hover (tuple[int, int, int]): The color when hovered.
        thickness (int): The thickness of the button's border.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        font: Font,
        action_value: Optional[str] = None,
    ) -> None:
        """Initializes the Button instance.

        Args:
            x (int): The x-coordinate of the button.
            y (int): The y-coordinate of the button.
            width (int): The width of the button.
            height (int): The height of the button.
            text (str): The text to display.
            font (Font): The font object for rendering the text.
            action_value (Optional[str], optional):
            Data associated with the button.
                Defaults to None.
        """
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.text: str = text
        self.font: Font = font
        self.action_value: Optional[str] = action_value

        self.color_normal: tuple[int, int, int] = (60, 60, 60)
        self.color_hover: tuple[int, int, int] = (255, 255, 255)
        self.thickness: int = 3

    def draw(self, surface: pygame.Surface, offset_y: int = 0) -> None:
        """Draws the button onto the given surface, handling hover state.

        Args:
            surface (pygame.Surface): The Pygame surface to draw on.
            offset_y (int, optional): The vertical offset applied by scrolling.
                Defaults to 0.
        """
        draw_rect: pygame.Rect = self.rect.copy()
        draw_rect.y -= offset_y

        mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
        is_hovered: bool = self.rect.collidepoint(
            mouse_pos[0], mouse_pos[1] + offset_y
        )
        current_color: tuple[int, int, int] = (
            self.color_hover if is_hovered else self.color_normal
        )

        pygame.draw.rect(
            surface,
            current_color,
            draw_rect,
            width=self.thickness,
            border_radius=12,
        )

        text_surf: pygame.Surface = self.font.render(
            self.text, True, current_color
        )
        text_rect: pygame.Rect = text_surf.get_rect(center=draw_rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(
        self, event: pygame.event.Event, offset_y: int = 0
    ) -> bool:
        """Checks if the button is clicked based on mouse events.

        Args:
            event (pygame.event.Event): The Pygame event to check.
            offset_y (int, optional): The vertical offset applied by scrolling.
                Defaults to 0.

        Returns:
            bool: True if the left mouse button is clicked inside the button,
                False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            adjusted_pos: tuple[int, int] = (
                event.pos[0],
                event.pos[1] + offset_y,
            )
            if self.rect.collidepoint(adjusted_pos):
                return True
        return False


class Menu:
    """Manages the main menu UI, video background, and category/map navigation.

    Attributes:
        width (int): The screen width.
        height (int): The screen height.
        video (cv2.VideoCapture): Background video object.
        state (str): Current menu state ('CATEGORIES' or 'MAPS').
    """

    def __init__(self, width: int, height: int) -> None:
        """Initializes the Menu with dimensions and sets up UI elements.

        Args:
            width (int): The width of the application window.
            height (int): The height of the application window.
        """
        self.width: int = width
        self.height: int = height

        # Video
        self.video: cv2.VideoCapture = cv2.VideoCapture(
            "assets/final_drone.mp4"
        )
        self.total_frames: int = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.direction: int = 1

        # Fonts
        self.font_title: Font = pygame.font.SysFont("arial", 80, bold=True)
        self.font_btn: Font = pygame.font.SysFont("arial", 50)
        self.font_subtitle: Font = pygame.font.SysFont("arial", 25, bold=True)
        self.font_error: Font = pygame.font.SysFont("arial", 40, bold=True)

        # Error Handling
        self.error_msg: str = ""
        self.error_time: int = 0

        # Menu States
        self.state: str = "CATEGORIES"
        self.current_category: str = ""
        self.scroll_y: int = 0

        self.category_buttons: list[Button] = []
        self.map_buttons: list[Button] = []
        self.exit_btn: Optional[Button] = None
        self.exith_btn: Optional[Button] = None
        self.back_btn: Optional[Button] = None
        self.setup_categories()

    def set_error(self, message: str) -> None:
        """Triggers the display of a temporary error message.

        Args:
            message (str): The error text to display.
        """
        self.error_msg = message
        self.error_time = pygame.time.get_ticks()

    def setup_categories(self) -> None:
        """Creates and positions the category selection buttons."""
        self.category_buttons = []
        categories: list[str] = [
            "easy",
            "medium",
            "hard",
            "challenger",
            "custom",
        ]
        x, y, w, h = 200, 650, 950, 90
        for cat in categories:
            self.category_buttons.append(
                Button(x, y, w, h, cat, self.font_btn, cat))
            y += 120
        self.exith_btn = Button(325, 1280, 700, 120, "EXIT", self.font_btn)

    def load_maps_from_folder(self, category_name: str) -> tuple[bool, str]:
        """Loads available map files from a category folder.

        Args:
            category_name (str): The name of the category to load.

        Returns:
            tuple[bool, str]: A tuple containing a success boolean and an
                error or success message string.
        """
        self.map_buttons = []
        self.scroll_y = 0
        path: str = os.path.join("maps", category_name)

        self.back_btn = Button(190, 1300, 500, 90, "< BACK", self.font_btn)
        self.exit_btn = Button(940, 1300, 500, 90, "EXIT", self.font_btn)

        if not os.path.exists(path):
            return False, f"[Error]: Directory '{path}' not found!"

        files: list[str] = [f for f in os.listdir(path) if f.endswith(".txt")]
        files.sort()

        if not files:
            return False, f"[Error]: No .txt files found in '{category_name}'!"

        x, y, w, h = 200, 670, 1200, 90
        for f in files:
            self.map_buttons.append(Button(x, y, w, h, f, self.font_btn, f))
            y += 120

        return True, "Success"

    def update_video(self) -> Optional[pygame.Surface]:
        """Reads the next video frame and converts it to a Pygame Surface.

        Handles reversing video direction to create a seamless loop.

        Returns:
            Optional[pygame.Surface]: The current video frame as a surface,
                or None if the frame could not be read.
        """
        curr: int = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
        if curr >= self.total_frames - 1:
            self.direction = -1
        if curr <= 0:
            self.direction = 1

        ret: bool
        frame: Any

        ret, frame = self.video.read()
        if not ret:
            return None
        self.video.set(cv2.CAP_PROP_POS_FRAMES, curr + self.direction)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).swapaxes(0, 1)
        surf: pygame.Surface = pygame.surfarray.make_surface(frame)
        return pygame.transform.scale(surf, (self.width, self.height))

    def update(self, events: list[pygame.event.Event]) -> Optional[str]:
        """Updates the menu state, processing user events and scrolling.

        Args:
            events (list[pygame.event.Event]): A list of Pygame events.

        Returns:
            Optional[str]: The file path of the selected map, or None if
                no map has been selected yet.
        """
        max_scroll: int = 0
        if self.state == "MAPS" and len(self.map_buttons) > 0:
            last_btn_bottom: int = self.map_buttons[-1].rect.bottom
            max_scroll = max(0, last_btn_bottom - 1190)

        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                self.scroll_y -= event.y * 60
                self.scroll_y = max(0, min(self.scroll_y, max_scroll))

            if self.state == "CATEGORIES":
                for btn in self.category_buttons:
                    if btn.is_clicked(event):
                        self.current_category = str(btn.action_value)

                        success: bool
                        error_msg: str
                        success, error_msg = self.load_maps_from_folder(
                            self.current_category
                        )
                        if success:
                            self.state = "MAPS"
                        else:
                            self.set_error(error_msg)
                if self.exith_btn and self.exith_btn.is_clicked(event):
                    pygame.quit()
                    sys.exit()

            elif self.state == "MAPS":
                if self.back_btn and self.back_btn.is_clicked(event):
                    self.state = "CATEGORIES"
                if self.exit_btn and self.exit_btn.is_clicked(event):
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if 650 <= event.pos[1] <= 1210:
                        for btn in self.map_buttons:
                            if btn.is_clicked(event, self.scroll_y):
                                return os.path.join(
                                    "maps",
                                    self.current_category,
                                    str(btn.action_value),
                                )
        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Renders the video background, menus, buttons, and error messages.

        Args:
            screen (pygame.Surface): The main Pygame display surface.
        """
        video_surf: Optional[pygame.Surface] = self.update_video()
        if video_surf:
            screen.blit(video_surf, (0, 0))

        top_text_surf: pygame.Surface = self.font_subtitle.render(
            "CPIETRZA - POWERED BY: 42", True, (50, 50, 50)
        )
        screen.blit(top_text_surf, (2440, 1460))

        if self.state == "CATEGORIES":
            title_surf: pygame.Surface = self.font_title.render(
                "SELECT DIFFICULTY", True, (70, 75, 80)
            )
            screen.blit(title_surf, (200, 550))
            for btn in self.category_buttons:
                btn.draw(screen)
            if self.exith_btn:
                self.exith_btn.draw(screen)

        elif self.state == "MAPS":
            title_surf = self.font_title.render(
                f"MAPS: {self.current_category.upper()}", True, (70, 75, 80)
            )
            screen.blit(title_surf, (200, 550))

            bg_panel: pygame.Surface = pygame.Surface(
                (1280, 560), pygame.SRCALPHA
            )
            pygame.draw.rect(
                bg_panel, (127, 134, 144, 180), bg_panel.get_rect()
            )
            screen.blit(bg_panel, (160, 650))

            scroll_area: pygame.Rect = pygame.Rect(0, 650, self.width, 560)
            screen.set_clip(scroll_area)
            for btn in self.map_buttons:
                btn.draw(screen, self.scroll_y)
            screen.set_clip(None)

            if self.back_btn:
                self.back_btn.draw(screen)
            if self.exit_btn:
                self.exit_btn.draw(screen)

        # --- Display Error Message ---
        if self.error_msg:
            current_time: int = pygame.time.get_ticks()
            if current_time - self.error_time < 3000:
                lines: list[str] = self.error_msg.splitlines()
                for i, line in enumerate(lines):
                    surf: pygame.Surface = self.font_error.render(
                        line, True, (255, 255, 255)
                    )
                    bg_rect: pygame.Rect = surf.get_rect(
                        center=(self.width // 2, 60 + i * 70)
                    )
                    bg_rect.inflate_ip(40, 20)
                    pygame.draw.rect(
                        screen, (220, 50, 50), bg_rect, border_radius=10
                    )
                    screen.blit(surf, surf.get_rect(center=bg_rect.center))
            else:
                self.error_msg = ""
