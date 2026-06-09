import pygame
from PIL import Image
from PIL.Image import Image as PILImage


class GifConverter:
    def __init__(
        self, filename: str, size: tuple[int, int] | None = None
    ) -> None:
        self.filename: str = filename
        self.size: tuple[int, int] | None = size
        self.frames: list[pygame.Surface] = []
        self._load_frames()
        self.last_update: int = pygame.time.get_ticks()
        self.current_frame: int = 0

    def _load_frames(self) -> None:
        try:
            image: PILImage = Image.open(self.filename)
            for frame_index in range(getattr(image, 'n_frames', 1)):
                image.seek(frame_index)
                frame_rgba: PILImage = image.convert("RGBA")
                img_size: tuple[int, int] = frame_rgba.size
                data: bytes = frame_rgba.tobytes()
                surface: pygame.Surface = pygame.image.fromstring(data,
                                                                  img_size,
                                                                  "RGBA")

                if self.size:
                    surface = pygame.transform.smoothscale(surface, self.size)

                self.frames.append(surface)
        except Exception as e:
            print(f"Error loading GIF {self.filename}: {e}")
            surface = pygame.Surface((32, 32), pygame.SRCALPHA)
            surface.fill((255, 0, 255, 100))
            if self.size:
                surface = pygame.transform.scale(surface, self.size)
            self.frames.append(surface)

    def get_frame(self, speed_ms: int = 100) -> pygame.Surface:
        if not self.frames:
            return pygame.Surface((0, 0))

        now: int = pygame.time.get_ticks()
        if now - self.last_update > speed_ms:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_update = now

        return self.frames[self.current_frame]
