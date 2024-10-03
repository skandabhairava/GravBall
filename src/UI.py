import pygame
from typing import Callable
import audio_factory, helper

SCREEN_SIZE = (1300, 700)

button_width = 550
button_height = 50

normal_font = pygame.font.Font(helper.resource_path('font/Broadway.ttf'), 30)
semi_big_font = pygame.font.Font(helper.resource_path('font/Broadway.ttf'), 30 * 2)
big_font = pygame.font.Font(helper.resource_path('font/Broadway.ttf'), 30 * 4)
small_font = pygame.font.SysFont('Arial', 22)

NUMS: list[tuple[pygame.Surface, tuple[int, int]]] = []
BIG_NUMS: list[tuple[pygame.Surface, tuple[int, int]]] = []

COLON_SYMB = normal_font.render(':' , True , (255, 255, 255))
COLON_SYMB_SIZE = COLON_SYMB.get_size()

MAIN_TEXT = big_font.render('Grav Ball' , True , (255, 255, 255))
PAUSED_TEXT = big_font.render('Paused' , True , (255, 255, 255))
GAME_END_TEXT = big_font.render('Game Over' , True , (255, 255, 255))

COLOR_WHEEL: pygame.Surface
COLOR_WHEEL_RADIUS: int
KEYS_IMAGE: dict[int, tuple[pygame.Surface, Callable[[], None], Callable[[], None]]] = {}

set_anim_wall = 100
set_anim_ball_revol_mainmenu = 300
set_anim_ball_comeback = 100

# OPENGL
OPENGL_VIGNETTE_OPACITY = 1.0
OPENGL_BRIGHTNESS = 2

