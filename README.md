# grav_ball

### Introduction
This is a simple game which mimics basketball, but uses gravitational mechanism to attract the ball. Your goal is to bring the ball to your court. Use WASD or arrow keys to move your character.

### Features
- Color Customization
- Various Interesting Powerups
- Split Screen
- Shaders
- Timed Matches

### Why?
Python isn't meant for building fast paced programs. Its known globaly as an adhoc language, its known to be slow. I wanted to challenge this notion of python, and build a fast paced game from scratch by optimizing it as much as I can. The project only uses `pygame` for input handling, and drawing to screen, and `moderngl` to compile shaders. The game runs smoothly around 120fps on my system.

### How to run:
*Uses uv for handling python venv.

1. Clone the project and cd into it.
```
git clone https://github.com/skandabhairava/GravBall
cd GravBall
```

2. Use uv* to sync up dependencies. Activate venv.
```
uv sync
source .venv/bin/activate #on linux
```

3. Run the program.
```
uv run src/main.py
```

4. Optionally edit the `player_config.json` to edit game configurations.

### Where to find:
Code: [Github](https://github.com/skandabhairava/GravBall)