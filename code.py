import pygame
import random
import sys

# --- Configuration ---
FONT_SIZE_BASE = 10  # Base font size for the front layer
SCREEN_WIDTH = 0  # Will be set to full screen
SCREEN_HEIGHT = 0 # Will be set to full screen
FPS = 30  # Frames per second

# Character set (Katakana is often used for Matrix-like effects)
KATAKANA_CHARS = [chr(code) for code in range(0x30A0, 0x30FF + 1)]
# You can add numbers and other symbols if you like:
# KATAKANA_CHARS.extend([str(i) for i in range(10)])
# KATAKANA_CHARS.extend(['$', '+', '-', '*', '/', '=', '%', '"', "'", '#', '@', '&', '(', ')'])


class Symbol:
    def __init__(self, x, y, speed, first, color_base, font_size, layer_brightness_factor):
        self.x = x
        self.y = y
        self.speed = speed
        self.value = random.choice(KATAKANA_CHARS)
        self.interval = random.randrange(5, 20)  # How often to switch character
        self.first = first  # Is this the leading symbol in a stream?
        self.color_base = color_base
        self.font_size = font_size
        self.layer_brightness_factor = layer_brightness_factor # Overall brightness for this layer

    def set_random_symbol(self):
        if pygame.time.get_ticks() % self.interval == 0: # Simple timer
            self.value = random.choice(KATAKANA_CHARS)

    def draw(self, surface, font, position_in_stream, stream_length):
        # Calculate color based on position in stream and layer
        if self.first and position_in_stream == 0: # Leading symbol
            # Make it brighter than the base color, often white or very light version
            r = min(255, int(self.color_base[0] * 1.8 * self.layer_brightness_factor))
            g = min(255, int(self.color_base[1] * 1.8 * self.layer_brightness_factor))
            b = min(255, int(self.color_base[2] * 1.8 * self.layer_brightness_factor))
            if sum(self.color_base) > 30: # If not a very dark base color
                 color = (
                    min(255, self.color_base[0] + 150),
                    min(255, self.color_base[1] + 150),
                    min(255, self.color_base[2] + 150)
                 )
                 # Ensure it's still affected by layer brightness
                 color = (int(color[0] * self.layer_brightness_factor),
                          int(color[1] * self.layer_brightness_factor),
                          int(color[2] * self.layer_brightness_factor))
            else: # For very dark base colors, just make the tip whiteish
                color = (int(220 * self.layer_brightness_factor),
                         int(220 * self.layer_brightness_factor),
                         int(220 * self.layer_brightness_factor))

        else: # Body and tail
            # Fade out towards the tail
            # The closer to stream_length, the darker it gets
            fade_factor = (stream_length - position_in_stream) / stream_length
            fade_factor = max(0.1, fade_factor**1.5) # Sharper fade at the very end

            r = int(self.color_base[0] * fade_factor * self.layer_brightness_factor)
            g = int(self.color_base[1] * fade_factor * self.layer_brightness_factor)
            b = int(self.color_base[2] * fade_factor * self.layer_brightness_factor)
            color = (max(0, r), max(0, g), max(0, b))


        try:
            char_surface = font.render(self.value, True, color)
            surface.blit(char_surface, (self.x, self.y + position_in_stream * self.font_size))
        except pygame.error as e:
            print(f"Error rendering char '{self.value}': {e}")
            pass # Skip if char can't be rendered by font

    def rain(self):
        self.y = self.y + self.speed if self.y < SCREEN_HEIGHT else -self.font_size * random.randint(5,25) # Reset if off screen
        self.set_random_symbol()


