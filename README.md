Fundamental Requirements:

R0 - Game_state implementation

	Boot -> Menu*s -> Game -> Scoreboard -> Menu

R1 - Start Screen
	-single player - car customization
	-settings
	-programmable keysbinds

R2 - Preference screen
	-map choosing (tumbnail)


R3 - Game engine
	-physics engine (velocity, brake, turn, collision)
	-camera's physics
	-checkpoint system
	-car rendering

R4 - Start, Pause and Quit handler
	-scoreboard and statistics
	-countdown

R5 - HUD/time
	-lap timer
		**DEBUG**
	-FPS
	-current_checkpoint



Additional requirements:

R1 - Drift (drift + tire marks #faded)
R2 - Inemies/multiplayer
R3 - recording/replay
R4 - items (mario-kart style power-ups)
R5 - map obstacle implementation
R6 - minimap (possibly player icons)
R7 - Soundeffect and Soundtrack
R8 - Different handling systems for car/track/situation

R-FINAL - Storyline	
	-Progression and achievments
	-End screen/credits
	-Money and car purchases/unlock

Ideas for modes = 
Laptime
Single race
	**Multiplayer**
Championship
Mario Kart (drifting & items)
F1

Codebase mock:

main.py - main loop and boot
helper_functions.py
resources
	-Audio
	-Imgs
