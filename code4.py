import pygame
import random
import sys

# --- Configuration ---
FONT_SIZE_BASE = 12
SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0
FPS = 25

KATAKANA_CHARS = [chr(code) for code in range(0x30A0, 0x30FF + 1)]
# KATAKANA_CHARS.extend([str(i) for i in range(10)])
# KATAKANA_CHARS.extend(['$', '+', '*', '%', '#', '@', '&'])


class Symbol:
    def __init__(self, x, y, speed, color_base, font_size, layer_brightness_factor, is_leader=False):
        self.x = x
        self.y = y
        self.speed = speed
        self.value = random.choice(KATAKANA_CHARS)
        self.interval = random.randrange(100, 250)
        self.last_switch_time = pygame.time.get_ticks()
        self.color_base = color_base # e.g., (0, 255, 70) for green
        self.font_size = font_size
        self.layer_brightness_factor = layer_brightness_factor
        self.is_leader = is_leader
        self.alpha = 255

    def set_random_symbol(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_switch_time > self.interval:
            self.value = random.choice(KATAKANA_CHARS)
            self.last_switch_time = current_time

    def update(self):
        self.y += self.speed
        self.set_random_symbol()

    def draw(self, surface, font, position_in_stream, stream_transition_length):
        color_tuple = (0,0,0) # Default
        white_color = (230, 255, 230) # Slightly off-white for the tip

        if self.is_leader: # The very first symbol is brightest white
            r = int(white_color[0] * self.layer_brightness_factor)
            g = int(white_color[1] * self.layer_brightness_factor)
            b = int(white_color[2] * self.layer_brightness_factor)
            color_tuple = (max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b)))

        elif position_in_stream < stream_transition_length: # In the white-to-base transition zone
            # Interpolate from white to base_color
            # progress = 0 means pure white (like leader), progress = 1 means pure base_color
            progress = position_in_stream / float(stream_transition_length)
            
            r_trans = int(white_color[0] * (1 - progress) + self.color_base[0] * progress)
            g_trans = int(white_color[1] * (1 - progress) + self.color_base[1] * progress)
            b_trans = int(white_color[2] * (1 - progress) + self.color_base[2] * progress)
            
            # Apply layer brightness
            r = int(r_trans * self.layer_brightness_factor)
            g = int(g_trans * self.layer_brightness_factor)
            b = int(b_trans * self.layer_brightness_factor)
            color_tuple = (max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b)))
            
        else: # Body of the stream (base color)
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
        self.layer_idx = layer_idx
        self.color_base = color_base
        self.symbols = []
        self.spawn_new_symbol_timer = 0
        
        self.max_length = 0
        self.base_speed = 0
        self.time_between_symbols = 0
        self.initial_delay = 0
        self.transition_length = 0 # How many symbols for white-to-base transition

        if self.layer_idx == 0:
            self.font_size = FONT_SIZE_BASE
            self.layer_brightness_factor = 1.0
            self.x = x_col_index * FONT_SIZE_BASE
        elif self.layer_idx == 1:
            self.font_size = int(FONT_SIZE_BASE * 0.75)
            self.layer_brightness_factor = 0.60
            self.x = x_col_index * int(FONT_SIZE_BASE * 0.75)
        else:
            self.font_size = int(FONT_SIZE_BASE * 0.55)
            self.layer_brightness_factor = 0.30
            self.x = x_col_index * int(FONT_SIZE_BASE * 0.55)

        try:
            self.font = pygame.font.Font("arialuni.ttf" if sys.platform != "win32" else "msmincho.ttc", self.font_size)
        except FileNotFoundError:
            try:
                self.font = pygame.font.Font("Arial Unicode MS", self.font_size)
            except FileNotFoundError:
                self.font = pygame.font.SysFont('arial', self.font_size, bold=True)
        
        self.reset_stream_properties(initial_setup=True)
        self.has_started = False
        self.start_time = pygame.time.get_ticks()


    def reset_stream_properties(self, initial_setup=False):
        self.max_length = random.randint(10, 35) # Slightly longer max possible
        # Random speed for each new stream instance
        if self.layer_idx == 0:
            self.base_speed = random.uniform(3.0, 6.0) # Wider speed range
        elif self.layer_idx == 1:
            self.base_speed = random.uniform(1.8, 3.8)
        else:
            self.base_speed = random.uniform(0.8, 2.2)
        
        self.time_between_symbols = random.randint(50, 90) 
        self.transition_length = random.randint(2, 5) # 2 to 5 symbols for white to base color transition

        if initial_setup:
            self.initial_delay = random.randint(0, 5000)
        else:
            self.initial_delay = random.randint(1000, 8000)

    def _add_symbol(self, is_leader=False):
        start_y = -self.font_size * random.randint(1,5)
        symbol_speed = self.base_speed
        if is_leader: # Leader can be a bit faster to "pull"
            symbol_speed *= random.uniform(1.0, 1.05)

        new_sym = Symbol(self.x, start_y, symbol_speed, self.color_base, self.font_size, self.layer_brightness_factor, is_leader)
        self.symbols.append(new_sym)

    def update_and_draw(self, surface):
        current_ticks = pygame.time.get_ticks()

        if not self.has_started:
            if current_ticks - self.start_time > self.initial_delay:
                self.has_started = True
                self._add_symbol(is_leader=True)
                self.spawn_new_symbol_timer = current_ticks
            else:
                return

        if len(self.symbols) < self.max_length and \
           current_ticks - self.spawn_new_symbol_timer > self.time_between_symbols:
            if self.symbols:
                self._add_symbol(is_leader=False)
            self.spawn_new_symbol_timer = current_ticks

        symbols_to_remove = []
        for i, symbol in enumerate(self.symbols):
            symbol.update()
            
            # Alpha fading for the tail
            # The leader (i=0) and transition symbols are handled by their color logic mostly
            # Tail fading starts after the color transition zone
            fade_start_point = self.transition_length 
            if i > fade_start_point:
                # Relative position in the purely base-colored tail
                relative_pos_in_tail = (i - fade_start_point) / max(1, (self.max_length - fade_start_point))
                symbol.alpha = max(0, int(255 * (1 - relative_pos_in_tail**1.8))) # Slightly sharper fade
            else:
                symbol.alpha = 255 # Leader and transition zone are fully opaque

            # Pass current position in stream for color calculation
            symbol.draw(surface, self.font, i, self.transition_length)

            if symbol.y > SCREEN_HEIGHT + self.font_size * 2:
                symbols_to_remove.append(symbol)

        for sym in symbols_to_remove:
            if sym in self.symbols:
                self.symbols.remove(sym)

        if not self.symbols and self.has_started:
            self.has_started = False
            self.start_time = current_ticks
            self.reset_stream_properties(initial_setup=False)