class Stream:
    def __init__(self, x, color_base, layer_idx):
        self.x = x
        self.layer_idx = layer_idx # 0: front, 1: middle, 2: back
        self.symbols = []
        self.total_symbols = random.randint(8, 25) # Length of the stream
        self.speed = random.uniform(0.5 + (2-layer_idx)*0.8, 2.0 + (2-layer_idx)*2.0) # Slower for back layers
        self.color_base = color_base

        # Adjust font size and brightness based on layer
        if self.layer_idx == 0: # Front
            self.font_size = FONT_SIZE_BASE
            self.layer_brightness_factor = 1.0
        elif self.layer_idx == 1: # Middle
            self.font_size = int(FONT_SIZE_BASE * 0.8)
            self.layer_brightness_factor = 0.65
        else: # Back
            self.font_size = int(FONT_SIZE_BASE * 0.6)
            self.layer_brightness_factor = 0.35

        self.font = pygame.font.Font("arialuni.ttf" if sys.platform != "win32" else "msmincho.ttc", self.font_size) # MS Mincho for Japanese, Arial Unicode for others
        # Fallback font if specific one not found
        try:
            self.font = pygame.font.Font("arialuni.ttf" if sys.platform != "win32" else "msmincho.ttc", self.font_size)
        except FileNotFoundError:
            try:
                self.font = pygame.font.Font("Arial Unicode MS", self.font_size) # Common on Windows
            except FileNotFoundError:
                self.font = pygame.font.SysFont('arial', self.font_size) # Generic fallback

        self._generate_symbols()

    def _generate_symbols(self):
        # Start the stream off-screen or partially on-screen
        start_y = random.randrange(-SCREEN_HEIGHT, 0)
        for i in range(self.total_symbols):
            symbol = Symbol(
                self.x,
                start_y, # All symbols in a stream share the stream's head y for drawing logic
                self.speed,
                i == 0, # First symbol is the leader
                self.color_base,
                self.font_size,
                self.layer_brightness_factor
            )
            self.symbols.append(symbol)

    def update_and_draw(self, surface):
        # The first symbol (leader) dictates the y-position of the stream's head
        # and its raining behavior. Other symbols just follow for drawing.
        leader = self.symbols[0]
        leader.rain() # This updates leader.y and its value

        # If leader resets, the whole stream effectively resets its y position
        # and potentially its content due to random symbol generation.
        if leader.y < 0 and leader.speed > 0: # Just reset from top
             # Re-randomize speed and length for variety when it reappears
            self.total_symbols = random.randint(8, 25)
            self.speed = random.uniform(0.5 + (2-self.layer_idx)*0.8, 2.0 + (2-self.layer_idx)*2.0)
            for sym in self.symbols: # Update speed for all symbols in this stream
                sym.speed = self.speed
            # Ensure symbols list matches new total_symbols length
            current_len = len(self.symbols)
            if self.total_symbols > current_len:
                for i in range(self.total_symbols - current_len):
                    new_symbol = Symbol(self.x, leader.y, self.speed, False, self.color_base, self.font_size, self.layer_brightness_factor)
                    self.symbols.append(new_symbol)
            elif self.total_symbols < current_len:
                self.symbols = self.symbols[:self.total_symbols]
            
            # Re-assign first correctly
            if self.symbols:
                self.symbols[0].first = True
                for i in range(1, len(self.symbols)):
                    self.symbols[i].first = False


        for i, symbol in enumerate(self.symbols):
            # Update y for drawing based on leader's y
            # This makes them appear as a column
            symbol.y = leader.y # All symbols in a stream share the stream's head y for drawing logic
            if i > 0: # Non-leader symbols just update their value
                symbol.set_random_symbol()
            symbol.draw(surface, self.font, i, len(self.symbols))


def get_user_color():
    colors = {
        "green": (0, 255, 70),
        "blue": (0, 120, 255),
        "red": (255, 50, 50),
        "purple": (180, 0, 255),
        "cyan": (0, 255, 255),
        "yellow": (255,255,0)
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

    # Set up full screen
    screen_info = pygame.display.Info()
    SCREEN_WIDTH = screen_info.current_w
    SCREEN_HEIGHT = screen_info.current_h
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF)
    pygame.display.set_caption("Matrix Rain")
    clock = pygame.time.Clock()

    # Create streams for each layer
    streams_by_layer = [[], [], []] # Layer 0 (front), 1 (middle), 2 (back)
    
    # Calculate number of streams based on font size and screen width
    # Fewer streams for larger base font size
    num_cols_layer0 = SCREEN_WIDTH // FONT_SIZE_BASE
    
    # Layer 0 (Front) - Most dense
    for i in range(num_cols_layer0):
        if random.random() < 0.85: # Chance to have a stream in a column
            streams_by_layer[0].append(Stream(i * FONT_SIZE_BASE, user_color_base, 0))

    # Layer 1 (Middle) - Less dense
    font_size_layer1 = int(FONT_SIZE_BASE * 0.8)
    num_cols_layer1 = SCREEN_WIDTH // font_size_layer1
    for i in range(num_cols_layer1):
        if random.random() < 0.65:
             streams_by_layer[1].append(Stream(i * font_size_layer1, user_color_base, 1))

    # Layer 2 (Back) - Least dense
    font_size_layer2 = int(FONT_SIZE_BASE * 0.6)
    num_cols_layer2 = SCREEN_WIDTH // font_size_layer2
    for i in range(num_cols_layer2):
        if random.random() < 0.45:
            streams_by_layer[2].append(Stream(i * font_size_layer2, user_color_base, 2))


    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        screen.fill((0, 0, 0))  # Black background

        # Draw layers from back to front for correct overlap
        for layer_idx in range(2, -1, -1): # 2, 1, 0
            for stream in streams_by_layer[layer_idx]:
                stream.update_and_draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()