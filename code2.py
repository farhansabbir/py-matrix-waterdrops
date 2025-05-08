import pygame
import random
import sys

# --- Configuration ---
FONT_SIZE_BASE = 22  # Base font size for the front layer
SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0
FPS = 25  # Slightly higher FPS for smoother rain

KATAKANA_CHARS = [chr(code) for code in range(0x30A0, 0x30FF + 1)]
# KATAKANA_CHARS.extend([str(i) for i in range(10)]) # Optional: add numbers
# KATAKANA_CHARS.extend(['$', '+', '*', '%', '#', '@', '&']) # Optional: add symbols


class Symbol:
    def __init__(self, x, y, speed, color_base, font_size, layer_brightness_factor, is_leader=False):
        self.x = x
        self.y = y
        self.speed = speed # Speed of this individual symbol
        self.value = random.choice(KATAKANA_CHARS)
        self.interval = random.randrange(100, 250) # Milliseconds to switch character
        self.last_switch_time = pygame.time.get_ticks()
        self.color_base = color_base
        self.font_size = font_size
        self.layer_brightness_factor = layer_brightness_factor
        self.is_leader = is_leader # Is this the very first (brightest) symbol of a stream?
        self.alpha = 255 # For fading tail

    def set_random_symbol(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_switch_time > self.interval:
            self.value = random.choice(KATAKANA_CHARS)
            self.last_switch_time = current_time

    def update(self):
        self.y += self.speed
        self.set_random_symbol()

    def draw(self, surface, font):
        # Determine color: leader is brightest, others are base color (alpha will handle fade)
        if self.is_leader:
            # Make it brighter than the base color, often white or very light version
            r_tip = min(255, int(self.color_base[0] * 1.5 + 100)) # Add fixed brightness for tip
            g_tip = min(255, int(self.color_base[1] * 1.5 + 100))
            b_tip = min(255, int(self.color_base[2] * 1.5 + 100))
            # Ensure it's still affected by layer brightness and alpha
            color_tuple = (
                max(0,min(255,int(r_tip * self.layer_brightness_factor))),
                max(0,min(255,int(g_tip * self.layer_brightness_factor))),
                max(0,min(255,int(b_tip * self.layer_brightness_factor)))
            )
        else:
            color_tuple = (
                max(0,min(255,int(self.color_base[0] * self.layer_brightness_factor))),
                max(0,min(255,int(self.color_base[1] * self.layer_brightness_factor))),
                max(0,min(255,int(self.color_base[2] * self.layer_brightness_factor)))
            )

        try:
            # Create a surface for the character to handle per-pixel alpha
            char_surface = font.render(self.value, True, color_tuple).convert_alpha()
            char_surface.set_alpha(self.alpha)
            surface.blit(char_surface, (self.x, self.y))
        except pygame.error as e:
            # print(f"Error rendering char '{self.value}' with font size {self.font_size}: {e}")
            pass


class Stream:
    def __init__(self, x_col_index, color_base, layer_idx):
        self.layer_idx = layer_idx  # 0: front, 1: middle, 2: back
        self.color_base = color_base
        self.symbols = [] # List of active symbols in this stream
        self.max_length = random.randint(10, 30) # Max symbols in this stream at any time
        self.current_length = 0 # How many symbols are currently visible
        self.spawn_new_symbol_timer = 0
        self.time_between_symbols = 70 # Milliseconds between spawning symbols in the stream

        # Adjust font size, brightness, and speed based on layer
        if self.layer_idx == 0:  # Front
            self.font_size = FONT_SIZE_BASE
            self.layer_brightness_factor = 1.0
            self.base_speed = random.uniform(3.5, 5.5)
            self.x = x_col_index * FONT_SIZE_BASE
        elif self.layer_idx == 1:  # Middle
            self.font_size = int(FONT_SIZE_BASE * 0.75)
            self.layer_brightness_factor = 0.60
            self.base_speed = random.uniform(2.0, 3.5)
            self.x = x_col_index * int(FONT_SIZE_BASE * 0.75) # Use layer-specific font size for x
        else:  # Back
            self.font_size = int(FONT_SIZE_BASE * 0.55)
            self.layer_brightness_factor = 0.30
            self.base_speed = random.uniform(1.0, 2.0)
            self.x = x_col_index * int(FONT_SIZE_BASE * 0.55) # Use layer-specific font size for x

        # Fallback font loading
        try:
            self.font = pygame.font.Font("arialuni.ttf" if sys.platform != "win32" else "msmincho.ttc", self.font_size)
        except FileNotFoundError:
            try:
                self.font = pygame.font.Font("Arial Unicode MS", self.font_size)
            except FileNotFoundError:
                self.font = pygame.font.SysFont('arial', self.font_size, bold=True)


        # Initial delay before this stream starts raining
        self.initial_delay = random.randint(0, 5000) # Up to 5 seconds delay
        self.has_started = False
        self.start_time = pygame.time.get_ticks()


    def _add_symbol(self, is_leader=False):
        # New symbols start at the top (or slightly above)
        # If it's not the leader, it starts where the previous symbol was, creating the trail
        start_y = 0
        if self.symbols and not is_leader: # If adding to an existing trail
            start_y = self.symbols[-1].y - self.font_size # Start just above the last symbol
        else: # Leader or first symbol
            start_y = -self.font_size * random.randint(1,5) # Start off screen

        symbol_speed = self.base_speed # All symbols in a stream move at roughly same base speed
        # Leader can be slightly faster to "pull" the stream
        if is_leader:
            symbol_speed *= random.uniform(1.0, 1.1)

        new_sym = Symbol(self.x, start_y, symbol_speed, self.color_base, self.font_size, self.layer_brightness_factor, is_leader)
        self.symbols.append(new_sym)
        self.current_length += 1

    def update_and_draw(self, surface):
        current_ticks = pygame.time.get_ticks()

        if not self.has_started:
            if current_ticks - self.start_time > self.initial_delay:
                self.has_started = True
                self._add_symbol(is_leader=True) # Add the first, leading symbol
                self.spawn_new_symbol_timer = current_ticks
            else:
                return # Not time to start this stream yet

        # Spawn new symbols to create the falling line effect
        if self.current_length < self.max_length and \
           current_ticks - self.spawn_new_symbol_timer > self.time_between_symbols:
            if self.symbols: # Ensure there's a leader to follow
                self._add_symbol(is_leader=False)
            self.spawn_new_symbol_timer = current_ticks

        # Update and draw existing symbols
        symbols_to_remove = []
        for i, symbol in enumerate(self.symbols):
            symbol.update()
            # Fade out the tail
            # Alpha decreases as the symbol gets further down the stream (older)
            # The first few symbols (closer to the leader) should be fully opaque
            if not symbol.is_leader:
                # i is index, 0 is leader. So (i) is distance from leader.
                # Fade starts after a few symbols
                fade_start_index = 3
                if i > fade_start_index:
                    # Calculate fade based on how far it is from the leader, up to max_length
                    # Relative position in the visible part of the stream
                    relative_pos_in_tail = (i - fade_start_index) / (self.max_length - fade_start_index)
                    symbol.alpha = max(0, int(255 * (1 - relative_pos_in_tail**1.5))) # Sharper fade
                else:
                    symbol.alpha = 255
            else: # Leader is always opaque
                symbol.alpha = 255

            symbol.draw(surface, self.font)

            if symbol.y > SCREEN_HEIGHT + self.font_size: # If symbol is off screen
                symbols_to_remove.append(symbol)

        for sym in symbols_to_remove:
            self.symbols.remove(sym)
            self.current_length -=1

        # If all symbols of this stream are gone, reset it to fall again later
        if not self.symbols and self.has_started:
            self.has_started = False # It will re-evaluate initial_delay
            self.start_time = current_ticks
            self.initial_delay = random.randint(1000, 8000) # Longer delay after finishing
            self.max_length = random.randint(10, 30) # New random length for next fall


def get_user_color():
    colors = {
        "green": (0, 255, 70), "blue": (0, 120, 255), "red": (255, 50, 50),
        "purple": (180, 0, 255), "cyan": (0, 255, 255), "yellow": (255,255,0),
        "white": (220,220,220)
    }
    while True:
        print("Available colors: " + ", ".join(colors.keys()))
        choice = input("Enter color for letters (e.g., green): ").lower()
        if choice in colors:
            return colors[choice]
        print("Invalid color. Please choose from the list.")

def main():
    global SCREEN_WIDTH, SCREEN_HEIGHT

    pygame.init()
    user_color_base = get_user_color()

    screen_info = pygame.display.Info()
    SCREEN_WIDTH = screen_info.current_w
    SCREEN_HEIGHT = screen_info.current_h
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
    pygame.display.set_caption("Matrix Rain II")
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False) # Hide mouse cursor

    streams_by_layer = [[], [], []] # Layer 0 (front), 1 (middle), 2 (back)

    # Calculate number of columns for each layer based on its font size
    num_cols_layer0 = SCREEN_WIDTH // FONT_SIZE_BASE
    num_cols_layer1 = SCREEN_WIDTH // int(FONT_SIZE_BASE * 0.75)
    num_cols_layer2 = SCREEN_WIDTH // int(FONT_SIZE_BASE * 0.55)

    density_layer0 = 0.9  # Higher chance for a stream
    density_layer1 = 0.7
    density_layer2 = 0.5

    for i in range(num_cols_layer0):
        if random.random() < density_layer0:
            streams_by_layer[0].append(Stream(i, user_color_base, 0))
    for i in range(num_cols_layer1):
        if random.random() < density_layer1:
            streams_by_layer[1].append(Stream(i, user_color_base, 1))
    for i in range(num_cols_layer2):
        if random.random() < density_layer2:
            streams_by_layer[2].append(Stream(i, user_color_base, 2))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False

        screen.fill((0, 0, 0)) # Black background

        # Draw layers from back to front
        for layer_idx in range(2, -1, -1): # 2, 1, 0
            for stream in streams_by_layer[layer_idx]:
                stream.update_and_draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()