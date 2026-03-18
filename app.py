from cmu_graphics import *
import math

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def distance(x1, y1, x2, y2):
    """Calculates the distance between two points (x1, y1) and (x2, y2)."""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# ==========================================
# INITIALIZATION
# ==========================================

def onAppStart(app):
    # --- Game State ---
    app.money = 650
    app.lives = 20
    app.wave = 1
    app.gameOver = False
    
    # --- Entities ---
    app.towers = []
    app.bloons = []
    app.projectiles = []
    
    # --- Pathing ---
    # The coordinate checkpoints the bloons will travel between
    app.path = [(0, 100), (200, 100), (200, 300), (400, 300), (400, 200), (400, -50)]
    
    # --- Timing ---
    app.stepsPerSecond = 30
    app.timer = 0

    app.mousePos = (0, 0)
    app.placingTower = True # Always showing a preview for now

# ==========================================
# CONTROLS
# ==========================================

def onMouseMove(app, mouseX, mouseY):
    app.mousePos = (mouseX, mouseY)

def onMousePress(app, mouseX, mouseY):
    # Ignore clicks if the game is over
    if app.gameOver: return
    
    # Tower stats
    towerCost = 200
    towerRange = 80
    
    # Place a tower if the player has enough money
    if app.money >= towerCost:
        newTower = {
            'x': mouseX, 
            'y': mouseY, 
            'range': towerRange, 
            'cooldown': 0 
        }
        app.towers.append(newTower)
        app.money -= towerCost
    else:
        print("Not enough money!")

# ==========================================
# CORE GAME LOGIC
# ==========================================

def onStep(app):
    # Stop processing logic if the game is over
    if app.gameOver: return
    
    app.timer += 1
    
    spawnRate = max(10, 30 - (app.wave * 2))
    # --- 1. Spawning Bloons ---
    # Spawn a new bloon every second (30 frames)
    if app.timer % spawnRate == 0:
        startX, startY = app.path[0]
        # Alternate between Red and Blue bloons
        isBlue = (app.timer % 60 == 0) 
        newBloon = {
            'x': startX, 
            'y': startY, 
            'targetNode': 1,
            'speed': 5 if isBlue else 3, # Blue is faster
            'health': 2 if isBlue else 1, # Blue takes two hits
            'color': 'blue' if isBlue else 'red'
        }
        app.bloons.append(newBloon)
    if app.timer % 300 == 0:
        app.wave += 1

    # --- 2. Moving Bloons ---
    # Iterate backwards so we can safely remove elements from the list
    for i in range(len(app.bloons) - 1, -1, -1):
        bloon = app.bloons[i]
        targetX, targetY = app.path[bloon['targetNode']]
        
        # Calculate the angle towards the next path node
        angle = math.atan2(targetY - bloon['y'], targetX - bloon['x'])
        
        # Move the bloon along that angle using trig
        bloon['x'] += bloon['speed'] * math.cos(angle)
        bloon['y'] += bloon['speed'] * math.sin(angle)
        
        # Check if the bloon reached the target node
        if distance(bloon['x'], bloon['y'], targetX, targetY) < bloon['speed']:
            bloon['targetNode'] += 1
            
            # Check if it reached the final node (end of the track)
            if bloon['targetNode'] >= len(app.path):
                app.lives -= 1
                app.bloons.pop(i) # Remove bloon
                
                # Trigger Game Over if lives hit 0
                if app.lives <= 0:
                    app.gameOver = True

    # --- 3. Tower Firing Logic ---
    for tower in app.towers:
        # Decrease cooldown timer
        if tower['cooldown'] > 0:
            tower['cooldown'] -= 1
            continue # Skip finding targets until reloaded
            
        # Look for a valid target in range
        for bloon in app.bloons:
            if distance(tower['x'], tower['y'], bloon['x'], bloon['y']) <= tower['range']:
                # Calculate angle to the bloon
                angle = math.atan2(bloon['y'] - tower['y'], bloon['x'] - tower['x'])
                
                # Fire a projectile at that angle
                newProj = {
                    'x': tower['x'], 
                    'y': tower['y'], 
                    'dx': 12 * math.cos(angle), # x velocity
                    'dy': 12 * math.sin(angle), # y velocity
                    'life': 30 # Disappears after 30 frames to avoid memory leaks
                }
                app.projectiles.append(newProj)
                
                # Reset tower cooldown (e.g., 20 frames = slightly faster than 1 sec)
                tower['cooldown'] = 20 
                
                # Stop looking for targets; only shoot one bloon per frame
                break 

    # --- 4. Moving and Colliding Projectiles ---
    # Iterate backwards because projectiles are destroyed on impact or timeout
    for i in range(len(app.projectiles) - 1, -1, -1):
        proj = app.projectiles[i]
        
        # Move the projectile
        proj['x'] += proj['dx']
        proj['y'] += proj['dy']
        proj['life'] -= 1
        
        # Remove dead projectiles that missed
        if proj['life'] <= 0:
            app.projectiles.pop(i)
            continue
            
        # Check for collision with any bloons
        hitTarget = False
        # Iterate backwards through bloons since they might be popped
        for j in range(len(app.bloons) - 1, -1, -1):
            bloon = app.bloons[j]
            
            # 15 is the "hitbox" radius of the bloon
            if distance(proj['x'], proj['y'], bloon['x'], bloon['y']) < 15: 
                bloon['health'] -= 1
                hitTarget = True
                
                # Handle popping the bloon
                if bloon['health'] <= 0:
                    app.money += 20
                    app.bloons.pop(j)
                    
                break # The projectile can only hit one bloon, so stop checking others
                
        # Remove the projectile if it successfully hit something
        if hitTarget:
            app.projectiles.pop(i)

