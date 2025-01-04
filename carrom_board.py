from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time

# Global variables for striker control
striker_x = 0
striker_y = -250  # Start in box 1 (bottom)
mouse_x = 0
mouse_y = 0
can_strike = True
striker_speed = 30.0
restart_button = {"x": 0, "y": 400, "width": 100, "height": 30}
strike_time = 0  # Time when striker hits a coin
return_delay = 5000  # 5 seconds in milliseconds
dragging = False
strike_power = 0

# Add global variables for mouse handling
last_mouse_update = 0
mouse_update_interval = 32  # Increased interval to reduce processing
mouse_positions = []  # Store recent mouse positions
max_stored_positions = 5  # Maximum number of positions to store

# Striker box states
BOX_1 = 1  # Bottom box
BOX_2 = 2  # Left box
BOX_3 = 3  # Top box
BOX_4 = 4  # Right box
current_box = BOX_1

# Striker box positions and movement ranges
striker_boxes = {
    BOX_1: {"y": -250, "x_range": (-200, 200), "fixed_axis": "y"},  # Bottom box
    BOX_2: {"x": -250, "y_range": (-200, 200), "fixed_axis": "x"},  # Left box
    BOX_3: {"y": 250, "x_range": (-200, 200), "fixed_axis": "y"},   # Top box
    BOX_4: {"x": 250, "y_range": (-200, 200), "fixed_axis": "x"}    # Right box
}

# Physics variables
striker_velocity_x = 0
striker_velocity_y = 0
friction = 0.98
minimum_velocity = 0.2

# Define pocket positions (corners)
POCKETS = [
    (-350, -350),  # Bottom-left
    (-350, 350),   # Top-left
    (350, -350),   # Bottom-right
    (350, 350)     # Top-right
]

class Coin:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.velocity_x = 0
        self.velocity_y = 0
        self.radius = 15
        self.mass = 1.0
        self.active = True

# Initialize coins with physics
coins = [
    # Center red coin
    Coin(0, 0, 'red'),
    
    # Inner circle (6 coins)
    Coin(0, 40, 'black'),   # Top
    Coin(35, 20, 'white'),  # Top right
    Coin(35, -20, 'black'), # Bottom right
    Coin(0, -40, 'white'),  # Bottom
    Coin(-35, -20, 'black'), # Bottom left
    Coin(-35, 20, 'white'),  # Top left
    
    # Outer circle (12 coins)
    Coin(0, 70, 'white'),    # Top
    Coin(35, 60, 'black'),   # Top right 1
    Coin(60, 35, 'white'),   # Top right 2
    Coin(60, -35, 'black'),  # Bottom right 2
    Coin(35, -60, 'white'),  # Bottom right 1
    Coin(0, -70, 'black'),   # Bottom
    Coin(-35, -60, 'white'), # Bottom left 1
    Coin(-60, -35, 'black'), # Bottom left 2
    Coin(-60, 35, 'white'),  # Top left 2
    Coin(-35, 60, 'black'),  # Top left 1
]

# Game state variables
GAME_MODE = None  # '2P' or '4P'
CURRENT_TEAM = 1  # 1 or 2
TEAM1_SCORE = 0
TEAM2_SCORE = 0
CURRENT_SET = 1
WINNING_SCORE = 15
RED_COIN_POCKETED = False
VALID_STRIKE = False  # Track if current player pocketed correct color

def init_game_state():
    global GAME_MODE, CURRENT_TEAM, TEAM1_SCORE, TEAM2_SCORE, CURRENT_SET
    global RED_COIN_POCKETED, VALID_STRIKE, current_box, can_strike
    GAME_MODE = None  # Reset to mode selection
    CURRENT_TEAM = 1
    TEAM1_SCORE = 0
    TEAM2_SCORE = 0
    CURRENT_SET = 1
    RED_COIN_POCKETED = False
    VALID_STRIKE = False
    current_box = 1
    can_strike = True
    reset_board()

