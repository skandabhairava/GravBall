import pygame, audio_factory, random
from enum import Enum

class PowerUp(Enum):
    SpeedUp = 110
    Grow = 210
    Quantum = 310
    AntiGravity = 410

class Gameplay:
    def __init__(self, max_time: int, winner_event: int, power_up_gain_event: int, power_up_destroy_event: int) -> None:
        assert max_time < 3600, "MaxTime can't be greater than 60 minutes"

        self.left_score: int = 0
        self.right_score: int = 0

        self.timer: int = max_time
        self.max_time: int = max_time
        self.clock_sound: bool = False

        self.winner_event: int = winner_event
        self.winner: int = 0

        self.power_up_gain_event: int = power_up_gain_event
        self.power_up_destroy_event: int = power_up_destroy_event

        self.left_power: None|tuple[PowerUp, int] = None
        self.left_power_allow: bool = False
        self.right_power: None|tuple[PowerUp, int] = None
        self.right_power_allow: bool = False

    def set_power(self, left_player: bool):
        if (left_player and (self.left_power or not self.left_power_allow)) or (not left_player and (self.right_power or not self.right_power_allow)):
            return
        
        power = random.choice(list(PowerUp))
        #power = PowerUp.SpeedUp
        #power = PowerUp.Grow
        #power = PowerUp.Quantum
        #power = PowerUp.AntiGravity

        if left_player:
            self.left_power = power, self.timer
        else:
            self.right_power = power, self.timer

        audio_factory.AUDIO_LIBRARY["POWER_UP"].play()
        pygame.event.post(pygame.event.Event(self.power_up_gain_event, left_player=left_player, power=power))

    def remove_power(self, left_player: bool):
        if left_player:
            self.left_power = None
            return
        
        self.right_power = None

    def left_score_add(self, add = 1):
        self.left_score += add
        if self.left_score > 99:
            self.left_score = 99

    def right_score_add(self, add = 1):
        self.right_score += add
        if self.right_score > 99:
            self.right_score = 99

    def timer_in_min_sec(self) -> tuple[str, str]:
        if self.timer < 0:
            return ("00", "00")
        return (f"{(self.timer // 60):02}", f"{(self.timer % 60):02}")
    
    def tick(self) -> None:
        self.timer -= 1
        #print("tick!", self.timer_in_min_sec())

        if self.timer < 10 and not self.clock_sound:
            audio_factory.AUDIO_LIBRARY["CLOCK"].play(-1)
            self.clock_sound = True


        self.check_powerup()
        if self.timer > 0:
            return
        
        self.check_winner()

    def check_powerup(self):
        if ((self.left_power is not None) and
            ((self.left_power[1] - self.timer) > self.left_power[0].value%100)):
            pygame.event.post(pygame.event.Event(self.power_up_destroy_event, left_player=True, power=self.left_power[0]))
            self.left_power = None

        if ((self.right_power is not None) and
            ((self.right_power[1] - self.timer) > self.right_power[0].value%100)):
            pygame.event.post(pygame.event.Event(self.power_up_destroy_event, left_player=False, power=self.right_power[0]))
            self.right_power = None

    def check_winner(self) -> int:

        # 0 -> timer hasnt run out
        # 1 -> left player won
        # 2 -> right player won
        # 3 -> tie

        if self.winner:
            return self.winner

        # self.winner = 0
        if self.timer > 0:
            return self.winner
        
        if self.left_score > self.right_score:
            self.winner = 1
        elif self.right_score > self.left_score:
            self.winner = 2
        else:
            self.winner = 3
        
        pygame.event.post(pygame.event.Event(self.winner_event))
        return self.winner
        
    def reset(self) -> None:
        self.left_score = 0
        self.right_score = 0
        self.timer = self.max_time
        self.winner = 0
        self.clock_sound = False
        self.left_power = None
        self.left_power_allow = False
        self.right_power = None
        self.right_power_allow = False