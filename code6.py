import pygame
import random
import sys

# --- Configuration ---
FONT_SIZE_BASE = 12
SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0
FPS = 35

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
        self.color_base = color_base
        self.font_size = font_size
        self.layer_brightness_factor = layer_brightness_factor
        self.is_leader = is_leader
        self.alpha = 255 # This will be set by the Stream for tail fade

    def set_random_symbol(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_switch_time > self.interval:
            self.value = random.choice(KATAKANA_CHARS)
            self.last_switch_time = current_time

    def update_leader(self):
        self.y += self.speed
        self.set_random_symbol()

    def update_follower(self, leader_y, index_from_leader):
        self.y = leader_y - (index_from_leader * self.font_size)
        self.set_random_symbol()

    def draw(self, surface, font, position_in_stream, stream_transition_length):
        color_tuple = (0,0,0)
        white_color = (230, 255, 230)

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
            char_surface.set_alpha(self.alpha) # Use the alpha set by the Stream
            surface.blit(char_surface, (self.x, self.y))
        except pygame.error:
            pass


class Stream:
    def __init__(self, x_col_index, color_base, layer_idx):
        self.layer_idx = layer_idx
        self.color_base = color_base
        self.symbols = []
        self.spawn_new_symbol_timer = 0
        
        self.target_max_length = 0 # The desired length for this fall
        self.current_length_on_screen = 0 # How many symbols are actually being shown
        self.base_speed = 0
        self.time_to_add_next_symbol = 0
        self.initial_delay = 0
        self.transition_length = 0

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
        self.has_started_falling = False
        self.start_time = pygame.time.get_ticks()


    def reset_stream_properties(self, initial_setup=False):
        self.target_max_length = random.randint(8, 30) # Random length for this fall
        # Random speed for this fall
        if self.layer_idx == 0:
            self.base_speed = random.uniform(3.0, 6.0)
        elif self.layer_idx == 1:
            self.base_speed = random.uniform(1.8, 3.8)
        else:
            self.base_speed = random.uniform(0.8, 2.2)
        
        self.time_to_add_next_symbol = int(self.font_size / max(0.1, self.base_speed) * 1000 / FPS)
        self.time_to_add_next_symbol = max(30, min(120, self.time_to_add_next_symbol))
        
        self.transition_length = random.randint(2, min(5, self.target_max_length -1 if self.target_max_length > 1 else 1) ) # Ensure transition is not longer than stream

        if initial_setup:
            self.initial_delay = random.randint(0, 7000)
        else:
            self.initial_delay = random.randint(2000, 10000)
        
        self.symbols = []
        self.current_length_on_screen = 0


    def update_and_draw(self, surface):
        current_ticks = pygame.time.get_ticks()

        if not self.has_started_falling:
            if current_ticks - self.start_time > self.initial_delay:
                self.has_started_falling = True
                leader_y_start = -self.font_size
                leader = Symbol(self.x, leader_y_start, self.base_speed, self.color_base, self.font_size, self.layer_brightness_factor, is_leader=True)
                self.symbols.append(leader)
                self.current_length_on_screen = 1
                self.spawn_new_symbol_timer = current_ticks
            else:
                return

        if not self.symbols:
            if self.has_started_falling:
                self.has_started_falling = False
                self.start_time = current_ticks
                self.reset_stream_properties(initial_setup=False)
            return

        leader = self.symbols[0]
        leader.update_leader()

        # Grow the stream if it hasn't reached its target_max_length for this fall
        if self.current_length_on_screen < self.target_max_length and \
           current_ticks - self.spawn_new_symbol_timer > self.time_to_add_next_symbol:
            follower_y_start = leader.y - (self.current_length_on_screen * self.font_size)
            follower = Symbol(self.x, follower_y_start, self.base_speed, self.color_base, self.font_size, self.layer_brightness_factor, is_leader=False)
            
            if len(self.symbols) == self.current_length_on_screen: # Normal growth
                 self.symbols.append(follower) # Add to end, which becomes the new tail
            else: # Should ideally not happen, but as a fallback, insert
                 self.symbols.insert(self.current_length_on_screen, follower)

            self.current_length_on_screen += 1
            self.spawn_new_symbol_timer = current_ticks

        # Update followers' positions and calculate alpha for tail fade
        symbols_to_render_this_frame = []
        leader_y_current = leader.y # Cache leader's y for this frame

        for i, symbol in enumerate(self.symbols):
            if i > 0: # Is a follower
                symbol.update_follower(leader_y_current, i)

            # Calculate alpha for tail fade
            # The fade starts after the color transition zone and applies to the "body" of the stream
            # It depends on the symbol's position relative to the *current end* of the visible stream
            
            # Only apply tail fade to symbols *after* the color transition part
            if i >= self.transition_length:
                # Position within the purely base-colored part of the stream
                pos_in_tail = i - self.transition_length
                # Total length of the purely base-colored part
                tail_segment_length = self.current_length_on_screen - self.transition_length
                
                if tail_segment_length > 0:
                    # Fade progress: 0 at start of tail segment, 1 at end of tail segment
                    fade_progress = pos_in_tail / float(tail_segment_length)
                    symbol.alpha = max(0, int(255 * (1 - fade_progress**1.8))) # Sharper fade
                else:
                    symbol.alpha = 255 # If tail segment is zero (e.g. only transition symbols), fully opaque
            else:
                symbol.alpha = 255 # Leader and transition symbols are fully opaque (color handles their look)

            # Only draw if symbol is on screen (or close to it)
            if -self.font_size < symbol.y < SCREEN_HEIGHT + self.font_size:
                symbols_to_render_this_frame.append((symbol, i)) # Keep track of its original index for color

        # Draw symbols (could be done in the loop above, but separating for clarity)
        for symbol_tuple in symbols_to_render_this_frame:
            symbol_to_draw, original_index = symbol_tuple
            symbol_to_draw.draw(surface, self.font, original_index, self.transition_length)


        # Remove leader (and thus the stream) if it's completely off screen
        # The stream "dies" when its leader has fallen far enough that its *entire max length* would be off-screen.
        if leader.y > SCREEN_HEIGHT + (self.target_max_length * self.font_size):
            self.symbols.clear()
            self.current_length_on_screen = 0
            # The `if not self.symbols:` check at the start of the function will handle the reset.


def get_user_color():
    colors = {
        "green": (0, 255, 70), "blue": (0, 120, 255), "red": (255, 50, 50),
        "purple": (180, 0, 255), "cyan": (0, 255, 255), "yellow": (255,255,0),
        "white": (220,220,220)
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
    pygame.display.set_caption("Matrix Rain VI")
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

        for layer_idx in range(2, -1, -1):
            for stream in streams_by_layer[layer_idx]:
                stream.update_and_draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()