def reset_board():
    global coins, striker_x, striker_y, striker_velocity_x, striker_velocity_y, can_strike
    coins.clear()
    
    # Place red coin in center
    coins.append(Coin(0, 0, 'red'))
    
    # Create coins in alternating black and white pattern
    # Inner circle (6 coins)
    radius = 30
    for i in range(6):
        angle = i * (2 * math.pi / 6)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        color = 'black' if i % 2 == 0 else 'white'
        coins.append(Coin(x, y, color))
    
    # Middle circle (6 coins)
    radius = 50
    for i in range(6):
        angle = (i * (2 * math.pi / 6)) + (math.pi / 6)  # Offset by 30 degrees
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        color = 'white' if i % 2 == 0 else 'black'
        coins.append(Coin(x, y, color))
    
    # Outer circle (6 coins)
    radius = 70
    for i in range(6):
        angle = i * (2 * math.pi / 6)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        color = 'black' if i % 2 == 0 else 'white'
        coins.append(Coin(x, y, color))
    
    # Reset striker to box 1
    striker_x = 0
    striker_y = -250
    striker_velocity_x = 0
    striker_velocity_y = 0
    can_strike = True

def check_set_complete():
    # Count remaining coins
    white_coins = sum(1 for coin in coins if coin.active and coin.color == 'white')
    black_coins = sum(1 for coin in coins if coin.active and coin.color == 'black')
    red_coin = any(coin.active for coin in coins if coin.color == 'red')
    
    # Check if either team has pocketed all their coins
    team1_complete = (CURRENT_TEAM == 1 and white_coins == 0) or (CURRENT_TEAM == 2 and black_coins == 0)
    team2_complete = (CURRENT_TEAM == 1 and black_coins == 0) or (CURRENT_TEAM == 2 and white_coins == 0)
    
    if team1_complete or team2_complete:
        # Calculate points
        points = white_coins if CURRENT_TEAM == 2 else black_coins  # Points from remaining opponent coins
        if RED_COIN_POCKETED:
            points += 5  # Bonus for red coin
        
        # Update scores
        global TEAM1_SCORE, TEAM2_SCORE
        if team1_complete:
            TEAM1_SCORE += points
        else:
            TEAM2_SCORE += points
        
        # Start new set if no winner yet
        if TEAM1_SCORE < WINNING_SCORE and TEAM2_SCORE < WINNING_SCORE:
            reset_board()
            global CURRENT_SET
            CURRENT_SET += 1
        return True
    return False

def move_striker_to_next_box():
    global striker_x, striker_y, current_box, CURRENT_TEAM, VALID_STRIKE
    
    # Only change position and team if strike wasn't valid
    if not VALID_STRIKE:
        if GAME_MODE == '4P':
            # In 4P mode, striker moves clockwise
            current_box = (current_box % 4) + 1
            # Update team based on box
            if current_box in [1, 3]:
                CURRENT_TEAM = 1
            else:
                CURRENT_TEAM = 2
        else:
            # In 2P mode, alternate between boxes 1 and 3
            current_box = 3 if current_box == 1 else 1
            # Change team only if no valid strike
            CURRENT_TEAM = 2 if CURRENT_TEAM == 1 else 1
    
    # Update striker position
    if current_box == 1:
        striker_x = 0
        striker_y = -250
    elif current_box == 2:
        striker_x = -250
        striker_y = 0
    elif current_box == 3:
        striker_x = 0
        striker_y = 250
    else:  # box 4
        striker_x = 250
        striker_y = 0
    
    VALID_STRIKE = False  # Reset for next turn

