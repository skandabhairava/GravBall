import os, sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS # type: ignore
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

ABOUT0 = "                        Welcome to GravBall!"

ABOUT1 = """


This offline 2-player sci-fi game mixes the concept of Basketball and Gravity.         
Make use of Physics to gravitationally attract the ball towards your colored court!    

Concept:
    Gravity is a mysterious force/property in this universe. Newton tried to understand
    gravity as a force and tried to formulate it. This is the formula he came up with. 
"""

ABOUT2 = """
    According to the formula, the attractive force acted on both bodies is
    proportional to the product of the mass of both bodies, and its scaled down        
    by the square of the distance between the two bodies.                              

    Thats just a fancy way to say "The Gravitational Force increases when the mass
    of any body increases, or when the distance between the 2 bodies decreases".               

    Next came Einstein, He tried to understand Gravity, not as a Force, but as a       
    curvature of time and space. Einstein packed all those formulas into his           
    General and Special Theory of Relativity. Even though Einstein's formulas are      
    pretty decent, they are still an approximation. There is continous work being done 
    to reconcile The Theories of Relativity                                            
    (The Theory that governs the Macroscopic world), and Quantum Mechanics             
    (The Theory that governs the microscopic world, i.e atoms, electrons, etc).        

    We'll be using Newton's equations to simulate gravity as its still very accurate,  
    and easy to simulate!
"""

ABOUT3 = """
Controls:
    Left player:
        Movement: WASD KEYS
        Trigger PowerUp: LEFT_SHIFT
        Zoom: Q(Zoom-out) E(Zoom-in)

    Right player:
        Movement: ARROW KEYS
        Trigger PowerUp: RIGHT_SHIFT
        Zoom: ,(Zoom-out) .(Zoom-in)

    Scroll on either windows to zoom in or out of your respective player.

PowerUps:
"""

ABOUT3_speed = """
    -> Speed:
        Ability: Increases your speed limit.
        Disability: Harder to control your player.
"""

ABOUT3_grow = """
    -> Grow:
        Ability: Increases your mass, so you attract the ball stronger.
        Disability: As the force on the ball is stronger, the ball falls faster
            gaining enough kinetic energy to bounce off higher from the player,
            and hence making it difficult to keep the ball around you at all time.
"""

ABOUT3_antigrav = """
    -> AntiGravity:
        Ability: Pushes away the ball instead of "attracting it".
        Disability: Makes it harder to "attract" the ball to your court.
"""

ABOUT3_quantum = """
    -> Quantum Wave:
        Concept:
            I know Quantum-Gravity isn't a real concept YET. This power-up is just
            a quirky connection between 2 cool physics concept.
            In Quantum Mechanics, a particle such as an electron, is both a wave
            and a particle at the same time. A Wave does not have a defined position,
            and a particle does not have defined momentum(/velocity).
            This is described by Heisenberg's Uncertainity Principle.
"""

ABOUT4 = """
            Now when an electron is "Observed" or "Measured", its position becomes
            approximately defined, but its velocity becomes uncertain.
            Without measurement, the electron just acts as a wave with
            uncertain position, but a pretty defined velocity.

            In this simulation, we dont really simulate waves, but we can bring in
            the concept of the Uncertainity principle, by creating multiple clones
            of the player, creating an "uncertainity in position", as in the wave form.

            When the ball touches(measures) one of the clones, or when the power-up time runs out,
            the superposition collapses down to that point, hence you end up in that position.
        Ability: Create multiple clones of yourself around the map until the effect runs out,
            or the ball touches one of your clones.
        Disability: You loose the ability to control your player, and you will end up on a
            random spot on the map after the Power-up runs out.
"""