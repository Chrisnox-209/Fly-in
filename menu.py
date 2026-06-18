import os
import sys
import cv2  # type: ignore[import-untyped, unused-ignore]
import pygame
from typing import Optional

from pygame.font import Font


class Menu:
    """Manages the main menu UI, background video, and map navigation.

    Uses an immediate-mode GUI approach to render buttons and handle clicks
    simultaneously, reducing class complexity.
    """

    def __init__(self, width: int, height: int) -> None:
        """Initializes the Menu with dimensions and sets up UI elements.

        Args:
            width (int): The screen width.
            height (int): The screen height.
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
        self.font_sub: Font = pygame.font.SysFont("arial", 25, bold=True)
        self.font_err: Font = pygame.font.SysFont("arial", 40, bold=True)

        # State
        self.state: str = "CATEGORIES"
        self.category: str = ""
        self.scroll_y: int = 0
        self.map_files: list[str] = []
        self.cats: list[str] = [
            "easy", "medium", "hard", "challenger", "custom"
        ]

        # Error handling
        self.error_msg: str = ""
        self.error_time: int = 0

        # Interaction
        self._selected: Optional[str] = None
        self._events: list[pygame.event.Event] = []

    def update(self, events: list[pygame.event.Event]) -> Optional[str]:
        """Processes events and scrolling.

        Args:
            events (list[pygame.event.Event]): A list of Pygame events.

        Returns:
            Optional[str]: The file path of the selected map, or None.
        """
        ret: Optional[str] = self._selected
        self._selected = None
        self._events = events

        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                max_scroll: int = (
                    max(0, len(self.map_files) * 120 + 670 - 1190)
                    if self.state == "MAPS"
                    else 0
                )
                self.scroll_y -= event.y * 60
                self.scroll_y = max(0, min(self.scroll_y, max_scroll))

        return ret

    def _btn(
        self,
        screen: pygame.Surface,
        text: str,
        rect: pygame.Rect,
        offset: int = 0,
    ) -> bool:
        """Draws an immediate-mode button and detects clicks.

        Args:
            screen (pygame.Surface): The surface to draw on.
            text (str): The button text.
            rect (pygame.Rect): The bounding box of the button.
            offset (int, optional): Scroll offset. Defaults to 0.

        Returns:
            bool: True if clicked this frame, False otherwise.
        """
        r: pygame.Rect = rect.copy()
        r.y -= offset

        hover: bool = r.collidepoint(pygame.mouse.get_pos())
        c: tuple[int, int, int] = (255, 255, 255) if hover else (60, 60, 60)
        color: tuple[int, int, int] = c

        pygame.draw.rect(screen, color, r, width=3, border_radius=12)
        txt: pygame.Surface = self.font_btn.render(text, True, color)
        screen.blit(txt, txt.get_rect(center=r.center))

        for event in self._events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if r.collidepoint(event.pos):
                    return True
        return False

    def _draw_video(self, screen: pygame.Surface) -> None:
        """Advances and draws the looping background video."""
        curr: int = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
        if curr >= self.total_frames - 1:
            self.direction = -1
        if curr <= 0:
            self.direction = 1

        ret, frame = self.video.read()
        if ret:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, curr + self.direction)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).swapaxes(0, 1)
            surf: pygame.Surface = pygame.surfarray.make_surface(frame)
            surf = pygame.transform.scale(surf, (self.width, self.height))
            screen.blit(surf, (0, 0))

    def set_error(self, msg: str) -> None:
        """Triggers an error message."""
        self.error_msg = msg
        self.error_time = pygame.time.get_ticks()

    def draw(self, screen: pygame.Surface) -> None:
        """Renders the video background, menus, buttons, and errors.

        Args:
            screen (pygame.Surface): The main display surface.
        """
        self._draw_video(screen)

        sub: pygame.Surface = self.font_sub.render(
            "CPIETRZA - POWERED BY: 42", True, (50, 50, 50)
        )
        screen.blit(sub, (2440, 1460))

        title_color: tuple[int, int, int] = (70, 75, 80)

        if self.state == "CATEGORIES":
            screen.blit(
                self.font_title.render(
                    "SELECT DIFFICULTY", True, title_color
                ),
                (200, 550),
            )
            for i, cat in enumerate(self.cats):
                rect = pygame.Rect(200, 650 + i * 120, 950, 90)
                if self._btn(screen, cat, rect):
                    path: str = os.path.join("maps", cat)
                    if os.path.exists(path):
                        files: list[str] = [
                            f for f in os.listdir(path) if f.endswith(".txt")
                        ]
                        if files:
                            self.map_files = sorted(files)
                            self.category = cat
                            self.state = "MAPS"
                            self.scroll_y = 0
                        else:
                            self.set_error(f"[Error]: No .txt in '{cat}'!")
                    else:
                        msg = f"[Error]: Directory '{path}' not found!"
                        self.set_error(msg)

            if self._btn(screen, "EXIT", pygame.Rect(325, 1280, 700, 120)):
                pygame.quit()
                sys.exit()

        elif self.state == "MAPS":
            title: str = f"MAPS: {self.category.upper()}"
            screen.blit(
                self.font_title.render(title, True, title_color), (200, 550)
            )

            bg = pygame.Surface((1280, 560), pygame.SRCALPHA)
            pygame.draw.rect(bg, (127, 134, 144, 180), bg.get_rect())
            screen.blit(bg, (160, 650))

            screen.set_clip(pygame.Rect(0, 650, self.width, 560))
            for i, f in enumerate(self.map_files):
                rect = pygame.Rect(200, 670 + i * 120, 1200, 90)
                if self._btn(screen, f, rect, self.scroll_y):
                    self._selected = os.path.join("maps", self.category, f)
            screen.set_clip(None)

            if self._btn(screen, "< BACK", pygame.Rect(190, 1300, 500, 90)):
                self.state = "CATEGORIES"
            if self._btn(screen, "EXIT", pygame.Rect(940, 1300, 500, 90)):
                pygame.quit()
                sys.exit()

        if self.error_msg:
            if pygame.time.get_ticks() - self.error_time < 3000:
                lines: list[str] = self.error_msg.splitlines()
                for i, line in enumerate(lines):
                    err: pygame.Surface = self.font_err.render(
                        line, True, (255, 255, 255))
                    br: pygame.Rect = err.get_rect(
                        center=(self.width // 2, 60 + i * 70)
                    ).inflate(40, 20)
                    pygame.draw.rect(
                        screen, (220, 50, 50), br, border_radius=10
                    )
                    screen.blit(err, err.get_rect(center=br.center))
            else:
                self.error_msg = ""