def check_pocket_collision(coin):
    global RED_COIN_POCKETED, VALID_STRIKE, CURRENT_TEAM
    
    for pocket_x, pocket_y in POCKETS:
        dx = coin.x - pocket_x
        dy = coin.y - pocket_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Increased pocket detection radius for corner pockets
        if distance < 40:  # Increased detection radius for corner pockets
            # Calculate direction towards pocket
            dir_x = pocket_x - coin.x
            dir_y = pocket_y - coin.y
            dir_len = math.sqrt(dir_x*dir_x + dir_y*dir_y)
            if dir_len > 0:
                dir_x /= dir_len
                dir_y /= dir_len
            
            # Calculate coin's velocity direction
            vel_len = math.sqrt(coin.velocity_x*coin.velocity_x + coin.velocity_y*coin.velocity_y)
            if vel_len > 0:
                vel_x = coin.velocity_x / vel_len
                vel_y = coin.velocity_y / vel_len
                
                # Calculate dot product to check if coin is moving towards pocket
                dot_product = dir_x*vel_x + dir_y*vel_y
                
                # More forgiving angle for corner pockets (>0.7 means >70% towards pocket)
                if dot_product > 0.7:
                    coin.active = False
                    
                    # Update game state based on pocketed coin
                    if coin.color == 'red':
                        RED_COIN_POCKETED = True
                    elif ((CURRENT_TEAM == 1 and coin.color == 'white') or 
                          (CURRENT_TEAM == 2 and coin.color == 'black')):
                        VALID_STRIKE = True  # Player pocketed their color
                    
                    return True
    return False

def draw_scoreboard():
    # Draw outside the board on the right side
    glColor3f(0.0, 0.0, 0.0)
    
    # Title
    draw_text(450, 550, "SCOREBOARD")
    
    # Horizontal line
    glBegin(GL_LINES)
    glVertex2f(450, 530)
    glVertex2f(750, 530)
    glEnd()
    
    # Game mode and scores
    mode_text = "2 Players (Box 1 & 3)" if GAME_MODE == '2P' else "4 Players (All Boxes)"
    draw_text(450, 500, f"Game Mode: {mode_text}")
    
    if GAME_MODE == '2P':
        draw_text(450, 450, f"Player 1 (White): {TEAM1_SCORE}")
        draw_text(450, 400, f"Player 2 (Black): {TEAM2_SCORE}")
    else:
        draw_text(450, 450, f"Team 1 (White): {TEAM1_SCORE}")
        draw_text(450, 400, f"Team 2 (Black): {TEAM2_SCORE}")
    
    # Current state
    draw_text(450, 350, f"Set: {CURRENT_SET}")
    current_team_color = "White" if CURRENT_TEAM == 1 else "Black"
    player_text = "Player" if GAME_MODE == '2P' else "Team"
    draw_text(450, 300, f"Current {player_text}: {current_team_color}")
    draw_text(450, 250, f"Current Box: {current_box}")
    
    # Winner announcement
    if TEAM1_SCORE >= WINNING_SCORE:
        winner = "Player 1" if GAME_MODE == '2P' else "Team 1"
        glColor3f(0.0, 0.8, 0.0)
        draw_text(450, 200, f"{winner} (White) Wins!")
    elif TEAM2_SCORE >= WINNING_SCORE:
        winner = "Player 2" if GAME_MODE == '2P' else "Team 2"
        glColor3f(0.0, 0.8, 0.0)
        draw_text(450, 200, f"{winner} (Black) Wins!")

def draw_rules():
    # Draw on the left side
    glColor3f(0.5, 0.5, 0.5)
    draw_text(-750, 550, "GAME RULES")
    draw_text(-750, 500, "1. Each coin = 1 point")
    draw_text(-750, 450, "2. Red coin = 5 bonus points")
    draw_text(-750, 400, "3. First to 15 points wins")
    draw_text(-750, 350, "4. Keep turn if you pocket")
    draw_text(-750, 300, "   your colored coin")
    draw_text(-750, 250, "5. Striker moves only after")
    draw_text(-750, 200, "   failed attempt")

