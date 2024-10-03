import pygame, helper

VOLUME = 10
#VOLUME = 0.05
#VOLUME = 0.0

AUDIO_LIBRARY = {
    "BUTTON_CLICK": pygame.mixer.Sound(helper.resource_path("audio/click-button.mp3")),
    "MAIN_MENU": pygame.mixer.Sound(helper.resource_path("audio/main-menu.mp3")),
    "GAME_LOOP": pygame.mixer.Sound(helper.resource_path("audio/game-loop.mp3")),
    "CLOCK": pygame.mixer.Sound(helper.resource_path("audio/clock.mp3")),
    "POWER_UP": pygame.mixer.Sound(helper.resource_path("audio/power_up.mp3")),
    "BEEP": pygame.mixer.Sound(helper.resource_path("audio/beep.mp3"))
}

def set_volume(vol:float=VOLUME):
    for key, audio in AUDIO_LIBRARY.items():
        if key in ("CLOCK", "POWER_UP", "BEEP"):
            audio.set_volume(vol * 2)
            continue
        audio.set_volume(vol)