# ==========================================
# DRAWING / RENDERING
# ==========================================

def redrawAll(app):
    # 1. Draw Background
    drawRect(0, 0, app.width, app.height, fill='forestGreen')
    
    # 2. Draw Path (Connecting the checkpoints)
    for i in range(len(app.path) - 1):
        x1, y1 = app.path[i]
        x2, y2 = app.path[i+1]
        # Draw the border first
        drawLine(x1, y1, x2, y2, fill='sienna', lineWidth=44) 
        # Then draw the main path
        drawLine(x1, y1, x2, y2, fill='tan', lineWidth=40)
        
    # 3. Draw Towers
    for tower in app.towers:
        # Draw the tower range indicator
        drawCircle(tower['x'], tower['y'], tower['range'], fill=None, border='black', dashes=True, opacity=30)
        
        # Draw the monkey/tower body
        drawCircle(tower['x'], tower['y'], 15, fill='saddleBrown')
        drawCircle(tower['x'], tower['y'], 8, fill='beige') 
        
    # 4. Draw Bloons
    for bloon in app.bloons:
        drawOval(bloon['x'], bloon['y'], 20, 26, fill=bloon['color'])

    # Draw preview tower at mouse position
    mx, my = app.mousePos
    drawCircle(mx, my, 80, fill=None, border='white', opacity=50) # Range preview
    drawCircle(mx, my, 15, fill='saddleBrown', opacity=50)        # Body preview
        
    # 5. Draw Projectiles
    for proj in app.projectiles:
        drawCircle(proj['x'], proj['y'], 4, fill='black')

    # 6. Draw UI
    drawRect(0, 0, 150, 70, fill='white', opacity=80)
    drawLabel(f'Money: ${app.money}', 10, 15, size=16, bold=True, align='left')
    drawLabel(f'Lives: {app.lives}', 10, 35, size=16, bold=True, align='left')
    drawLabel(f'Wave: {app.wave}', 10, 55, size=16, bold=True, align='left')
    
    # 7. Draw Game Over Screen
    if app.gameOver:
        drawRect(0, 0, app.width, app.height, fill='black', opacity=70)
        drawLabel('GAME OVER', app.width/2, app.height/2 - 20, size=40, fill='red', bold=True)
        drawLabel('You let too many bloons past!', app.width/2, app.height/2 + 20, size=16, fill='white')

runApp(width=400, height=400)