def draw_mode_selection():
    if GAME_MODE is None:
        glColor3f(0.0, 0.0, 0.0)
        # Title
        draw_text(-100, 200, "Welcome to Carrom Board Game!")
        draw_text(-100, 150, "Select Game Mode:")
        
        # Mode options
        draw_text(-100, 50, "Press 2 for 2 Players")
        draw_text(-100, 0, "(White: Box 1, Black: Box 3)")
        draw_text(-100, -50, "Press 4 for 4 Players")
        draw_text(-100, -100, "(Clockwise through all boxes)")
        
        # Rules
        draw_text(-100, -200, "Game Rules:")
        draw_text(-100, -250, "- Each coin = 1 point")
        draw_text(-100, -300, "- Red coin = 5 bonus points")
        draw_text(-100, -350, "- Keep turn if you pocket your color")
        draw_text(-100, -400, "- First to 15 points wins!")

def draw_board():
    # Draw the outer square
    glColor3f(0.55, 0.27, 0.07)
    draw_rectangle(-400, -400, 800, 800)
    
    # Draw the inner square
    glColor3f(0.91, 0.76, 0.65)
    draw_rectangle(-350, -350, 700, 700)
    
    # Draw corner pockets (black circles)
    glColor3f(0.0, 0.0, 0.0)  # Black color
    for x, y in POCKETS:
        draw_circle(x, y, 25, True)  # Solid black circles for pockets
    
    # Draw center circle
    glColor3f(0.55, 0.27, 0.07)
    draw_circle(0, 0, 75, False)
    
    # Draw the orange outer circles
    for x, y in [(-400, -400), (400, -400), (400, 400), (-400, 400)]:
        draw_pocket(x, y)
    
    # Striker line
    glColor3f(0.36, 0.25, 0.20)
    #box 1
    draw_line(-250, -250, 200, -250)  # Striker movement line
    draw_line(-250, -275, 200, -275)
    draw_line(-250, -250, -250, -275)
    draw_line(200, -250, 200, -275)
    
    #box 2
    draw_line(-250, -200, -250, 200)  #Striker movement line
    draw_line(-275, -200, -275, 200)
    draw_line(-250, -200, -275, -200)
    draw_line(-250, 200, -275, 200)

    #box 3
    draw_line(-250, 250, 200, 250)  #Striker movement line
    draw_line(-250, 275, 200, 275)
    draw_line(-250, 250, -250, 275)
    draw_line(200, 250, 200, 275)

    #box 4
    draw_line(250, -200, 250, 200)  #Striker movement line
    draw_line(275, -200, 275, 200)
    draw_line(250, -200, 275, -200)
    draw_line(250, 200, 275, 200)

def draw_speed_meter():
    # Draw meter background
    glColor3f(0.8, 0.8, 0.8)
    for i in range(420, 460):
        draw_line(i, -400, i, 0)  # Vertical meter
    
    # Draw power level
    power_height = (striker_speed / 15.0) * 400
    glColor3f(1.0, 0.0, 0.0)
    for i in range(420, 460):
        draw_line(i, -400, i, -400 + power_height)
    
    # Draw markings
    glColor3f(0.0, 0.0, 0.0)
    for i in range(0, 5):
        y = -400 + (i * 100)
        draw_line(415, y, 465, y)

def check_collision(obj1, obj2):
    dx = obj2.x - obj1.x
    dy = obj2.y - obj1.y
    distance = math.sqrt(dx*dx + dy*dy)
    
    if distance < (obj1.radius + obj2.radius):
        # Calculate collision normal
        nx = dx / distance
        ny = dy / distance
        
        # Relative velocity
        rx = obj2.velocity_x - obj1.velocity_x
        ry = obj2.velocity_y - obj1.velocity_y
        
        # Impact speed
        speed = rx * nx + ry * ny
        
        # Don't process collision if objects are moving apart
        if speed > 0:
            return
        
        # Impact force
        imp = (-(1.0 + 0.8) * speed) / (obj1.mass + obj2.mass)
        
        # Apply impulse
        obj1.velocity_x -= imp * obj2.mass * nx
        obj1.velocity_y -= imp * obj2.mass * ny
        obj2.velocity_x += imp * obj1.mass * nx
        obj2.velocity_y += imp * obj1.mass * ny
        
        # Move objects apart to prevent sticking
        overlap = (obj1.radius + obj2.radius - distance) / 2.0
        obj1.x -= overlap * nx
        obj1.y -= overlap * ny
        obj2.x += overlap * nx
        obj2.y += overlap * ny

