import pygame
import random
import sys

# --- Configuration ---
FONT_SIZE_BASE = 12 # Slightly smaller base for more room for many layers
SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0
FPS = 20 # Can adjust if performance is an issue with more layers

KATAKANA_CHARS = [chr(code) for code in range(0x30A0, 0x30FF + 1)]
# KATAKANA_CHARS.extend([str(i) for i in range(10)])
# KATAKANA_CHARS.extend(['$', '+', '*', '%', '#', '@', '&'])

TOTAL_LAYERS = 2 # Increased from 3 to 6

class Symbol:
    def __init__(self, x, y, speed, color_base, font_size, layer_brightness_factor, is_leader=False):
        self.x = x
        self.y = y
        self.speed = speed
        self.value = random.choice(KATAKANA_CHARS)
        self.interval = random.randrange(100, 250)
        self.last_switch_time = pygame.time.get_ticks()
        self.color_base = color_base
        self.font_size = font_size
        self.layer_brightness_factor = layer_brightness_factor
        self.is_leader = is_leader
        self.alpha = 155

    def set_random_symbol(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_switch_time > self.interval:
            self.value = random.choice(KATAKANA_CHARS)
            self.last_switch_time = current_time

    def update(self): # Renamed from Symbol.update to avoid conflict if Stream also has update
        self.y += self.speed
        self.set_random_symbol()

    def draw(self, surface, font, position_in_stream, stream_transition_length):
        color_tuple = (0,0,0)
        white_color = (230, 255, 255)

        if self.is_leader:
            r = int(white_color[0] * self.layer_brightness_factor)
            g = int(white_color[1] * self.layer_brightness_factor)
            b = int(white_color[2] * self.layer_brightness_factor)
            color_tuple = (max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b)))
        elif position_in_stream < stream_transition_length:
            progress = position_in_stream / float(stream_transition_length)
            r_trans = int(white_color[0] * (1 - progress) + self.color_base[0] * progress)
            g_trans = int(white_color[1] * (1 - progress) + self.color_base[1] * progress)
            b_trans = int(white_color[2] * (1 - progress) + self.color_base[2] * progress)
            r = int(r_trans * self.layer_brightness_factor)
            g = int(g_trans * self.layer_brightness_factor)
            b = int(b_trans * self.layer_brightness_factor)
            color_tuple = (max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b)))
        else:
            r = int(self.color_base[0] * self.layer_brightness_factor)
            g = int(self.color_base[1] * self.layer_brightness_factor)
            b = int(self.color_base[2] * self.layer_brightness_factor)
            color_tuple = (max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b)))

        try:
            char_surface = font.render(self.value, True, color_tuple).convert_alpha()
            char_surface.set_alpha(self.alpha)
            surface.blit(char_surface, (self.x, self.y))
        except pygame.error:
            pass