class Sprite:
    def __init__(self, 
                 image: pygame.Surface, 
                 center_func: Callable[[float, float], tuple[float, float]],
                 width_height: tuple[float, float],
                 is_text: bool
                 ) -> None:
        self.image: pygame.Surface = image
        self.size = self.image.get_size()
        self.center_func = center_func
        self.pos: tuple[float, float]
        self.is_text: bool = is_text

        self.resize(*width_height)

    @classmethod
    def import_image(
        cls,
        name: str,
        width_height_image: tuple[int, int], 
        center_func: Callable[[float, float], tuple[float, float]],
        width_height: tuple[float, float],
        ) -> 'Sprite':

        img = pygame.transform.scale(pygame.image.load(helper.resource_path(f"images/{name}")).convert_alpha(), width_height_image)
        return cls(img, center_func, width_height, False)

    def resize(self, width: float, height: float):
        center_pos = self.center_func(width, height)
        self.pos = (center_pos[0] - self.size[0]//2, center_pos[1] - self.size[1]//2)

    def draw(self, display: pygame.Surface):
        display.blit(self.image, self.pos)

    def scroll_draw(self, display: pygame.Surface, offset: tuple[float, float]=(0, 0)):
        display.blit(self.image, (self.pos[0] + offset[0], self.pos[1] + offset[1]))

class Button:
    def __init__(self,
                 text: str,
                 font: pygame.font.Font,
                 button_size: tuple[float, float],
                 center_func: Callable[[float, float], tuple[float, float]],
                 width_height: tuple[float, float],
                 callback: Callable[[], None],
                 global_button_click: list[bool]
                 ) -> None:
        
        self.text = font.render(text, True, (255, 255, 255))
        self.text_size = self.text.get_size()
        self.text_pos: tuple[float, float]
        self.center_func = center_func
        self.button_size = button_size
        self.callback = callback
        self.size: tuple[float, float]

        self.global_button_click: list[bool] = global_button_click

        self.resize(*width_height)

    def resize(self, width: float, height: float):
        bounding_box_tuple = self.center_func(width, height)
        self.bounding_box_rect = pygame.Rect((bounding_box_tuple[0] - self.button_size[0]//2, bounding_box_tuple[1] - self.button_size[1]//2), self.button_size)
        self.text_pos = (bounding_box_tuple[0] - self.text_size[0]//2, bounding_box_tuple[1] - self.text_size[1]//2)

        self.size = (self.bounding_box_rect.width, self.bounding_box_rect.height)

    def draw(self, display: pygame.Surface, disable:bool=False):
        color = (20, 20, 20)
        if self.bounding_box_rect.collidepoint(pygame.mouse.get_pos()):
            if pygame.mouse.get_pressed()[0] and not self.global_button_click[0] and not disable:
                self.global_button_click[0] = True
                self.callback()
                audio_factory.AUDIO_LIBRARY["BUTTON_CLICK"].play()
            else:
                color = (30, 30, 30)

        pygame.draw.rect(display, color, self.bounding_box_rect)
        display.blit(self.text, self.text_pos)

    def scroll_draw(self, display: pygame.Surface, disable:bool=False, offset: tuple[float, float]=(0, 0)):
        color = (20, 20, 20)
        if self.bounding_box_rect.move(offset).collidepoint(pygame.mouse.get_pos()):
            if pygame.mouse.get_pressed()[0] and not self.global_button_click[0] and not disable:
                self.global_button_click[0] = True
                self.callback()
                audio_factory.AUDIO_LIBRARY["BUTTON_CLICK"].play()
            else:
                color = (30, 30, 30)

        pygame.draw.rect(display, color, self.bounding_box_rect.move(offset))
        display.blit(self.text, (self.text_pos[0] + offset[0], self.text_pos[1] + offset[1]))

class Animation:
    def __init__(self, min_: int, max_: int, speed: int = 1) -> None:
        self.min: int = min_
        self.max: int = max_
        self.frame: int|float = min_
        self.speed: int = speed
        self.message = None

    def update_add(self, delta, clamp: bool=False, wrap: bool=False):
        #assert clamp ^ wrap or not (clamp or wrap)

        val = delta * self.speed

        if clamp:
            if (self.frame + val) > self.max:
                self.frame = self.max
                return
            elif (self.frame + val) < self.min:
                self.frame = self.min
                return
        elif wrap:
            if (self.frame + val) > self.max:
                self.frame = self.min
                return
            elif (self.frame + val) < self.min:
                self.frame = self.max
                return

        self.frame += val

    def wrap(self):
        if self.frame > self.max:
            self.frame = self.min
        elif self.frame < self.min:
            self.frame = self.max

    def clamp(self):
        if self.frame > self.max:
            self.frame = self.max
        elif self.frame < self.min:
            self.frame = self.min

    def is_playing_within_top(self):
        return self.frame < self.max
    
    def is_playing_after_down(self):
        return self.frame > self.min

    def is_playing(self):
        return self.frame < self.max and self.frame > self.min

    def set_message(self, msg, delta=0.0):
        self.message = msg
        self.update_add(delta)

def multiple_texts(text:str, font: pygame.font.Font) -> pygame.Surface:
    renders: list[pygame.Surface] = []
    for line in text.split("\n"):
        renders.append(font.render(line, True, (255, 255, 255)))

    space_in_between = 5

    max_width: float = max(renders, key=lambda render: render.get_size()[0]).get_size()[0]
    max_height: float = sum([render.get_size()[1] + space_in_between for render in renders]) - space_in_between
    final_text = pygame.Surface((max_width, max_height), pygame.SRCALPHA)

    height = 0

    for line in renders:
        final_text.blit(line, (0, height))
        height += line.get_size()[1] + space_in_between

    return final_text

class ScrollableWindow:
    def __init__(self, items: list[Sprite|Button], width_height: tuple[float, float]) -> None:
        self.items: list[Sprite|Button] = items
        self.scroll_length = 0
        self.first_scroll = 0
        self.last_scroll = -1
        self.resize(*width_height)

    def resize(self, width, height):

        for item in self.items:
            item.resize(width, height)

        match self.items:
            case [val, *_] if isinstance(val, Sprite):
                if self.scroll_length == self.first_scroll:
                    self.scroll_length = self.first_scroll = int(val.pos[1] - 50)
                else:
                    self.first_scroll = int(val.pos[1] - 50)

        total_height = 0
        for i in range(0, len(self.items)-1):
            curr_item = self.items[i]
            next_item = self.items[i+1]
            
            total_height += curr_item.size[1]//2 + next_item.size[1]//2 + 20

        if self.scroll_length == self.last_scroll and len(self.items) > 0:
            self.scroll_length = self.last_scroll = int(total_height) - height//2 + self.items[-1].size[1]//2 + 50
        elif len(self.items) > 0:
            self.last_scroll = int(total_height) - height//2 + self.items[-1].size[1]//2 + 50
        
        self.scroll(0)

    def scroll(self, amt: int) -> None:
        if (self.scroll_length + amt) < self.first_scroll:
            self.scroll_length = self.first_scroll
            return
        
        if (self.scroll_length + amt) > self.last_scroll:
            self.scroll_length = self.last_scroll
            return
        
        self.scroll_length += amt

    def draw(self, display: pygame.Surface):
        total_height = 0
        left_align_pos = 0
        
        match self.items:
            case [val, *_] if isinstance(val, Sprite) and val.is_text:
                left_align_pos = val.pos[0]

        for i in range(0, len(self.items)-1):
            curr_item = self.items[i]
            next_item = self.items[i+1]
            
            if isinstance(curr_item, Sprite) and curr_item.is_text:
                curr_item.scroll_draw(display, offset=(-curr_item.pos[0] + left_align_pos, total_height - self.scroll_length))
            else:
                curr_item.scroll_draw(display, offset=(0, total_height - self.scroll_length))

            total_height += curr_item.size[1]//2 + next_item.size[1]//2 + 20

        match self.items:
            case [*_, val]:
                if isinstance(val, Sprite):
                    val.scroll_draw(display, offset=(-val.pos[0] + left_align_pos, total_height - self.scroll_length))
                elif isinstance(val, Button):
                    val.scroll_draw(display, offset=(0, total_height - self.scroll_length))

def hue_to_rbg(p, q, t):
    if t < 0: t += 1
    if t > 1: t -= 1
    if t < 1/6: return p + (q - p) * 6 * t
    if t < 1/2: return q
    if t < 2/3: return p + (q - p) * (2/3 - t) * 6

    return p

def find_opp_color(color: pygame.Color) -> pygame.Color:
    h, s, l, a = color.hsla
    h += 190
    #if h > 360: h-=360

    h /= 360
    s /= 100
    l /= 100

    r, g, b = 0, 0, 0
    if s == 0:
        r = g = b = l
        return pygame.Color(round(r * 255), round(g * 255), round(b * 255))
    
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    r = hue_to_rbg(p, q, h + 1/3)
    g = hue_to_rbg(p, q, h)
    b = hue_to_rbg(p, q, h - 1/3)

    return pygame.Color(round(r * 255), round(g * 255), round(b * 255))

""" def rot_center(image, angle, x, y):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center = image.get_rect(center = (x, y)).center)
    return rotated_image, new_rect.center """

# used to load in images after starting up window, otherwise pygame wont allow
def define(pygame_map: dict[str, tuple[int, Callable[[],None], Callable[[], None]]]):
    global COLOR_WHEEL, COLOR_WHEEL_RADIUS
    COLOR_WHEEL = pygame.transform.scale(pygame.image.load(helper.resource_path("images/colorwheel.png")).convert_alpha(), (400, 400))
    COLOR_WHEEL_RADIUS = COLOR_WHEEL.get_width()//2

    for key_id, key_val in pygame_map.items():
        key = pygame.image.load(helper.resource_path(f"images/keys/{key_id}_KEY.png")).convert_alpha()
        key = pygame.transform.scale(key, (78, 78))
        key.set_alpha(50)
        KEYS_IMAGE[key_val[0]] = key, key_val[1], key_val[2]

    for i in range(0, 10):
        num = normal_font.render(str(i), True, (255, 255, 255))
        num_size = num.get_size()
        NUMS.append((num, num_size))

    for i in range(0, 10):
        num = semi_big_font.render(str(i), True, (255, 255, 255))
        num_size = num.get_size()
        BIG_NUMS.append((num, num_size))