def update_physics():
    global striker_velocity_x, striker_velocity_y, striker_x, striker_y, can_strike, CURRENT_TEAM
    
    current_time = glutGet(GLUT_ELAPSED_TIME)
    all_stopped = True
    
    # Create striker object for collision detection
    striker = Coin(striker_x, striker_y, 'striker')
    striker.velocity_x = striker_velocity_x
    striker.velocity_y = striker_velocity_y
    striker.radius = 18
    striker.mass = 2.0
    
    # Update striker position
    if abs(striker_velocity_x) > 0.01 or abs(striker_velocity_y) > 0.01:
        striker_x += striker_velocity_x
        striker_y += striker_velocity_y
        striker.x = striker_x
        striker.y = striker_y
        
        # Apply friction
        striker_velocity_x *= 0.98
        striker_velocity_y *= 0.98
        striker.velocity_x = striker_velocity_x
        striker.velocity_y = striker_velocity_y
        
        all_stopped = False
        
        # Allow striker to reach corners but bounce off walls
        if abs(striker_x) > 350:
            # Check if near pocket
            near_pocket = False
            for pocket_x, pocket_y in POCKETS:
                dx = striker_x - pocket_x
                dy = striker_y - pocket_y
                if math.sqrt(dx*dx + dy*dy) < 40:
                    near_pocket = True
                    break
            
            if not near_pocket:
                striker_velocity_x *= -0.5
                striker_x = 350 if striker_x > 0 else -350
        
        if abs(striker_y) > 350:
            # Check if near pocket
            near_pocket = False
            for pocket_x, pocket_y in POCKETS:
                dx = striker_x - pocket_x
                dy = striker_y - pocket_y
                if math.sqrt(dx*dx + dy*dy) < 40:
                    near_pocket = True
                    break
            
            if not near_pocket:
                striker_velocity_y *= -0.5
                striker_y = 350 if striker_y > 0 else -350
        
        # Check if striker is pocketed
        for pocket_x, pocket_y in POCKETS:
            dx = striker_x - pocket_x
            dy = striker_y - pocket_y
            if math.sqrt(dx*dx + dy*dy) < 40:
                striker_velocity_x = 0
                striker_velocity_y = 0
                move_striker_to_next_box()
                can_strike = True
                break
    
    # Update coins and check collisions
    for coin in coins:
        if not coin.active:
            continue
        
        # Check collision with striker
        if abs(striker_velocity_x) > 0.01 or abs(striker_velocity_y) > 0.01:
            check_collision(striker, coin)
            striker_velocity_x = striker.velocity_x
            striker_velocity_y = striker.velocity_y
        
        # Update coin position
        if abs(coin.velocity_x) > 0.01 or abs(coin.velocity_y) > 0.01:
            coin.x += coin.velocity_x
            coin.y += coin.velocity_y
            
            # Apply friction
            coin.velocity_x *= 0.98
            coin.velocity_y *= 0.98
            
            all_stopped = False
            
            # Allow coins to reach corners but bounce off walls
            if abs(coin.x) > 350:
                # Check if near pocket
                near_pocket = False
                for pocket_x, pocket_y in POCKETS:
                    dx = coin.x - pocket_x
                    dy = coin.y - pocket_y
                    if math.sqrt(dx*dx + dy*dy) < 40:
                        near_pocket = True
                        break
                
                if not near_pocket:
                    coin.velocity_x *= -0.5
                    coin.x = 350 if coin.x > 0 else -350
            
            if abs(coin.y) > 350:
                # Check if near pocket
                near_pocket = False
                for pocket_x, pocket_y in POCKETS:
                    dx = coin.x - pocket_x
                    dy = coin.y - pocket_y
                    if math.sqrt(dx*dx + dy*dy) < 40:
                        near_pocket = True
                        break
                
                if not near_pocket:
                    coin.velocity_y *= -0.5
                    coin.y = 350 if coin.y > 0 else -350
            
            # Check if coin is pocketed
            if check_pocket_collision(coin):
                coin.velocity_x = 0
                coin.velocity_y = 0
        
        # Check collisions with other coins
        for other_coin in coins:
            if other_coin != coin and other_coin.active:
                check_collision(coin, other_coin)
    
    # Check if all objects have stopped moving
    if all_stopped and not can_strike:
        can_strike = True
        # Move striker to next position only if no valid strike
        if not VALID_STRIKE:
            move_striker_to_next_box()
    
    glutPostRedisplay()

