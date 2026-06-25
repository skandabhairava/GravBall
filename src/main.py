#!/usr/bin/env python3
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame, json, math, moderngl, array, random
from enum import Enum
pygame.init()

import UI, audio_factory
from camera import CameraSystem
from gameplay import Gameplay, PowerUp
from pygame.math import Vector2
from phybody import Body
import phybody
import userevents, helper

class States(Enum):
    MAIN_MENU_S = 0
    GAME_SCREEN_S = 1
    PAUSE_MENU_S = 2
    OPTION_MENU_S = 3
    GAME_END_S = 4
    ABOUT_S = 5

class GravClient:
    def __init__(self, SET_FPS: int) -> None:
        self.SET_FPS = SET_FPS
        self.FPS = SET_FPS
        self.delta = 0

        self.player_config: dict[str, str|list[int]|int|float]
        try:
            with open("player_config.json", "r") as config:
                self.player_config = json.loads(config.read())
        except FileNotFoundError:
            self.fix_broken_config()

        if not isinstance(self.player_config["volume"], float|int):
            print(">> GAME: 'volume' in player_config should be a float or int value")
            return
        audio_factory.set_volume(self.player_config["volume"])

        self.left_color = pygame.Color(self.player_config["color"][0], self.player_config["color"][1], self.player_config["color"][2]) # type: ignore
        self.left_color_ball: pygame.Color
        self.left_color_wall: pygame.Color
        self.right_color = pygame.Color(self.player_config["opposite_color"][0], self.player_config["opposite_color"][1], self.player_config["opposite_color"][2]) # type: ignore
        self.right_color_ball: pygame.Color
        self.right_color_wall: pygame.Color
        self.set_colors()

        self.clock = pygame.time.Clock()

        # SCREEN STATE:
        # 0 => Main Menu
        # 1 => GAME SCREEN
        # 2 => Pause menu
        # 3 => Options
        # 4 => GameWon

        self.STATE: States = States.MAIN_MENU_S
        self.global_button_click = [False]

        """ self.bodies: list[Body] = [
            Body(0, True, (255, 0, 0), 50, 100, Vector2(-300, 0), Vector2(0, 0)),
            Body(1, True, (0, 255, 0), 50, 100, Vector2(300, 0), Vector2(0, 0)),
            Body(2, False, (0, 0, 255), 20, 50, Vector2(0, 0), Vector2(0, 0)),
        ] """

        self.window_title = "Grav Ball"

        if not isinstance(self.player_config["postprocess"], int):
            print(">> GAME: 'postprocess' in player_config should be an integer value. 0 -> to disable, any other int -> enable")
            exit()
        self.postprocess = bool(self.player_config["postprocess"])
        self.window: pygame.Surface
        if self.postprocess:
            # enable OPEN GL and load a bunch of other stuff
            self.postprocess_enable()
            self.base_color = (85, 60, 143)
        else:
            self.base_color = (0, 0, 0)
            self.window = pygame.display.set_mode(UI.SCREEN_SIZE, pygame.RESIZABLE | pygame.DOUBLEBUF)
            self.main_display = pygame.Surface(self.window.get_size())

        pygame.display.set_caption("Grav Ball")

        self.ball = Body(1, False, pygame.Color(255, 255, 255), Vector2(0, 0), Vector2(0, 0), 20, 50)
        self.left_player = Body(2, True, self.left_color_ball, Vector2(-250, 0), Vector2(0, 0))
        self.right_player = Body(3, True, self.right_color_ball, Vector2(250, 0), Vector2(0, 0))
        
        self.bodies: list[Body] = [
            self.left_player, 
            self.right_player,
            self.ball
        ]

        self.coins: list[phybody.Coin] = []

        self.acceleration = 0.2

        pygame_map = {
            "W": (pygame.K_w, lambda: self.left_player.add_mouse_y(self.acceleration), lambda: self.left_player.add_mouse_y(-self.acceleration)),
            "A": (pygame.K_a, lambda: self.left_player.add_mouse_x(-self.acceleration), lambda: self.left_player.add_mouse_x(self.acceleration)),
            "S": (pygame.K_s, lambda: self.left_player.add_mouse_y(-self.acceleration), lambda: self.left_player.add_mouse_y(self.acceleration)),
            "D": (pygame.K_d, lambda: self.left_player.add_mouse_x(self.acceleration), lambda: self.left_player.add_mouse_x(-self.acceleration)),
            "UP": (pygame.K_UP, lambda: self.right_player.add_mouse_y(self.acceleration), lambda: self.right_player.add_mouse_y(-self.acceleration)),
            "DOWN": (pygame.K_DOWN, lambda: self.right_player.add_mouse_y(-self.acceleration), lambda: self.right_player.add_mouse_y(self.acceleration)),
            "LEFT": (pygame.K_LEFT, lambda: self.right_player.add_mouse_x(-self.acceleration), lambda: self.right_player.add_mouse_x(self.acceleration)),
            "RIGHT": (pygame.K_RIGHT, lambda: self.right_player.add_mouse_x(self.acceleration), lambda: self.right_player.add_mouse_x(-self.acceleration))
        }

        UI.define(pygame_map)
        self.running = False

        width, height = self.main_display.get_size()
        self.buttons = {
            "OPTION_EXIT": UI.Button("Exit", UI.normal_font, (UI.button_width // 2.5, UI.button_height), lambda width, height: ((width//2 - 200, height//2 + 200)), (width, height), self.option_exit_clicked, self.global_button_click),
            "OPTION_SAVE_EXIT": UI.Button("Save & Exit", UI.normal_font, (UI.button_width // 2.5, UI.button_height), lambda width, height: (width//2 + 200, height//2 + 200), (width, height), self.option_save_exit_clicked, self.global_button_click),
            "PAUSE_END": UI.Button("End Game", UI.normal_font, (UI.button_width, UI.button_height), lambda width, height: (width//2, height//2 + 160), (width, height), lambda: self.transition.set_message(States.MAIN_MENU_S, self.delta), self.global_button_click),
            "MAIN_START": UI.Button("Start Game", UI.normal_font, (UI.button_width, UI.button_height), lambda width, height: (width//2, height//2 + 20), (width, height), lambda: self.transition.set_message(States.GAME_SCREEN_S, self.delta), self.global_button_click),
            "MAIN_OPTION": UI.Button("Options", UI.normal_font, (UI.button_width, UI.button_height), lambda width, height: (width//2, height//2 + 90), (width, height), lambda: self.change_state(States.OPTION_MENU_S), self.global_button_click),
            "MAIN_ABOUT": UI.Button("About", UI.normal_font, (UI.button_width, UI.button_height), lambda width, height: (width//2, height//2 + 160), (width, height), lambda: self.change_state(States.ABOUT_S), self.global_button_click),
            "WIN_END": UI.Button("Back to Menu", UI.normal_font, (UI.button_width, UI.button_height), lambda width, height: (width//2, height//2 + 150), (width, height), lambda: self.transition.set_message(States.MAIN_MENU_S, self.delta), self.global_button_click)
        }

        self.sprites = {
            "LEFT_CROWN": UI.Sprite.import_image("left_crown.png", (300, 300), lambda width, height: (width//2 - 250, height//2 - 20), (width, height)),
            "RIGHT_CROWN": UI.Sprite.import_image("right_crown.png", (300, 300), lambda width, height: (width//2 + 250, height//2 - 20), (width, height)),
            "COLOR_WHEEL": UI.Sprite(UI.COLOR_WHEEL, lambda width, height: (width//2 + 200, height//2 - 100), (width, height), False),
            "MAIN_TEXT": UI.Sprite(UI.MAIN_TEXT, lambda width, height: (width//2, height//2 - 200), (width, height), True),
            "PAUSE_TEXT": UI.Sprite(UI.PAUSED_TEXT, lambda width, height: (width//2, height//2 - 200), (width, height), True),
            "GAME_END_TEXT": UI.Sprite(UI.GAME_END_TEXT, lambda width, height: (width//2, height//2 - 200), (width, height), True),
        }
        self.power_up_sprites = {
            PowerUp.Quantum: pygame.transform.scale(pygame.image.load(helper.resource_path(f"images/powerups/quantum.png")).convert_alpha(), (100, 100)),
            PowerUp.Grow: pygame.transform.scale(pygame.image.load(helper.resource_path(f"images/powerups/grow.png")).convert_alpha(), (100, 100)),
            PowerUp.SpeedUp: pygame.transform.scale(pygame.image.load(helper.resource_path(f"images/powerups/speed.png")).convert_alpha(), (100, 100)),
            PowerUp.AntiGravity: pygame.transform.scale(pygame.image.load(helper.resource_path(f"images/powerups/antigravity.png")).convert_alpha(), (100, 100)),
        }

        self.about_text = UI.ScrollableWindow([
            UI.Sprite(UI.multiple_texts(helper.ABOUT0, UI.normal_font), lambda width, height: (width//2-50, height//2), (width, height), True),
            UI.Sprite(UI.multiple_texts(helper.ABOUT1, UI.small_font), lambda width, height: (width//2, height//2), (width, height), True),
            UI.Sprite.import_image("gravity_formula.png", (332, 167), lambda width, height: (width//2, height//2), (width, height)),
            UI.Sprite(UI.multiple_texts(helper.ABOUT2, UI.small_font), lambda width, height: (width//2, height//2), (width, height), True),
            UI.Sprite(UI.multiple_texts(helper.ABOUT3, UI.small_font), lambda width, height: (width//2, height//2), (width, height), True),
            UI.Sprite(self.power_up_sprites[PowerUp.SpeedUp], lambda width, height: (width//2, height//2), (width, height), False),
            UI.Sprite(UI.multiple_texts(helper.ABOUT3_speed, UI.small_font), lambda width, height: (width//2, height//2), (width, height), True),
            UI.Sprite(self.power_up_sprites[PowerUp.Grow], lambda width, height: (width//2, height//2), (width, height), False),
            UI.Sprite(UI.multiple_texts(helper.ABOUT3_grow, UI.small_font), lambda width, height: (width//2, height//2), (width, height), True),
            UI.Sprite(self.power_up_sprites[PowerUp.AntiGravity], lambda width, height: (width//2, height//2), (width, height), False),
            UI.Sprite(UI.multiple_texts(helper.ABOUT3_antigrav, UI.small_font), lambda width, height: (width//2, height//2), (width, height), True),
            UI.Sprite(self.power_up_sprites[PowerUp.Quantum], lambda width, height: (width//2, height//2), (width, height), False),
            UI.Sprite(UI.multiple_texts(helper.ABOUT3_quantum, UI.small_font), lambda width, height: (width//2, height//2), (width, height), True),
            UI.Sprite.import_image("uncertainity.png", (337, 149), lambda width, height: (width//2, height//2), (width, height)),
            UI.Sprite(UI.multiple_texts(helper.ABOUT4, UI.small_font), lambda width, height: (width//2, height//2), (width, height), True),
            UI.Button("Back to Menu", UI.normal_font, (UI.button_width, UI.button_height), lambda width, height: (width//2, height//2), (width, height), lambda: self.change_state(States.MAIN_MENU_S), self.global_button_click)
        ], (width, height))

        self.top_void = 3000
        self.bottom_void = -self.top_void
        self.left_void = -5000
        self.right_void = -self.left_void
        self.left_court_size = 500
        self.right_court_size = self.left_court_size

        self.left_power_anim = UI.Animation(0, 100, (6))
        self.right_power_anim = UI.Animation(0, 100, (6))
        self.coin_boost = 60*20

        self.left_screen = pygame.Surface((width//2, height))
        self.left_rect = self.left_screen.get_bounding_rect()
        self.right_screen = pygame.Surface((width//2, height))
        self.right_rect = self.right_screen.get_bounding_rect()

        self.pause_window = pygame.Surface((width, height))
        #self.pause_window.fill((0, 0, 0))

        self.pause_screen = pygame.Surface((width, height))
        self.pause_screen.set_alpha(128)
        self.pause_screen.fill((128, 128, 128))

        self.left_cam = CameraSystem((self.left_player.pos.x, self.left_player.pos.y), 1, (width//2, height))
        self.right_cam = CameraSystem((self.right_player.pos.x, self.right_player.pos.y), 1, (width//2, height))

        self.minimap_height = 100
        minimap_aspect_ratio = (self.right_void - self.left_void)/(self.top_void - self.bottom_void) #width/height
        self.minimap_width = self.minimap_height * minimap_aspect_ratio
        self.center_cam = CameraSystem((0, 0), self.minimap_height/(self.top_void-self.bottom_void), (self.minimap_width, self.minimap_height))
        self.center_screen = pygame.Surface((self.minimap_width, self.minimap_height))

        self.anim = pygame.Surface((width, height))
        self.half_anim = pygame.Surface((width//2, height))

        self.transition_screen = pygame.Surface((width, height))
        self.transition = UI.Animation(0, 100, (60 * 6))
        self.transition_screen.fill((0, 0, 0))

        self.game_anims = UI.Animation(0, UI.set_anim_wall, (60 * 2))
        self.anim_ball_revol_mainmenu = UI.Animation(0, UI.set_anim_ball_revol_mainmenu, (60))
        self.anim_ball_comeback = UI.Animation(0, UI.set_anim_ball_comeback, 60)

        if not isinstance(self.player_config["game_time"], int):
            print(">> GAME: 'game_time' in player config should be an integer < 3600")
            exit()
        self.gameplay = Gameplay(self.player_config["game_time"], userevents.WINNER_DECLARED, userevents.POWER_UP_GAIN_EVENT, userevents.POWER_UP_DESTROY_EVENT)
        #self.gameplay = Gameplay(15, WINNER_DECLARED)

        self.input_keys = UI.KEYS_IMAGE
        self.LEFT_DPAD = pygame.Surface((254, 166))
        self.LEFT_DPAD.set_colorkey(self.base_color)

        self.RIGHT_DPAD = pygame.Surface((254, 166))
        self.RIGHT_DPAD.set_colorkey(self.base_color)

        self.blit_dpads()

        #self.lock = threading.Lock()

    def fix_broken_config(self):
        self.player_config = {
                "color": [228, 93, 37],
                "opposite_color": [37, 140, 228],
                "postprocess": 1,
                "volume": 0.1,
                "game_time": 1200
            }
        with open("player_config.json", "w") as config:
            config.write(json.dumps(self.player_config))

    def postprocess_enable(self):
        self.window = pygame.display.set_mode(UI.SCREEN_SIZE, pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.main_display = pygame.Surface(self.window.get_size())
        self.opengl_ctx = moderngl.create_context()
        self.quad_buffer = self.opengl_ctx.buffer(data=array.array('f', [
            #position (x, y), uv coords (x, y)
            -1.0,  1.0, 0.0, 0.0, # top left
             1.0,  1.0, 1.0, 0.0, # top right
            -1.0, -1.0, 0.0, 1.0, # bottom left
             1.0, -1.0, 1.0, 1.0  # bottom right
        ]))
        with open(helper.resource_path("shaders/shader.frag"), "r") as fragment:
            fragment_shader = fragment.read()
        with open(helper.resource_path("shaders/shader.vert"), "r") as vert:
            vertex_shader = vert.read()

        self.opengl_program = self.opengl_ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        self.opengl_renderer = self.opengl_ctx.vertex_array(self.opengl_program, [(self.quad_buffer, '2f 2f', 'vert', 'texcoord')])

        # OPENGL EFFECTS UNIFORMS
        self.opengl_program['tex'] = 0
        self.opengl_program['curvature'] = 4.0, 3.0
        self.opengl_program['scanLineOpacity'] = 0.05, 0.05
        self.opengl_program['screenResolution'] = self.window.get_size()
        self.opengl_program['vignetteRoundness'] = 2.0
        self.opengl_program['bigScanLineOpacity'] = 0.01
        self.opengl_program['vignetteOpacity'] = UI.OPENGL_VIGNETTE_OPACITY
        self.opengl_program['brightness'] = UI.OPENGL_BRIGHTNESS

    def surface_to_texture(self, surface: pygame.Surface) -> moderngl.Texture:
        tex = self.opengl_ctx.texture(surface.get_size(), 4)
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        tex.swizzle = 'BGRA'
        tex.write(surface.get_view('1'))
        return tex

    def quit(self):
        pygame.mixer.stop()
        print(">> GAME: SHUTTING DOWN")

    def change_state(self, new_state: States) -> None:
        # SCREEN STATE:
        # 0 => Main Menu
        # 1 => GAME SCREEN
        # 2 => Pause menu
        # 3 => Options
        # 4 => GameWon

        match new_state:

            case States.PAUSE_MENU_S: #if self.STATE == States.GAME_SCREEN_S: #pause #commenting this line, as u can only pause from the game screen
                pygame.time.set_timer(userevents.GAME_TICK_SECOND, 0)
                self.pause_window.blit(self.main_display, (0, 0))
                self.pause_window.blit(self.pause_screen, (0, 0))

            ##########################################################################################################
            case States.GAME_SCREEN_S if self.STATE in (States.MAIN_MENU_S, States.OPTION_MENU_S):
                print(">> GAME: STARTED")
                pygame.mixer.stop()
                audio_factory.AUDIO_LIBRARY["GAME_LOOP"].play(-1)
                pygame.time.set_timer(userevents.GAME_TICK_SECOND, 1000)
                self.transition.set_message(None)

            case States.GAME_SCREEN_S if self.STATE == States.PAUSE_MENU_S: # unpause
                pygame.time.set_timer(userevents.GAME_TICK_SECOND, 1000)
            ##########################################################################################################

            case States.MAIN_MENU_S if self.STATE in (States.GAME_SCREEN_S, States.PAUSE_MENU_S, States.GAME_END_S):
                print(">> GAME: EXITED")
                self.reset_game()

                pygame.mixer.stop()
                audio_factory.AUDIO_LIBRARY["MAIN_MENU"].play(-1)
                pygame.time.set_timer(userevents.GAME_TICK_SECOND, 0)

                self.transition.set_message(None)
            ##########################################################################################################

            case States.GAME_END_S: #if self.STATE in (States.GAME_SCREEN_S, States.PAUSE_MENU_S): # commented this line, as GAME_END can only happen during GAME_SCREEN_S
                print(">> GAME: ENDED")
                pygame.mixer.stop()
                audio_factory.AUDIO_LIBRARY["MAIN_MENU"].play(-1)
                pygame.time.set_timer(userevents.GAME_TICK_SECOND, 0)
                self.transition.set_message(None)
            ##########################################################################################################

            case States.ABOUT_S:
                self.about_text.scroll_length = self.about_text.first_scroll

        self.STATE = new_state
    
    def set_colors(self):
        self.left_color_ball = self.left_color.correct_gamma(2)
        self.left_color_wall = self.left_color.correct_gamma(0.8)
        self.right_color_ball = self.right_color.correct_gamma(2)
        self.right_color_wall = self.right_color.correct_gamma(0.8)

    def blit_dpads(self):
        self.LEFT_DPAD = pygame.transform.scale_by(self.LEFT_DPAD, 2)
        self.LEFT_DPAD.fill(self.base_color)
        self.LEFT_DPAD.blit(self.input_keys[pygame.K_w][0], (254//2 - 78//2, 0))
        self.LEFT_DPAD.blit(self.input_keys[pygame.K_a][0], (0, 78+10))
        self.LEFT_DPAD.blit(self.input_keys[pygame.K_s][0], (254//2 - 78//2, 78+10))
        self.LEFT_DPAD.blit(self.input_keys[pygame.K_d][0], (254 - 78, 78+10))
        self.LEFT_DPAD = pygame.transform.scale_by(self.LEFT_DPAD, 0.5)

        self.RIGHT_DPAD = pygame.transform.scale_by(self.RIGHT_DPAD, 2)
        self.RIGHT_DPAD.fill(self.base_color)
        self.RIGHT_DPAD.blit(self.input_keys[pygame.K_UP][0], (254//2 - 78//2, 0))
        self.RIGHT_DPAD.blit(self.input_keys[pygame.K_LEFT][0], (0, 78+10))
        self.RIGHT_DPAD.blit(self.input_keys[pygame.K_DOWN][0], (254//2 - 78//2, 78+10))
        self.RIGHT_DPAD.blit(self.input_keys[pygame.K_RIGHT][0], (254 - 78, 78+10))
        self.RIGHT_DPAD = pygame.transform.scale_by(self.RIGHT_DPAD, 0.5)

    def reset_game(self):
        self.left_player.reset((-250, 0))
        #self.left_player.color = self.left_color_ball

        self.right_player.reset((250, 0))
        #self.right_player.color = self.right_color_ball

        self.ball.reset((0, 0))

        self.bodies: list[Body] = [
            self.left_player, 
            self.right_player,
            self.ball
        ]

        self.left_cam.reset((self.left_player.pos.x, self.left_player.pos.y))
        self.right_cam.reset((self.right_player.pos.x, self.right_player.pos.y))

        self.left_power_anim.frame = self.left_power_anim.min
        self.right_power_anim.frame = self.right_power_anim.min

        self.gameplay.reset()

    def resize(self, new_size: tuple[float, float]) -> None:
        width, height = new_size
        self.main_display = pygame.transform.scale(self.main_display, new_size)
        self.anim = pygame.transform.scale(self.anim, new_size)
        self.pause_screen = pygame.transform.scale(self.pause_screen, new_size)
        self.transition_screen = pygame.transform.scale(self.transition_screen, new_size)

        self.half_anim = pygame.transform.scale(self.half_anim, (width//2, height))
        
        self.left_screen = pygame.transform.scale(self.left_screen, (width//2, height))
        self.left_rect = self.left_screen.get_bounding_rect()
        self.right_screen = pygame.transform.scale(self.right_screen, (width//2, height))
        self.right_rect = self.right_screen.get_bounding_rect()

        self.left_cam.set_width_height((width//2, height))
        self.right_cam.set_width_height((width//2, height))

        for button in self.buttons.values():
            button.resize(width, height)

        for sprite in self.sprites.values():
            sprite.resize(width, height)

        self.about_text.resize(width, height)

        self.pause_window = pygame.transform.scale(self.pause_window, new_size)
        if self.STATE == States.PAUSE_MENU_S: # if paused
            self.game_draw(self.pause_window, width, height)
            self.pause_window.blit(self.pause_screen, (0, 0))

        if self.postprocess:
            self.opengl_program['screenResolution'] = new_size

    def draw_glow(self, cam: CameraSystem, display: pygame.Surface, player: Body, rect: pygame.Rect):
        body_pos = (cam.calc_pos_x(player.pos.x), cam.calc_pos_y(player.pos.y))
        if rect.collidepoint(body_pos):
            pygame.draw.circle(display, player.color, body_pos, max(player.size * cam.SCALE * (self.game_anims.frame * 0.03), player.size * cam.SCALE))

    def game_draw(self, display: pygame.Surface, width: float, height: float):
        self.left_screen.fill(self.base_color)
        self.right_screen.fill(self.base_color)        

        # setup animation
        self.half_anim.set_alpha(int((-200// self.game_anims.max ) * self.game_anims.frame) + 200)
        self.transition_screen.set_alpha(int(2.55 * self.transition.frame))

        self.left_cam.follow((self.left_player.pos.x, self.left_player.pos.y), self.delta)
        self.right_cam.follow((self.right_player.pos.x, self.right_player.pos.y), self.delta)

        self.left_cam.zoom(self.delta*0.5)
        self.right_cam.zoom(self.delta*0.5)

        for (cam, screen, rect) in ((self.left_cam, self.left_screen, self.left_rect), (self.right_cam, self.right_screen, self.right_rect)):
            left_void_pos =  cam.calc_pos_x(self.left_void)
            right_void_pos = cam.calc_pos_x(self.right_void)
            left_wall_pos = cam.calc_pos_x(self.left_void + self.left_court_size)
            right_wall_pos = cam.calc_pos_x(self.right_void - self.right_court_size)
            top_void_pos = cam.calc_pos_y(self.top_void)
            bottom_void_pos = cam.calc_pos_y(self.bottom_void)
            
            LEFT_WALL = (left_void_pos, 0, left_wall_pos-left_void_pos, height)
            RIGHT_WALL = (right_wall_pos, 0, right_void_pos - right_wall_pos, height)

            self.half_anim.fill(self.base_color)

            match self.gameplay.left_power:
                case (PowerUp.Grow, _):
                    self.draw_glow(cam, self.half_anim, self.left_player, rect)
            if (self.left_player.glow and not self.left_player.hidden):
                self.draw_glow(cam, self.half_anim, self.left_player, rect)

            match self.gameplay.right_power:
                case (PowerUp.Grow, _):
                    self.draw_glow(cam, self.half_anim, self.right_player, rect)
            if (self.right_player.glow and not self.right_player.hidden):
                self.draw_glow(cam, self.half_anim, self.right_player, rect)

            left_anim_wall_pos = cam.calc_pos_x(self.left_void + self.left_court_size + (self.game_anims.frame * 4))
            right_anim_wall_pos = cam.calc_pos_x(self.right_void - self.right_court_size - (self.game_anims.frame * 4))
            if left_anim_wall_pos > rect.left:
                pygame.draw.rect(self.half_anim, self.left_color_wall, (left_wall_pos, 0, left_anim_wall_pos-left_wall_pos, height))
            if right_anim_wall_pos < rect.right:
                pygame.draw.rect(self.half_anim, self.right_color_wall, (right_anim_wall_pos, 0, right_wall_pos-right_anim_wall_pos, height))

            screen.blit(self.half_anim, (0,0))    # draw animation onto screen

            if left_void_pos > rect.left:
                pygame.draw.rect(screen, (20, 20, 20), (0, 0, left_void_pos, height))
            if right_void_pos < rect.right:
                pygame.draw.rect(screen, (20, 20, 20), (right_void_pos, 0, width, height))
            if left_wall_pos > rect.left:
                pygame.draw.rect(screen, self.left_color_wall, LEFT_WALL)
            if right_wall_pos < rect.right:
                pygame.draw.rect(screen, self.right_color_wall, RIGHT_WALL)
            if top_void_pos > rect.top:
                pygame.draw.rect(screen, (20, 20, 20), (0, 0, width//2, top_void_pos))
            if bottom_void_pos < rect.bottom:
                pygame.draw.rect(screen, (20, 20, 20), (0, bottom_void_pos, width//2, height))

            for body in self.bodies:
                if body.hidden:
                    continue

                body_pos = (cam.calc_pos_x(body.pos.x), cam.calc_pos_y(body.pos.y))
                if rect.collidepoint(body_pos):
                    pygame.draw.circle(screen, body.color, body_pos, max(body.size * cam.SCALE, 2))

            for coin in self.coins:
                coin_pos = (cam.calc_pos_x(coin.pos.x), cam.calc_pos_y(coin.pos.y))
                if rect.collidepoint(coin_pos):
                    pygame.draw.circle(screen, (245, 189, 2), coin_pos, max(15 * cam.SCALE, 1))

        # draw on minimap
        self.center_screen.fill(self.base_color)
        left_void_pos =  self.center_cam.calc_pos_x(self.left_void)
        right_void_pos = self.center_cam.calc_pos_x(self.right_void)
        left_wall_pos = self.center_cam.calc_pos_x(self.left_void + self.left_court_size)
        right_wall_pos = self.center_cam.calc_pos_x(self.right_void - self.right_court_size)
        top_void_pos = self.center_cam.calc_pos_y(self.top_void)
        bottom_void_pos = self.center_cam.calc_pos_y(self.bottom_void)

        #print(left_void_pos, right_void_pos, left_wall_pos, right_wall_pos, top_void_pos, bottom_void_pos)
        
        LEFT_WALL = (left_void_pos, 0, left_wall_pos-left_void_pos, self.minimap_height)
        RIGHT_WALL = (right_wall_pos, 0, right_void_pos - right_wall_pos, self.minimap_height)

        pygame.draw.rect(self.center_screen, (20, 20, 20), (0, 0, left_void_pos, self.minimap_height))
        pygame.draw.rect(self.center_screen, (20, 20, 20), (right_void_pos, 0, self.minimap_width, self.minimap_height))
        pygame.draw.rect(self.center_screen, self.left_color_wall, LEFT_WALL)
        pygame.draw.rect(self.center_screen, self.right_color_wall, RIGHT_WALL)
        pygame.draw.rect(self.center_screen, (20, 20, 20), (0, 0, self.minimap_width, top_void_pos))
        pygame.draw.rect(self.center_screen, (20, 20, 20), (0, bottom_void_pos, self.minimap_width, self.minimap_height))

        for body in self.bodies:
            if body.hidden or body.is_clone:
                continue

            body_pos = (self.center_cam.calc_pos_x(body.pos.x), self.center_cam.calc_pos_y(body.pos.y))
            if body.is_player:
                pygame.draw.circle(self.center_screen, body.color, body_pos, 5)
            else:
                pygame.draw.circle(self.center_screen, body.color, body_pos, 3)
        for body in self.coins:
            body_pos = (self.center_cam.calc_pos_x(body.pos.x), self.center_cam.calc_pos_y(body.pos.y))
            pygame.draw.circle(self.center_screen, (245, 189, 2), body_pos, 1)

        if self.transition.message is None and self.transition.is_playing_after_down():
            self.transition.update_add(-self.delta, clamp=True)
        elif self.transition.message and self.transition.is_playing():
            self.transition.update_add(self.delta, clamp=True)

        display.blit(self.left_screen, (0, 0))
        display.blit(self.right_screen, (width//2, 0))
        pygame.draw.rect(display, (255, 255, 255), (width//2 - self.minimap_width//2 - 3, 17 + UI.COLON_SYMB_SIZE[1], self.minimap_width + 6, self.minimap_height+6))
        display.blit(self.center_screen, (width//2 - self.minimap_width//2, 20 + UI.COLON_SYMB_SIZE[1]))

        display.blit(self.LEFT_DPAD, (width//2 - (254 * 0.5) - 10, height - (78 * 2 + 10 + 20)*0.5))
        display.blit(self.RIGHT_DPAD, (width//2 + 10, height - (78 * 2 + 10 + 20)*0.5))

        #background for power-up bar
        pygame.draw.rect(display, (80, 80, 80), (50, height-50-10-30, width//2 - 180 - 30, 10))
        pygame.draw.rect(display, (80, 80, 80), (width - 50 - (width//2 - 180 - 30), height-50-10-30, width//2 - 180 - 30, 10))
        
        green = (250 - 120) * (self.left_power_anim.frame == self.left_power_anim.max) + 120
        pygame.draw.rect(
            display,
            (120, green, 120),
            (55, height-50-8-30, ((self.left_power_anim.frame/100) * (width//2 - 180 - 35 - 5)), 6)
        )
        
        green = (250 - 120) * (self.right_power_anim.frame == self.right_power_anim.max) + 120
        right_power_width = ((self.right_power_anim.frame/100) * (width//2 - 180 - 35 - 5))
        pygame.draw.rect(
            display,
            (120, green, 120),
            ((width - 55 - right_power_width), height-50-8-30, right_power_width, 6)
        )

        if self.gameplay.left_power:
            left_power = self.power_up_sprites.get(self.gameplay.left_power[0])
            if left_power:
                display.blit(left_power, (30, height - 100 - 30))
        if self.gameplay.right_power:
            right_power = self.power_up_sprites.get(self.gameplay.right_power[0])
            if right_power:
                display.blit(right_power, (width - 30 - 100, height - 100 - 30))

        # TIMER
        display.blit(UI.COLON_SYMB, (width//2 - UI.COLON_SYMB_SIZE[0]//2, 10))
        minute, sec = self.gameplay.timer_in_min_sec()
        
        min_0 = int(minute[0])
        min_1 = int(minute[1])
        display.blit(UI.NUMS[min_1][0], (width//2 - UI.COLON_SYMB_SIZE[0]//2 - 10 - UI.NUMS[min_1][1][0], 13))
        display.blit(UI.NUMS[min_0][0], (width//2 - UI.COLON_SYMB_SIZE[0]//2 - 10 - UI.NUMS[min_1][1][0] - 5 - UI.NUMS[min_0][1][0], 13))

        sec_0 = int(sec[0])
        sec_1 = int(sec[1])
        display.blit(UI.NUMS[sec_0][0], (width//2 + UI.COLON_SYMB_SIZE[0]//2 + 10, 13))
        display.blit(UI.NUMS[sec_1][0], (width//2 + UI.COLON_SYMB_SIZE[0]//2 + 10 + UI.NUMS[sec_0][1][0] + 5, 13))

        # SCORES
        score = f"{(self.gameplay.left_score):02}"
        score_0 = int(score[0])
        score_1 = int(score[1])
        display.blit(UI.BIG_NUMS[score_0][0], (40, 20))
        display.blit(UI.BIG_NUMS[score_1][0], (40 + UI.BIG_NUMS[score_0][1][0] + 10, 20))

        score = f"{(self.gameplay.right_score):02}"
        score_0 = int(score[0])
        score_1 = int(score[1])
        display.blit(UI.BIG_NUMS[score_1][0], (width - 40 - UI.BIG_NUMS[score_1][1][0], 20))
        display.blit(UI.BIG_NUMS[score_0][0], (width - 40 - UI.BIG_NUMS[score_1][1][0] - 10 - UI.BIG_NUMS[score_0][1][0], 20))

        pygame.draw.line(display, (255, 255, 255), (width//2, 17 + UI.COLON_SYMB_SIZE[1] + 5 + self.minimap_height), (width//2, height), 3)
        self.main_display.blit(self.transition_screen, (0, 0))

    def game_start_lobby_menu(self, width, height):
        if not self.transition.is_playing():
            self.ball.gravity_calc(self.bodies)

            for body in self.bodies:
                body.update(self.delta, (self.top_void, self.bottom_void, self.left_void, self.right_void), self.coins)

            #self.ball.update(self.delta, (self.top_void, self.bottom_void, self.left_void, self.right_void))

            self.game_anims.update_add(self.delta, wrap=True)

            if (self.ball.pos.x - self.ball.size) > (self.right_void - self.right_court_size):
                self.gameplay.right_score_add()
                self.ball.reset((0, 0))

            if (self.ball.pos.x + self.ball.size) < (self.left_void + self.right_court_size):
                self.gameplay.left_score_add()
                self.ball.reset((0, 0))

            self.left_power_anim.update_add(self.delta, clamp=True)
            self.right_power_anim.update_add(self.delta, clamp=True)

            if (self.left_power_anim.frame == self.left_power_anim.max) and not self.gameplay.left_power_allow:
                self.gameplay.left_power_allow = True
                audio_factory.AUDIO_LIBRARY["BEEP"].play()
            if (self.right_power_anim.frame == self.right_power_anim.max) and not self.gameplay.right_power_allow:
                self.gameplay.right_power_allow = True
                audio_factory.AUDIO_LIBRARY["BEEP"].play()

        if self.transition.message and not self.transition.is_playing():
            self.change_state(self.transition.message)

        self.game_draw(self.main_display, width, height)

    def pause_menu(self, width, height):
        self.main_display.blit(self.pause_window, (0, 0))

        self.transition_screen.set_alpha(int(2.55 * self.transition.frame))
        if self.transition.message is None and self.transition.is_playing_after_down():
            self.transition.update_add(-self.delta, clamp=True)
        elif self.transition.message and self.transition.is_playing():
            self.transition.update_add(self.delta, clamp=True)
        elif self.transition.message and not self.transition.is_playing():
            self.change_state(self.transition.message)


        self.sprites["PAUSE_TEXT"].draw(self.main_display)
        self.buttons["PAUSE_END"].draw(self.main_display, self.transition.is_playing())
        
        self.main_display.blit(self.transition_screen, (0, 0))

    def option_menu(self, width, height):

        mouse = pygame.mouse.get_pos()
        x, y = (
            (width//2 - 250 * ((1/self.anim_ball_comeback.max)*self.anim_ball_comeback.frame)) - 500 * math.cos((2*math.pi*self.anim_ball_revol_mainmenu.frame )/ self.anim_ball_revol_mainmenu.max) * ((-1/self.anim_ball_comeback.max)*self.anim_ball_comeback.frame + 1),
            (height//2 + 50 * ((-1/self.anim_ball_comeback.max)*self.anim_ball_comeback.frame + 1)) - 200 * math.sin((2*math.pi*self.anim_ball_revol_mainmenu.frame )/ self.anim_ball_revol_mainmenu.max) * ((-1/self.anim_ball_comeback.max)*self.anim_ball_comeback.frame + 1)
        )
        self.anim.set_alpha(int((-200// self.game_anims.max ) * self.game_anims.frame) + 200)                     # alpha level
        self.anim.fill(self.base_color)

        LEFT_WALL = pygame.Rect(-100, 0, min(width//2 - 500, 250), height + 100)
        RIGHT_WALL = pygame.Rect(width - min(width//2 - 600, 150), 0, width + 100, height + 100)

        COLOR_WHEEL_REGION_SQ = (Vector2(mouse) - Vector2(width//2 + 200, height//2 - 100)).length_squared()

        pygame.draw.rect(self.anim, self.left_color_wall, LEFT_WALL.move(self.game_anims.frame, 0))
        pygame.draw.rect(self.anim, self.right_color_wall, RIGHT_WALL.move(-self.game_anims.frame, 0))
        self.main_display.blit(self.anim, (0,0))    # (0,0) are the top-left coordinates

        pygame.draw.rect(self.main_display, self.left_color_wall, LEFT_WALL)
        pygame.draw.rect(self.main_display, self.right_color_wall, RIGHT_WALL)
        
        self.sprites["COLOR_WHEEL"].draw(self.main_display)

        pygame.draw.circle(self.main_display, self.left_color_ball, (x, y), (((50 - 10)/self.anim_ball_comeback.max)*self.anim_ball_comeback.frame + 10))

        self.buttons["OPTION_EXIT"].draw(self.main_display, self.transition.is_playing())
        self.buttons["OPTION_SAVE_EXIT"].draw(self.main_display, self.transition.is_playing())

        self.game_anims.update_add(self.delta, wrap=True)

        if self.anim_ball_comeback.is_playing_within_top():
            self.anim_ball_comeback.update_add(self.delta, clamp=True)

            self.anim_ball_revol_mainmenu.update_add(self.delta, wrap=True)

        if ((COLOR_WHEEL_REGION_SQ < UI.COLOR_WHEEL_RADIUS ** 2) and
            (pygame.mouse.get_pressed()[0])):
            color = self.main_display.get_at(mouse)
            if color.a > 200:
                self.left_color.r, self.left_color.g, self.left_color.b = color.r, color.g, color.b
                color = UI.find_opp_color(color)
                self.right_color.r, self.right_color.g, self.right_color.b = color.r, color.g, color.b

                self.set_colors()

    def option_exit_clicked(self):
        self.change_state(States.MAIN_MENU_S)

        if not (isinstance(self.player_config["color"], list) and isinstance(self.player_config["opposite_color"], list)):
            self.fix_broken_config()
            
        color = pygame.Color(self.player_config["color"]) # type: ignore
        self.left_color.r, self.left_color.g, self.left_color.b = color.r, color.g, color.b

        color = pygame.Color(self.player_config["opposite_color"]) # type: ignore
        self.right_color.r, self.right_color.g, self.right_color.b = color.r, color.g, color.b

        self.set_colors()

    def option_save_exit_clicked(self):
        self.change_state(States.MAIN_MENU_S)

        self.player_config["color"] = [self.left_color.r, self.left_color.g, self.left_color.b]
        self.player_config["opposite_color"] = [self.right_color.r, self.right_color.g, self.right_color.b]

        with open("player_config.json", "w") as config:
            config.write(json.dumps(self.player_config))

    def win_screen(self, width, height):
        self.transition_screen.set_alpha(int(2.55 * self.transition.frame))
        pygame.draw.circle(self.main_display, self.left_color_ball, (width//2 - 250, height//2 - 20), 50)
        pygame.draw.circle(self.main_display, self.right_color_ball, (width//2 + 250, height//2 - 20), 50)

        self.sprites["GAME_END_TEXT"].draw(self.main_display)
        self.buttons["WIN_END"].draw(self.main_display, self.transition.is_playing())

        if self.transition.message is None and self.transition.is_playing_after_down():
            self.transition.update_add(-self.delta, clamp=True)
        elif self.transition.message and self.transition.is_playing():
            self.transition.update_add(self.delta, clamp=True)
        elif self.transition.message and not self.transition.is_playing():
            self.change_state(self.transition.message)

        match self.gameplay.winner:
            case 1:
                self.sprites["LEFT_CROWN"].draw(self.main_display)
            case 2:
                self.sprites["RIGHT_CROWN"].draw(self.main_display)
        
        self.main_display.blit(self.transition_screen, (0, 0))

    def main_menu(self, width, height):
        self.anim.set_alpha(int((-200// self.game_anims.max ) * self.game_anims.frame) + 200)                     # alpha level
        self.transition_screen.set_alpha(int(2.55 * self.transition.frame))
        self.anim.fill(self.base_color)

        LEFT_WALL = pygame.Rect(-100, 0, min(width//2 - 500, 250), height + 100)
        RIGHT_WALL = pygame.Rect(width - min(width//2 - 600, 150), 0, width + 100, height + 100)

        x, y = (
            (width//2 - 250 * ((1/self.anim_ball_comeback.max)*self.anim_ball_comeback.frame)) - 500 * math.cos((2*math.pi*self.anim_ball_revol_mainmenu.frame)/self.anim_ball_revol_mainmenu.max) * ((-1/self.anim_ball_comeback.max)*self.anim_ball_comeback.frame + 1),
            (height//2 + 50 * ((-1/self.anim_ball_comeback.max)*self.anim_ball_comeback.frame + 1)) - 200 * math.sin((2*math.pi*self.anim_ball_revol_mainmenu.frame)/self.anim_ball_revol_mainmenu.max) * ((-1/self.anim_ball_comeback.max)*self.anim_ball_comeback.frame + 1)
        )

        #anim.fill((255,255,255))           # this fills the entire surface
        pygame.draw.rect(self.anim, self.left_color_wall, LEFT_WALL.move(self.game_anims.frame, 0))
        pygame.draw.rect(self.anim, self.right_color_wall, RIGHT_WALL.move(-self.game_anims.frame, 0))
        self.main_display.blit(self.anim, (0,0))    # (0,0) are the top-left coordinates
        
        self.game_anims.update_add(self.delta, wrap=True)
        self.anim_ball_comeback.update_add(-self.delta, clamp=True)
        self.anim_ball_revol_mainmenu.update_add(self.delta, wrap=True)

        if self.transition.message is None and self.transition.is_playing_after_down():
            self.transition.update_add(-self.delta, clamp=True)
        elif self.transition.message and self.transition.is_playing():
            self.transition.update_add(self.delta, clamp=True)
        elif self.transition.message and not self.transition.is_playing():
            self.change_state(self.transition.message)

        pygame.draw.circle(self.main_display, self.left_color_ball, (x, y), (((50 - 10)/self.anim_ball_comeback.max)*self.anim_ball_comeback.frame + 10))

        pygame.draw.rect(self.main_display, self.left_color_wall, LEFT_WALL)
        pygame.draw.rect(self.main_display, self.right_color_wall, RIGHT_WALL)

        self.sprites["MAIN_TEXT"].draw(self.main_display)

        self.buttons["MAIN_START"].draw(self.main_display, self.transition.is_playing())
        self.buttons["MAIN_OPTION"].draw(self.main_display, self.transition.is_playing())
        self.buttons["MAIN_ABOUT"].draw(self.main_display, self.transition.is_playing())

        self.main_display.blit(self.transition_screen, (0, 0))

    def about_menu(self, width, height):
        self.about_text.draw(self.main_display)
        #self.about_text.items[0].draw(self.main_display)

    def quantumn_collapse(self, random_body: Body, player: Body, left_player: bool):
        player.pos = random_body.pos
        player.velocity = random_body.velocity

        self.bodies = [body for body in self.bodies if (body.is_clone != player.id)]

        player.hidden = False
        player.glow = True

        if left_player:
            self.left_cam.zoom_in()
            pygame.time.set_timer(pygame.event.Event(userevents.POWER_UP_QUANTUM_COLLAPSE_STOP_GLOW_LEFT), 2000, loops=1)
        else:
            self.right_cam.zoom_in()
            pygame.time.set_timer(pygame.event.Event(userevents.POWER_UP_QUANTUM_COLLAPSE_STOP_GLOW_RIGHT), 2000, loops=1)

        self.gameplay.remove_power(left_player)

    # SCREEN STATE:
        # 0 => Main Menu
        # 1 => GAME SCREEN
        # 2 => Pause menu
        # 3 => Options
        # 4 => About menu

    def evaluate_event(self, event: pygame.event.Event, width):
        match event.type:
            case pygame.KEYDOWN:
                if self.STATE in (States.GAME_SCREEN_S, States.PAUSE_MENU_S):
                    if event.key in self.input_keys:
                        self.input_keys[event.key][0].set_alpha(255)
                        self.blit_dpads()

                        self.input_keys[event.key][1]() # start acceleration

                    if self.STATE in (States.GAME_SCREEN_S,):
                        if event.key == pygame.K_LSHIFT:
                            self.gameplay.set_power(True)
                        elif event.key == pygame.K_RSHIFT:
                            self.gameplay.set_power(False)
                        
                        elif event.key == pygame.K_q:
                            self.left_cam.decrease_scale()
                        elif event.key == pygame.K_e:
                            self.left_cam.increase_scale()
                        elif event.key == pygame.K_COMMA:
                            self.right_cam.decrease_scale()
                        elif event.key == pygame.K_PERIOD:
                            self.right_cam.increase_scale()

                    # todo: REMOVE LATER
                    """ if event.key == pygame.K_TAB:
                        self.gameplay.timer = 15
                    elif event.key == pygame.K_q:
                        self.gameplay.left_score_add(5)
                    elif event.key == pygame.K_e:
                        self.gameplay.right_score_add(5) """
                
                if event.key == pygame.K_ESCAPE:
                    match self.STATE:
                        case States.GAME_SCREEN_S:
                            self.change_state(States.PAUSE_MENU_S)
                        case States.PAUSE_MENU_S:
                            self.change_state(States.GAME_SCREEN_S)

                elif event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

            case pygame.KEYUP:
                if event.key in self.input_keys and self.STATE in (States.GAME_SCREEN_S, States.PAUSE_MENU_S):
                    self.input_keys[event.key][0].set_alpha(50)
                    self.blit_dpads()

                    self.input_keys[event.key][2]() # start deacceleration

            case userevents.GAME_TICK_SECOND:
                self.gameplay.tick()
                if len(self.coins) < 10 and random.random() < 0.4:
                    self.coins.append(phybody.Coin(Vector2(phybody.Body.random_pos((self.left_void, self.top_void, self.right_void, self.bottom_void)))))
                if len(self.coins) > 0 and random.random() < 0.1:
                    self.coins.pop(random.randint(0, len(self.coins)-1))

            case userevents.COIN_PICKUP:
                if event.player == self.left_player.id:
                    self.left_power_anim.update_add(self.delta * self.coin_boost, clamp=True)
                else:
                    self.right_power_anim.update_add(self.delta * self.coin_boost, clamp=True)

            case pygame.MOUSEWHEEL:
                match self.STATE:
                    case States.GAME_SCREEN_S:
                        mouse_x_y = pygame.mouse.get_pos()
                        right_rect = self.right_rect.move(width//2, 0)
                        match event.y:
                            case 1: #UP
                                if self.left_rect.collidepoint(mouse_x_y):
                                    self.left_cam.increase_scale()

                                if right_rect.collidepoint(mouse_x_y):
                                    self.right_cam.increase_scale()
                            case -1: #DOWN
                                if self.left_rect.collidepoint(mouse_x_y):
                                    self.left_cam.decrease_scale()

                                if right_rect.collidepoint(mouse_x_y):
                                    self.right_cam.decrease_scale() 

                    case States.ABOUT_S:
                        match event.y:
                            case 1: #UP
                                self.about_text.scroll(-80)
                            case -1: #DOWN
                                self.about_text.scroll(80)

            case pygame.VIDEORESIZE:
                self.resize(event.size)

            case pygame.MOUSEBUTTONUP if event.button == 1 and self.global_button_click[0]:
                self.global_button_click[0] = False

            case userevents.POWER_UP_GAIN_EVENT:
                if event.left_player:
                    player = self.left_player
                    self.gameplay.left_power_allow = False
                    self.left_power_anim.frame = self.left_power_anim.min
                else:
                    player = self.right_player
                    self.gameplay.right_power_allow = False
                    self.right_power_anim.frame = self.right_power_anim.min
                
                match event.power:
                    case PowerUp.SpeedUp:
                        player.speed_limit = phybody.POWER_SPEED_LIMIT
                    case PowerUp.Grow:
                        player.size, player.mass = phybody.POWER_SIZE, phybody.POWER_MASS
                    case PowerUp.AntiGravity:
                        player.mass = -1 * abs(player.mass)
                    case PowerUp.Quantum:
                        for i in range(70):
                            self.bodies.append(player.create_clone(player.id*100 + i, (self.left_void, self.top_void, self.right_void, self.bottom_void)))
                        
                        player.hidden = True
                        if event.left_player:
                            self.left_cam.zoom_out()
                        else:
                            self.right_cam.zoom_out()

            case userevents.POWER_UP_DESTROY_EVENT:
                player = self.left_player if event.left_player else self.right_player

                match event.power:
                    case PowerUp.SpeedUp:
                        player.speed_limit = phybody.SPEED_LIMIT
                    case PowerUp.Grow:
                        player.size, player.mass = phybody.SIZE, phybody.MASS
                    case PowerUp.AntiGravity:
                        player.mass = abs(player.mass)
                    case PowerUp.Quantum:
                        for body in self.bodies:
                            if body.is_clone == player.id:
                                self.quantumn_collapse(body, player, event.left_player)
                                break
                        else:
                            self.quantumn_collapse(player, player, event.left_player)

            case userevents.POWER_UP_QUANTUM_COLLAPSE:
                if event.random_body.is_clone == self.left_player.id:
                    self.quantumn_collapse(event.random_body, self.left_player, True)
                else:
                    self.quantumn_collapse(event.random_body, self.right_player, False)

            case userevents.POWER_UP_QUANTUM_COLLAPSE_STOP_GLOW_LEFT:
                self.left_player.glow = False
            case userevents.POWER_UP_QUANTUM_COLLAPSE_STOP_GLOW_RIGHT:
                self.right_player.glow = False

            case userevents.WINNER_DECLARED:
                self.transition.set_message(States.GAME_END_S, self.delta)

            case pygame.QUIT:
                self.running = False

    def display(self):
        self.running = True
        time = 0.0
        audio_factory.AUDIO_LIBRARY["MAIN_MENU"].play(-1)
        while self.running:
            try:
                width, height = self.main_display.get_size()

                events = pygame.event.get()
                for event in events:
                    self.evaluate_event(event, width)

                self.main_display.fill(self.base_color)

                match self.STATE:
                    case States.MAIN_MENU_S:
                        self.main_menu(width, height)
                    case States.GAME_SCREEN_S:
                        self.game_start_lobby_menu(width, height)
                    case States.PAUSE_MENU_S:
                        self.pause_menu(width, height)
                    case States.OPTION_MENU_S:
                        self.option_menu(width, height)
                    case States.ABOUT_S:
                        self.about_menu(width, height)
                    case States.GAME_END_S:
                        self.win_screen(width, height)

                if self.postprocess:
                    frame_tex = self.surface_to_texture(self.main_display)
                    frame_tex.use(0)
                    self.opengl_program['time'] = time
                    
                    self.opengl_renderer.render(mode=moderngl.TRIANGLE_STRIP)
                else:
                    self.window.blit(self.main_display, (0, 0))

                pygame.display.flip()

                if self.postprocess:
                    frame_tex.release()
                    if time >= 2 * math.pi * 100: time = 0

                self.delta = self.clock.tick(self.FPS) * 0.001
                pygame.display.set_caption(f"FPS: {1/self.delta}")
                #self.delta *= 0.001
            except KeyboardInterrupt:
                if self.postprocess:
                    frame_tex.release()
                self.running = False

CLIENT = GravClient(SET_FPS=1000)
CLIENT.display()
# program loop
CLIENT.quit()
pygame.quit()