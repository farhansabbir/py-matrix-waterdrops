import pygame
import random
import sys

# --- Configuration ---
FONT_SIZE_BASE = 12
SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0
FPS = 40 # Slightly higher FPS can make the growth feel smoother

KATAKANA_CHARS = [chr(code) for code in range(0x30A0, 0x30FF + 1)]
# KATAKANA_CHARS.extend([str(i) for i in range(10)])
# KATAKANA_CHARS.extend(['$', '+', '*', '%', '#', '@', '&'])


class Symbol:
    def __init__(self, x, y, speed, color_base, font_size, layer_brightness_factor, is_leader=False):
        self.x = x
        self.y = y
        self.speed = speed # Speed of the leader primarily, followers keep up
        self.value = random.choice(KATAKANA_CHARS)
        self.interval = random.randrange(100, 250)
        self.last_switch_time = pygame.time.get_ticks()
        self.color_base = color_base
        self.font_size = font_size
        self.layer_brightness_factor = layer_brightness_factor
        self.is_leader = is_leader
        self.alpha = 255 # Used for tail fade of the entire stream

    def set_random_symbol(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_switch_time > self.interval:
            self.value = random.choice(KATAKANA_CHARS)
            self.last_switch_time = current_time

    def update_leader(self): # Only leader moves independently based on its speed
        self.y += self.speed
        self.set_random_symbol()

    def update_follower(self, leader_y, index_from_leader):
        # Followers position themselves relative to the leader's current y
        self.y = leader_y - (index_from_leader * self.font_size)
        self.set_random_symbol()


    def draw(self, surface, font, position_in_stream, stream_transition_length, overall_stream_alpha):
        color_tuple = (0,0,0)
        white_color = (230, 255, 230)

        if self.is_leader: # position_in_stream will be 0 for leader
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
            # Apply the stream's overall tail fade alpha, not individual symbol alpha here
            char_surface.set_alpha(overall_stream_alpha)
            surface.blit(char_surface, (self.x, self.y))
        except pygame.error:
            pass


class Stream:
    def __init__(self, x_col_index, color_base, layer_idx):
        self.layer_idx = layer_idx
        self.color_base = color_base
        self.symbols = [] # Active symbols in this stream
        self.spawn_new_symbol_timer = 0 # Used to time adding new symbols to the tail
        
        self.max_length = 0
        self.current_display_length = 0 # How many symbols are currently being *displayed*
        self.base_speed = 0 # Speed of the leading tip
        self.time_to_add_next_symbol = 0 # Governs how fast the stream "grows"
        self.initial_delay = 0
        self.transition_length = 0 # For white-to-base color

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
        self.has_started_falling = False # If the leader has begun its descent
        self.start_time = pygame.time.get_ticks() # For initial delay


    def reset_stream_properties(self, initial_setup=False):
        self.max_length = random.randint(10, 35)
        if self.layer_idx == 0:
            self.base_speed = random.uniform(3.0, 6.0)
        elif self.layer_idx == 1:
            self.base_speed = random.uniform(1.8, 3.8)
        else:
            self.base_speed = random.uniform(0.8, 2.2)
        
        # Time to add next symbol is related to speed: faster speed = faster growth
        self.time_to_add_next_symbol = int(self.font_size / self.base_speed * 1000 / FPS) # roughly
        self.time_to_add_next_symbol = max(30, min(120, self.time_to_add_next_symbol)) # Clamp it
        
        self.transition_length = random.randint(2, 5)

        if initial_setup:
            self.initial_delay = random.randint(0, 7000) # Wider initial spread
        else:
            self.initial_delay = random.randint(2000, 10000) # Longer delay for respawns
        
        self.symbols = [] # Clear symbols for a fresh start
        self.current_display_length = 0


    def update_and_draw(self, surface):
        current_ticks = pygame.time.get_ticks()

        if not self.has_started_falling:
            if current_ticks - self.start_time > self.initial_delay:
                self.has_started_falling = True
                # Add the very first leader symbol
                leader_y_start = -self.font_size # Start just above screen
                leader = Symbol(self.x, leader_y_start, self.base_speed, self.color_base, self.font_size, self.layer_brightness_factor, is_leader=True)
                self.symbols.append(leader)
                self.current_display_length = 1
                self.spawn_new_symbol_timer = current_ticks
            else:
                return # Not time to start this stream yet

        if not self.symbols: # Stream might have finished and cleared
            if self.has_started_falling: # It was falling, now it's done
                self.has_started_falling = False
                self.start_time = current_ticks # Reset timer for next initial_delay
                self.reset_stream_properties(initial_setup=False)
            return


        # --- Update leader ---
        leader = self.symbols[0]
        leader.update_leader()

        # --- Grow the stream from the leader ---
        if self.current_display_length < self.max_length and \
           current_ticks - self.spawn_new_symbol_timer > self.time_to_add_next_symbol:
            # Add a new symbol at the "top" of the currently displayed stream, which is where the leader *was*
            # or slightly above the current second symbol.
            # The new symbol's Y will be determined by the leader in the drawing phase.
            new_follower_y = leader.y - (self.current_display_length * self.font_size) # Tentative start based on leader
            
            # Create follower at the correct X, but its Y will be set relative to leader in draw
            follower = Symbol(self.x, new_follower_y, self.base_speed, self.color_base, self.font_size, self.layer_brightness_factor, is_leader=False)
            
            # Insert new follower right after the leader
            if len(self.symbols) == 1: # Only leader exists
                 self.symbols.append(follower)
            else:
                 self.symbols.insert(1, follower) # Insert to become the new second symbol

            self.current_display_length += 1
            self.spawn_new_symbol_timer = current_ticks
            # Trim if we somehow overshot max_length (shouldn't happen with current logic)
            # while len(self.symbols) > self.max_length:
            #     self.symbols.pop() # Remove from the very end (oldest follower)

        # --- Update followers and draw all symbols ---
        # The oldest symbol (end of the tail) determines the stream's overall alpha for fading out
        # Only fade if the stream is longer than its color transition part
        stream_alpha = 255
        if self.current_display_length > self.transition_length:
            # Calculate how far the last visible symbol is from its "full opaque" position
            # The stream starts fading when its tail (last symbol) passes a certain point relative to leader
            # Let's say, the tail starts fading when it's formed about half its max_length
            
            # If the *leader* is far down, the whole stream starts to fade.
            # This gives the "gradual fall off" effect for the entire line.
            if leader.y > SCREEN_HEIGHT * 0.6: # Start fading when leader past 60% of screen
                fade_progress = (leader.y - SCREEN_HEIGHT * 0.6) / (SCREEN_HEIGHT * 0.4)
                stream_alpha = max(0, int(255 * (1 - fade_progress**2)))


        for i, symbol in enumerate(self.symbols):
            if i > 0: # Followers update their position based on the leader
                symbol.update_follower(leader.y, i) # i is index_from_leader

            # Only draw if symbol is on screen (or close to it)
            if -self.font_size < symbol.y < SCREEN_HEIGHT + self.font_size:
                symbol.draw(surface, self.font, i, self.transition_length, stream_alpha)

        # --- Remove leader if it's completely off screen ---
        # This signifies the end of this stream's fall.
        if leader.y > SCREEN_HEIGHT + (self.max_length * self.font_size): # Leader far off screen
            self.symbols.clear() # Entire stream is gone
            self.current_display_length = 0
            # The check `if not self.symbols:` at the beginning of this function will handle reset.


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
    pygame.display.set_caption("Matrix Rain V")
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