def animate(value):
    try:
        update_physics()
        glutPostRedisplay()
        glutTimerFunc(16, animate, 0)  # 60 FPS
    except Exception as e:
        print(f"Error in animate: {e}")
        cleanup()  # Attempt to recover from error

def draw_text(x, y, text):
    glRasterPos2f(x, y)
    for c in text:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(c))

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    
    if GAME_MODE is None:
        draw_mode_selection()
    else:
        draw_board()
        
        # Draw active coins
        for coin in coins:
            if coin.active:
                if coin.color == 'black':
                    glColor3f(0.1, 0.1, 0.1)
                elif coin.color == 'white':
                    glColor3f(0.9, 0.9, 0.9)
                else:  # red
                    glColor3f(0.8, 0.0, 0.0)
                draw_circle(coin.x, coin.y, coin.radius, True)
        
        # Draw striker
        glColor3f(0.3, 0.3, 0.8)
        draw_circle(striker_x, striker_y, 18, True)
        
        # Draw aim guide when dragging
        draw_aim_guide()
        
        draw_restart_button()
        draw_scoreboard()
        draw_rules()
    
    glutSwapBuffers()

def keyboard(key, x, y):
    global GAME_MODE, striker_x, striker_y, can_strike
    
    if GAME_MODE is None:
        if key == b'2':
            GAME_MODE = '2P'
            init_game_state()
            GAME_MODE = '2P'  # Set it again after init
            can_strike = True
            glutPostRedisplay()
            return
        elif key == b'4':
            GAME_MODE = '4P'
            init_game_state()
            GAME_MODE = '4P'  # Set it again after init
            can_strike = True
            glutPostRedisplay()
            return
    
    if not can_strike:
        return
    
    step = 10  # Movement step size
    
    if current_box in [1, 3]:  # Horizontal movement boxes
        if key == b'a' or key == b'A':  # Left
            striker_x = max(striker_x - step, -200)
        elif key == b'd' or key == b'D':  # Right
            striker_x = min(striker_x + step, 200)
    elif current_box in [2, 4]:  # Vertical movement boxes
        if key == b'w' or key == b'W':  # Up
            striker_y = min(striker_y + step, 200)
        elif key == b's' or key == b'S':  # Down
            striker_y = max(striker_y - step, -200)
    
    glutPostRedisplay()

def smooth_mouse_position(x, y):
    global mouse_positions
    
    # Add new position
    mouse_positions.append((x, y))
    
    # Keep only recent positions
    if len(mouse_positions) > max_stored_positions:
        mouse_positions.pop(0)
    
    # Average positions for smoothing
    if mouse_positions:
        avg_x = sum(pos[0] for pos in mouse_positions) / len(mouse_positions)
        avg_y = sum(pos[1] for pos in mouse_positions) / len(mouse_positions)
        return avg_x, avg_y
    return x, y