class Stream:
    def __init__(self, x_col_index, color_base, layer_idx):
        self.layer_idx = layer_idx # 0 is front, TOTAL_LAYERS - 1 is backmost
        self.color_base = color_base
        self.symbols = []
        self.spawn_new_symbol_timer = 0
        
        self.max_length = 0
        self.base_speed = 0
        self.time_between_symbols = 0
        self.initial_delay = 0
        self.transition_length = 0

        # --- Layer Properties ---
        # Layer 0: Frontmost, brightest, fastest, largest
        # Layer TOTAL_LAYERS - 1: Backmost, dimmest, slowest, smallest
        
        # Calculate properties based on layer_idx relative to TOTAL_LAYERS
        # Brightness: from 1.0 (front) down to ~0.2 (back)
        self.layer_brightness_factor = 1.0 - (self.layer_idx / (TOTAL_LAYERS -1)) * 0.8 if TOTAL_LAYERS > 1 else 1.0
        self.layer_brightness_factor = max(0.15, self.layer_brightness_factor) # Ensure minimum visibility

        # Font size: from FONT_SIZE_BASE down to ~40% of it
        font_scale = 1.0 - (self.layer_idx / (TOTAL_LAYERS -1)) * 0.65 if TOTAL_LAYERS > 1 else 1.0
        self.font_size = int(FONT_SIZE_BASE * max(0.35, font_scale)) # Min font size about 35%
        self.font_size = max(6, self.font_size) # Absolute minimum font size

        self.x = x_col_index * self.font_size # X position based on this layer's font size

        try:
            self.font = pygame.font.Font("arialuni.ttf" if sys.platform != "win32" else "msmincho.ttc", self.font_size)
        except FileNotFoundError:
            try:
                self.font = pygame.font.Font("Arial Unicode MS", self.font_size)
            except FileNotFoundError:
                self.font = pygame.font.SysFont('arial', self.font_size, bold=(self.layer_idx < 2)) # Bold for front layers
        
        self.reset_stream_properties(initial_setup=True)
        self.has_started = False
        self.start_time = pygame.time.get_ticks()


    def reset_stream_properties(self, initial_setup=False):
        self.max_length = random.randint(8, 30 - self.layer_idx * 2) # Back layers can be shorter
        self.max_length = max(5, self.max_length)

        # Speed: From ~3.0-6.0 (front) down to ~0.5-1.5 (back)
        speed_scale_factor = 1.0 - (self.layer_idx / (TOTAL_LAYERS -1)) * 0.8 if TOTAL_LAYERS > 1 else 1.0
        min_speed = 0.5 + (2.5 * speed_scale_factor)
        max_speed = 1.5 + (4.5 * speed_scale_factor)
        self.base_speed = random.uniform(max(0.3, min_speed), max(0.6, max_speed))
        
        self.time_between_symbols = random.randint(50 + self.layer_idx * 10, 100 + self.layer_idx * 15)
        self.transition_length = random.randint(2, min(5, self.max_length -1 if self.max_length > 1 else 1) )


        if initial_setup:
            self.initial_delay = random.randint(0, 5000 + self.layer_idx * 1000) # Back layers can have more initial delay
        else:
            self.initial_delay = random.randint(1000, 8000 + self.layer_idx * 1500)

    def _add_symbol(self, is_leader=False): # Symbol objects are added to self.symbols
        start_y = -self.font_size * random.randint(1,5)
        symbol_speed = self.base_speed # All symbols in a stream now share the same speed
        # if is_leader: symbol_speed *= random.uniform(1.0, 1.05) # Leader slight speed boost

        new_sym = Symbol(self.x, start_y, symbol_speed, self.color_base, self.font_size, self.layer_brightness_factor, is_leader)
        self.symbols.append(new_sym)

    def update_and_draw(self, surface): # Method of Stream class
        current_ticks = pygame.time.get_ticks()

        if not self.has_started:
            if current_ticks - self.start_time > self.initial_delay:
                self.has_started = True
                self._add_symbol(is_leader=True)
                self.spawn_new_symbol_timer = current_ticks
            else:
                return

        # Add new symbols to the stream if it's not at max length
        if len(self.symbols) < self.max_length and \
           current_ticks - self.spawn_new_symbol_timer > self.time_between_symbols:
            if self.symbols: # Make sure there's a leader to follow
                self._add_symbol(is_leader=False)
            self.spawn_new_symbol_timer = current_ticks

        symbols_to_remove = []
        # Update and draw existing symbols
        for i, symbol in enumerate(self.symbols):
            symbol.update() # Call the renamed Symbol.update()
            
            fade_start_point = self.transition_length 
            if i > fade_start_point:
                relative_pos_in_tail = (i - fade_start_point) / max(1, (len(self.symbols) -1 - fade_start_point)) # Use current length
                symbol.alpha = max(0, int(255 * (1 - relative_pos_in_tail**1.8)))
            else:
                symbol.alpha = 255

            symbol.draw(surface, self.font, i, self.transition_length)

            if symbol.y > SCREEN_HEIGHT + self.font_size * 2: # If symbol is off screen
                symbols_to_remove.append(symbol)

        for sym in symbols_to_remove:
            if sym in self.symbols:
                self.symbols.remove(sym)

        # If all symbols of this stream are gone, reset it to fall again later
        if not self.symbols and self.has_started:
            self.has_started = False
            self.start_time = current_ticks # Reset start time for new initial delay
            self.reset_stream_properties(initial_setup=False)


def get_user_color():
    colors = {
        "green": (30, 255, 30), "blue": (0, 120, 255), "red": (255, 50, 50),
        "purple": (180, 0, 255), "cyan": (0, 255, 255), "yellow": (255,255,0),
        "white": (220,220,220)
    }
    while True:
        print("Available colors: " + ", ".join(colors.keys()))
        choice = input("Enter base color for letters (e.g., green): ").lower()
        if choice in colors:
            return colors[choice]
        else:
            return colors["green"]
        # print("Invalid color. Please choose from the list.")

def main():
    global SCREEN_WIDTH, SCREEN_HEIGHT

    pygame.init()
    user_color_base = get_user_color()

    screen_info = pygame.display.Info()
    SCREEN_WIDTH = screen_info.current_w
    SCREEN_HEIGHT = screen_info.current_h
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
    pygame.display.set_caption(f"Matrix Rain - {TOTAL_LAYERS} Layers")
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)

    streams_by_layer = [[] for _ in range(TOTAL_LAYERS)] # Initialize for all layers

    # --- Calculate num_cols and density for each layer ---
    # These will scale similarly to font_size and brightness
    layer_properties = []
    for i in range(TOTAL_LAYERS):
        font_scale = 1.0 - (i / (TOTAL_LAYERS -1)) * 0.65 if TOTAL_LAYERS > 1 else 1.0
        current_font_size = int(FONT_SIZE_BASE * max(0.35, font_scale))
        current_font_size = max(6, current_font_size)
        
        num_cols = SCREEN_WIDTH // max(1, current_font_size) # Avoid division by zero if font size too small
        
        # Density: from ~0.9 (front) down to ~0.2 (backmost)
        density_scale = 1.0 - (i / (TOTAL_LAYERS -1)) * 0.85 if TOTAL_LAYERS > 1 else 1.0
        density = max(0.15, 0.9 * density_scale) # Min density 15%
        
        layer_properties.append({'num_cols': num_cols, 'density': density, 'font_size': current_font_size})


    for layer_idx in range(TOTAL_LAYERS):
        props = layer_properties[layer_idx]
        for i in range(props['num_cols']):
            if random.random() < props['density']:
                streams_by_layer[layer_idx].append(Stream(i, user_color_base, layer_idx))


    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False

        screen.fill((0, 0, 0))

        # Draw layers from back (TOTAL_LAYERS - 1) to front (0)
        for layer_idx in range(TOTAL_LAYERS - 1, -1, -1):
            for stream in streams_by_layer[layer_idx]:
                stream.update_and_draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()