def get_user_color():
    colors = {
        "green": (0, 255, 70), "blue": (0, 120, 255), "red": (255, 50, 50),
        "purple": (180, 0, 255), "cyan": (0, 255, 255), "yellow": (255,255,0),
        "white": (220,220,220) # User can choose white as base, tip will still be brighter white
    }
    while True:
        print("Available colors: " + ", ".join(colors.keys()))
        choice = input("Enter base color for letters (e.g., green): ").lower()
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
    pygame.display.set_caption("Matrix Rain IV")
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)

    streams_by_layer = [[], [], []]

    num_cols_layer0 = SCREEN_WIDTH // FONT_SIZE_BASE
    num_cols_layer1 = SCREEN_WIDTH // int(FONT_SIZE_BASE * 0.75)
    num_cols_layer2 = SCREEN_WIDTH // int(FONT_SIZE_BASE * 0.55)

    density_layer0 = 0.9
    density_layer1 = 0.7
    density_layer2 = 0.5

    for layer_idx, num_cols, density in zip(range(3), [num_cols_layer0, num_cols_layer1, num_cols_layer2], [density_layer0, density_layer1, density_layer2]):
        for i in range(num_cols):
            if random.random() < density:
                streams_by_layer[layer_idx].append(Stream(i, user_color_base, layer_idx))


    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False

        screen.fill((0, 0, 0))

        for layer_idx in range(2, -1, -1): # Draw back to front
            for stream in streams_by_layer[layer_idx]:
                stream.update_and_draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()