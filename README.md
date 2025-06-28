# Python Matrix Digital Rain

This project is a "digital rain" or "Matrix code" effect created using Python and the Pygame library. It simulates the iconic green falling characters from *The Matrix* films, featuring a multi-layered parallax effect for depth and realism.

 <!--- A placeholder GIF showing the effect --->

![Project Output](https://raw.githubusercontent.com/farhansabbir/py-matrix-waterdrops/main/screenshot.png)


## Features

*   **Multi-Layered Parallax Effect:** Multiple layers of streams fall at different speeds, sizes, and brightness levels to create a convincing illusion of depth.
*   **Dynamic Streams:** Each stream has randomized properties (length, speed, initial delay) for a varied and organic look.
*   **Authentic Visuals:**
    *   Uses Katakana characters, similar to the original effect.
    *   The leading character of each stream is brighter (white).
    *   A smooth color transition from the white leader to the base color.
    *   The tail of the stream gradually fades to black.
*   **Customizable:**
    *   The number of layers can be easily configured.
    *   The base color of the rain can be chosen by the user at runtime.
*   **Fullscreen & Performant:** Runs in fullscreen mode and is optimized to handle many streams across multiple layers smoothly.

---

## How to Run

### Prerequisites

*   Python 3.x
*   Pygame library

### Installation

1.  **Install Pygame:**
    ```bash
    pip install pygame
    ```

2.  **Fonts (Optional but Recommended):**
    For the best visual experience with Japanese characters, the script tries to use `msmincho.ttc` (on Windows) or `arialuni.ttf`. If these are not found, it falls back to system fonts, which may not render all characters correctly.

### Execution

Run the main script from your terminal:

```bash
python matrix_code.py
```

You will be prompted to choose a base color for the rain. After you enter a valid color, the simulation will start in fullscreen. Press the `ESC` key to exit.

---

## Code Explained (`matrix_code.py`)

The script is structured into two main classes, `Symbol` and `Stream`, and a `main` function to orchestrate the effect.

### Configuration

At the top of the file, you can find global constants to tweak the overall effect:

*   `FONT_SIZE_BASE`: The font size for the front-most layer. Other layers are scaled down from this.
*   `FPS`: Frames per second.
*   `KATAKANA_CHARS`: The list of characters to be used in the rain.
*   `TOTAL_LAYERS`: The number of parallax layers to generate. Increasing this adds more depth but may impact performance.

### `Symbol` Class

A `Symbol` object represents a single character in a stream.

*   **Attributes:** It stores its position (`x`, `y`), `speed`, `value` (the character itself), `color_base`, `font_size`, and whether it's the `is_leader` of a stream.
*   **`update()`:** This method is called every frame. It moves the symbol down the screen based on its `speed` and periodically switches its character value.
*   **`draw()`:** This is where the color logic happens.
    *   If the symbol `is_leader`, it's drawn in a bright white color.
    *   If it's in the "transition zone" (right behind the leader), its color is interpolated between white and the base color.
    *   Otherwise, it's drawn in the base color.
    *   The `layer_brightness_factor` is applied to dim the symbols on background layers.
    *   Finally, its `alpha` (transparency) is set, which is controlled by the `Stream` class for the tail-fading effect.

### `Stream` Class

A `Stream` object manages a column of falling `Symbol` objects. It's the core of the simulation.

*   **Initialization (`__init__`)**:
    *   It calculates its properties based on its `layer_idx`. Deeper layers (higher `layer_idx`) are made dimmer, smaller, and slower. This is the key to the parallax depth effect.
    *   It sets a random `max_length`, `base_speed`, and `initial_delay` for its first fall.

*   **`reset_stream_properties()`**: This method is called when a stream finishes its run and is about to respawn. It re-randomizes its length, speed, and delay, ensuring the rain looks constantly changing.

*   **`_add_symbol()`**: A helper method to create a new `Symbol` and add it to the stream's list of symbols.

*   **`update_and_draw()`**: This is the main logic method for the stream, called every frame.
    1.  **Start Delay:** It waits for its `initial_delay` before starting to fall.
    2.  **Growth:** It adds new `Symbol` objects over time until it reaches its `max_length`, creating the "growing" effect of the stream.
    3.  **Update Symbols:** It iterates through all its `Symbol` objects, calling their `update()` method.
    4.  **Fade Logic:** It calculates the `alpha` for each symbol based on its position in the stream. Symbols further down the tail get a lower alpha, creating the fade-out effect.
    5.  **Draw Symbols:** It calls each symbol's `draw()` method.
    6.  **Cleanup & Reset:** It removes symbols that have fallen off-screen. Once all symbols in a stream are gone, it calls `reset_stream_properties()` to prepare for its next fall.

### `main()` Function

This function sets up the environment and runs the main loop.

1.  **Setup:** Initializes Pygame, gets the user's color choice, and creates a fullscreen window.
2.  **Layer & Stream Creation:**
    *   It creates a list of lists, `streams_by_layer`.
    *   It loops from the front layer to the back, calculating the number of columns and stream density for each layer. Back layers are less dense.
    *   It populates `streams_by_layer` by creating `Stream` objects for each layer at random column positions.
3.  **Main Loop:**
    *   Handles events (like quitting with `ESC`).
    *   Fills the screen with black.
    *   **Crucially, it draws the layers from back to front (`TOTAL_LAYERS - 1` down to `0`).** This ensures that faster, brighter front layers are drawn on top of the slower, dimmer back layers.
    *   Updates the display and controls the frame rate.