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
    # Shifted the 400s to 340s so the thick path fits entirely on screen
    app.path = [(0, 100), (200, 100), (200, 300), (340, 300), (340, -50)]
    
    # --- Timing ---
    app.stepsPerSecond = 30
    app.timer = 0

    app.mousePos = (0, 0)
    app.placingTower = True # Always showing a preview for now

    # --- Bloon Blueprints ---
    # The key (1, 2, 3) is the tier/health level. 
    app.bloonTypes = {
        1: {'color': 'red', 'speed': 3, 'reward': 20},
        2: {'color': 'blue', 'speed': 5, 'reward': 20},
        # You can easily add more later just by uncommenting/adding lines!
        3: {'color': 'green', 'speed': 7, 'reward': 20},
        4: {'color': 'yellow', 'speed': 9, 'reward': 20}
    }

# ==========================================
# CONTROLS
# ==========================================

def onMouseMove(app, mouseX, mouseY):
    app.mousePos = (mouseX, mouseY)

def onMousePress(app, mouseX, mouseY):
    # --- Restart Button Logic ---
    if app.gameOver:
        # Check if the click was inside the button's boundaries
        # x between 140 and 260 (center 200 +/- 60)
        # y between 230 and 270 (center 200 + 30, height 40)
        if (app.width/2 - 60 <= mouseX <= app.width/2 + 60 and 
            app.height/2 + 30 <= mouseY <= app.height/2 + 70):
            onAppStart(app) # Instantly resets the entire game!
        return # Stop checking for tower placements if game is over
    
    # --- Tower Placement Logic ---
    towerCost = 200
    towerRange = 80
    
    # Check if they have money AND the placement is valid
    if app.money >= towerCost and isValidPlacement(app, mouseX, mouseY):
        newTower = {
            'x': mouseX, 
            'y': mouseY, 
            'range': towerRange, 
            'cooldown': 0 
        }
        app.towers.append(newTower)
        app.money -= towerCost
    elif app.money < towerCost:
        print("Not enough money!")
    else:
        print("Invalid placement!")

# ==========================================
# CORE GAME LOGIC
# ==========================================

def isValidPlacement(app, mouseX, mouseY):
    towerRadius = 15
    pathRadius = 22 # Half of the 44 lineWidth
    
    # 1. Check tower overlap
    for tower in app.towers:
        # Multiply by 2 because we need the distance between two centers
        if distance(mouseX, mouseY, tower['x'], tower['y']) < (towerRadius * 2):
            return False
            
    # 2. Check path overlap
    for i in range(len(app.path) - 1):
        x1, y1 = app.path[i]
        x2, y2 = app.path[i+1]
        
        # Clamp the coordinates to find the closest point on the path segment
        closestX = max(min(x1, x2), min(mouseX, max(x1, x2)))
        closestY = max(min(y1, y2), min(mouseY, max(y1, y2)))
        
        # If the distance is less than the tower + path radii, it's overlapping
        if distance(mouseX, mouseY, closestX, closestY) < (towerRadius + pathRadius):
            return False
            
    return True

def onStep(app):
    # Stop processing logic if the game is over
    if app.gameOver: return
    
    app.timer += 1
    
    spawnRate = max(10, 30 - (app.wave * 2))
    # --- 1. Spawning Bloons ---
    # Spawn a new bloon based on the spawnRate
    if app.timer % spawnRate == 0:
        startX, startY = app.path[0]
        
        # Determine the hardest bloon allowed for the current wave (Caps at 4 for Yellow)
        highestTierAvailable = min(app.wave, 4)
        
        # Cycle through the available tiers so you get a mix of colors
        startingTier = (app.timer // spawnRate) % highestTierAvailable + 1
        
        newBloon = {
            'x': startX, 
            'y': startY, 
            'targetNode': 1,
            'tier': startingTier, 
            'speed': app.bloonTypes[startingTier]['speed'],
            'color': app.bloonTypes[startingTier]['color']
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
                
                # Deduct lives equal to the bloon's remaining layers (tier)
                app.lives -= bloon['tier'] 
                
                app.bloons.pop(i) # Remove bloon
                
                # Trigger Game Over if lives drop to 0 or below
                if app.lives <= 0:
                    app.lives = 0 # Prevents the UI from showing negative lives
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
                
                # 1. Give money for popping the CURRENT layer
                app.money += app.bloonTypes[bloon['tier']]['reward']
                
                # 2. Downgrade the bloon's tier
                bloon['tier'] -= 1
                hitTarget = True
                
                # 3. Update stats if it survived, otherwise remove it entirely
                if bloon['tier'] > 0:
                    bloon['color'] = app.bloonTypes[bloon['tier']]['color']
                    bloon['speed'] = app.bloonTypes[bloon['tier']]['speed']
                else:
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
        
        # Draw the line segments
        drawLine(x1, y1, x2, y2, fill='sienna', lineWidth=44) 
        drawLine(x1, y1, x2, y2, fill='tan', lineWidth=40)
        
        # Draw circles at the nodes to round the corners
        drawCircle(x1, y1, 22, fill='sienna')
        drawCircle(x1, y1, 20, fill='tan')
        drawCircle(x2, y2, 22, fill='sienna')
        drawCircle(x2, y2, 20, fill='tan')
        
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
        drawLabel('GAME OVER', app.width/2, app.height/2 - 40, size=40, fill='red', bold=True)
        drawLabel('You let too many bloons past!', app.width/2, app.height/2, size=16, fill='white')
        
        # Draw the Restart Button
        buttonX = app.width/2 - 60
        buttonY = app.height/2 + 30
        drawRect(buttonX, buttonY, 120, 40, fill='forestGreen', border='white')
        drawLabel('Play Again', app.width/2, buttonY + 20, size=16, fill='white', bold=True)

runApp(width=400, height=400)