def mouse_motion(x, y):
    global mouse_x, mouse_y, strike_power, last_mouse_update, mouse_positions
    
    current_time = glutGet(GLUT_ELAPSED_TIME)
    
    # Only update mouse position at fixed intervals
    if current_time - last_mouse_update >= mouse_update_interval:
        # Convert window coordinates to world coordinates
        world_x = (x - 800) * 1600/1600
        world_y = (600 - y) * 1200/1200
        
        if dragging and can_strike:
            # Apply smoothing to mouse position
            smooth_x, smooth_y = smooth_mouse_position(world_x, world_y)
            mouse_x = smooth_x
            mouse_y = smooth_y
            
            # Calculate strike power with smoothed position
            dx = smooth_x - striker_x
            dy = smooth_y - striker_y
            strike_power = min(math.sqrt(dx*dx + dy*dy) / 200.0, 1.0)
            
            # Only redisplay if significant change
            if abs(dx) > 1 or abs(dy) > 1:
                glutPostRedisplay()
        
        last_mouse_update = current_time

def mouse_button(button, state, x, y):
    global can_strike, striker_velocity_x, striker_velocity_y, mouse_x, mouse_y, dragging, strike_power, mouse_positions
    
    # Convert window coordinates to world coordinates
    world_x = (x - 800) * 1600/1600
    world_y = (600 - y) * 1200/1200
    
    # Check restart button click
    if (button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and
        abs(world_x - restart_button["x"]) < restart_button["width"]/2 and
        abs(world_y - restart_button["y"]) < restart_button["height"]/2):
        global GAME_MODE
        GAME_MODE = None  # Reset to mode selection
        init_game_state()
        glutPostRedisplay()
        return
    
    if can_strike:
        if button == GLUT_LEFT_BUTTON:
            if state == GLUT_DOWN:
                dragging = True
                mouse_x = world_x
                mouse_y = world_y
                strike_power = 0
                mouse_positions.clear()  # Clear stored positions
            elif state == GLUT_UP and dragging:
                # Use smoothed position for final strike
                smooth_x, smooth_y = smooth_mouse_position(world_x, world_y)
                
                # Calculate direction and velocity
                dx = smooth_x - striker_x
                dy = smooth_y - striker_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Normalize direction
                if distance > 0:
                    dx = dx / distance
                    dy = dy / distance
                    
                    # Apply power (scaled by distance) with reduced maximum speed
                    power = min(distance / 200.0, 1.0) * 15
                    striker_velocity_x = dx * power
                    striker_velocity_y = dy * power
                
                dragging = False
                can_strike = False
                strike_power = 0
                mouse_positions.clear()  # Clear stored positions

def draw_aim_guide():
    if can_strike and dragging:
        glColor3f(0.5, 0.5, 0.5)  # Gray color for aim guide
        glLineWidth(1.0)
        
        # Draw aim line with reduced frequency
        if glutGet(GLUT_ELAPSED_TIME) % 2 == 0:  # Update every other frame
            dx = mouse_x - striker_x
            dy = mouse_y - striker_y
            length = math.sqrt(dx*dx + dy*dy)
            
            if length > 0:
                # Normalize direction
                dx = dx / length
                dy = dy / length
                
                # Draw line
                glBegin(GL_LINES)
                glVertex2f(striker_x, striker_y)
                glVertex2f(striker_x + dx * 50, striker_y + dy * 50)
                glEnd()

def cleanup():
    global coins, dragging, strike_power, mouse_positions
    # Reset any accumulated state
    dragging = False
    strike_power = 0
    mouse_positions.clear()
    # Clear coin list
    coins.clear()
    # Reset game state
    init_game_state()

def draw_line(x1, y1, x2, y2):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    
    x, y = x1, y1
    
    x_step = 1 if x2 > x1 else -1
    y_step = 1 if y2 > y1 else -1
    
    glBegin(GL_POINTS)
    
    if dx > dy:
        d = 2*dy - dx
        while x != x2:
            glVertex2f(x, y)
            if d >= 0:
                y += y_step
                d -= 2*dx
            x += x_step
            d += 2*dy
    else:
        d = 2*dx - dy
        while y != y2:
            glVertex2f(x, y)
            if d >= 0:
                x += x_step
                d -= 2*dy
            y += y_step
            d += 2*dx
            
    glVertex2f(x2, y2)
    glEnd()

