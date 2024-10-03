from pygame.math import Vector2
import pygame, random, userevents

# const
G = 20

# DAMPENING FACTORS AS SYSTEM LOOSES ENERGY TO HEAT
BOUNCE_DAMP = 0.0
GRAV_DAMP = 0.3

SPEED_LIMIT = 4
POWER_SPEED_LIMIT = 10
BALL_SPEED_LIMIT = 8

SIZE, MASS = 30, 100
POWER_SIZE, POWER_MASS = 50, 1000

FRICTION = 0.99

class Coin:
    def __init__(self, pos: Vector2) -> None:
        self.pos = pos

class Body:

    def __init__(self, id: int, is_player: bool, color: pygame.Color, pos: Vector2, velocity: Vector2, size: int = SIZE, mass: float = MASS, is_clone: int = 0, hidden: bool = False) -> None:

        self.id: int = id

        self.is_player: bool = is_player
        self.color: pygame.Color = color
        self.size: int = size
        self.mass: float = mass
        self.pos: Vector2 = pos

        self.velocity: Vector2 = velocity
        self.acceleration: Vector2 = Vector2(0, 0)

        self.speed_limit: int = SPEED_LIMIT if is_player else BALL_SPEED_LIMIT

        self.is_clone: int = is_clone
        self.hidden: bool = hidden

        self.glow = False

    @staticmethod
    def random_pos(pos_limit: tuple[float, float, float, float]) -> tuple[float, float]:
        return random.randint(int(pos_limit[0]), int(pos_limit[2])), random.randint(int(pos_limit[3]), int(pos_limit[1]))

    def create_clone(self, id: int, pos_limit: tuple[float, float, float, float]) -> 'Body':
        #pos_limit: (left, top, right, down)

        new_bod = Body(
                    id=id,
                    is_player=True,
                    color=self.color,
                    pos=Vector2(self.random_pos(pos_limit)),
                    velocity=Vector2(random.randint(-10, 10), random.randint(-10, 10)),
                    size=random.randint(10, 30),
                    mass=random.randint(50, 1500),
                    is_clone=self.id,
                    hidden=False
                    )
        new_bod.speed_limit = 50
        return new_bod

    def reset(self, center: tuple[float, float]):
        self.pos.x, self.pos.y = center
        self.acceleration.x, self.acceleration.y = 0, 0
        self.velocity.x, self.velocity.y = 0, 0
        self.hidden = False
        if self.is_player:
            self.size = SIZE
            self.mass = MASS
            self.speed_limit = SPEED_LIMIT
        else:
            self.mass = abs(self.mass)

    def add_mouse_x(self, val: float):
        self.acceleration.x += val

    def add_mouse_y(self, val: float):
        self.acceleration.y += val

    def update(self, dt: float, void_dim: tuple[float, float, float, float], coins: list[Coin]):
        # void dim: (self.top_void, self.bottom_void, self.left_void, self.right_void)

        if self.hidden:
            return
        
        if self.is_player and not self.is_clone:
            coins_to_remove: list[Coin] = []
            for coin in coins:
                dist = self.pos.distance_to(coin.pos)
                if dist < (self.size + 15):
                    coins_to_remove.append(coin)
                    pygame.event.post(pygame.event.Event(userevents.COIN_PICKUP, player=self.id))
            
            for coin in coins_to_remove:
                if coin in coins:
                    coins.remove(coin)

        friction_factor = ((FRICTION ** (dt * 60 * 2)) * (not self.is_clone)) + bool(self.is_clone)

        if (self.pos.y + self.size) > void_dim[0]:
            self.velocity.y = abs(self.velocity.y) * -1
        if (self.pos.y - self.size) < void_dim[1]:
            self.velocity.y = abs(self.velocity.y)
        if (self.pos.x - self.size) < void_dim[2]:
            self.velocity.x = abs(self.velocity.x)
        if (self.pos.x + self.size) > void_dim[3]:
            self.velocity.x = abs(self.velocity.x) * -1

        if not (self.velocity.x == 0 and self.velocity.y == 0):
            self.pos += (self.velocity).clamp_magnitude(self.speed_limit) * (dt * 60 * 2)
        
        self.velocity += (self.acceleration) * (dt * 60 * 2)
        self.velocity *= friction_factor

        if self.velocity.magnitude() < 0.01:
            self.velocity.x = 0
            self.velocity.y = 0

    def gravity_calc(self, all_bodies: list['Body']):

        force: Vector2 = Vector2(0, 0)

        for body in all_bodies:
            if body.id == self.id:
                continue
            elif self.is_player or not body.is_player:
                continue
            elif body.hidden:
                continue

            # self is ball, body is player or clone

            dist = self.pos.distance_to(body.pos)
            if dist < (self.size + body.size):
                # HANDLE COLLISION

                dist = self.size + body.size

                op_direction_norm = (-(body.pos - self.pos)).normalize()
                self.pos = body.pos + (op_direction_norm * (dist))

                self.velocity = self.velocity.reflect(op_direction_norm) * (1 - BOUNCE_DAMP)

                if body.is_clone:
                    pygame.event.post(pygame.event.Event(userevents.POWER_UP_QUANTUM_COLLAPSE, random_body=body))

            elif dist > (self.size + body.size) :
                # GRAVITY
                force += ((G * self.mass * body.mass)/( (dist**2) )) * (body.pos - self.pos).normalize()

        self.acceleration = ((1 - GRAV_DAMP) * force)/self.mass