def draw_circle(center_x, center_y, radius, filled=False):
    x = 0
    y = radius
    d = 1 - radius
    
    if filled:
        glBegin(GL_POINTS)
        for r in range(radius):
            x = 0
            y = r
            d = 1 - r
            while x <= y:
                for px, py in [(x,y), (y,x), (-x,y), (-y,x),
                              (-x,-y), (-y,-x), (x,-y), (y,-x)]:
                    glVertex2f(center_x + px, center_y + py)
                if d < 0:
                    d += 2*x + 3
                else:
                    d += 2*(x - y) + 5
                    y -= 1
                x += 1
        glEnd()
    else:
        glBegin(GL_POINTS)
        while x <= y:
            glVertex2f(center_x + x, center_y + y)
            glVertex2f(center_x + y, center_y + x)
            glVertex2f(center_x - y, center_y + x)
            glVertex2f(center_x - x, center_y + y)
            glVertex2f(center_x - x, center_y - y)
            glVertex2f(center_x - y, center_y - x)
            glVertex2f(center_x + y, center_y - x)
            glVertex2f(center_x + x, center_y - y)
            
            if d < 0:
                d += 2*x + 3
            else:
                d += 2*(x - y) + 5
                y -= 1
            x += 1
        glEnd()

def draw_rectangle(x, y, width, height):
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

def fill_board_color(x1, y1, x2, y2):
    glColor3f(0.82, 0.70, 0.55)  # Wooden board color
    for y in range(y1, y2):
        draw_line(x1, y, x2, y)

def draw_pocket(x, y):
    # Draw orange outer circle
    glColor3f(1.0, 0.5, 0.0)  # Orange color
    draw_circle(x, y, 30, True)
    
    # Draw black outline for outer circle
    glColor3f(0.0, 0.0, 0.0)
    draw_circle(x, y, 30, False)

def draw_restart_button():
    # Draw restart button on the right side of the board
    glColor3f(0.2, 0.6, 0.2)  # Green color for button
    
    # Button position (moved to right side)
    restart_button["x"] = 600  # Right side of window
    restart_button["y"] = -500  # Bottom of window
    
    # Draw button rectangle
    glBegin(GL_QUADS)
    glVertex2f(restart_button["x"] - restart_button["width"]/2, restart_button["y"] - restart_button["height"]/2)
    glVertex2f(restart_button["x"] + restart_button["width"]/2, restart_button["y"] - restart_button["height"]/2)
    glVertex2f(restart_button["x"] + restart_button["width"]/2, restart_button["y"] + restart_button["height"]/2)
    glVertex2f(restart_button["x"] - restart_button["width"]/2, restart_button["y"] + restart_button["height"]/2)
    glEnd()
    
    # Draw button text
    glColor3f(1.0, 1.0, 1.0)  # White text
    draw_text(restart_button["x"] - 30, restart_button["y"] - 5, "Restart")

def init():
    glClearColor(1.0, 1.0, 1.0, 1.0)
    gluOrtho2D(-800, 800, -600, 600)

def cleanup():
    global coins, dragging, strike_power, mouse_positions
    # Reset any accumulated state
    dragging = False
    strike_power = 0
    mouse_positions.clear()
    # Clear coin list
    coins.clear()
    # Reset game state
    init_game_state()

glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(1600, 1200)
glutCreateWindow(b"Carrom Game")

init()  # Initialize game state
GAME_MODE = None  # Start with mode selection

# Register callbacks
glutDisplayFunc(display)
glutKeyboardFunc(keyboard)
glutMotionFunc(mouse_motion)
glutMouseFunc(mouse_button)
glutTimerFunc(16, animate, 0)  # Start animation loop

# Register cleanup
glutCloseFunc(cleanup)

# Start the game
glutMainLoop()