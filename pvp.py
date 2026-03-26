from pynput import keyboard
import pyautogui
import time
import threading

# Configurable macro map
# Add more entries to scale your macro system.
macro_definitions = {
    '2': {
        'type': 'press',
        'action': lambda: (
            pyautogui.click(button='left'),
            time.sleep(0.001),
            pyautogui.press('3'),
            pyautogui.click(button='left')
        ),
    },
    't': {
        'type': 'hold',
        'hold_delay_ms': 25,
        'hold_duration_ms': 500,  # set how long to keep held if user only wants max duration
    },
}

macro_enabled = False
hold_timer = None
held_key = None
held_key_release_time = None


def release_held_mouse():
    global held_key, hold_timer
    if held_key:
        pyautogui.mouseUp(button='left')
        held_key = None
    if hold_timer:
        hold_timer = None


def start_hold_macro(key_char, definition):
    global held_key, hold_timer
    if 'hold_duration_ms' not in definition:
        return

    pyautogui.click(button='left')
    time.sleep(definition.get('hold_delay_ms', 0) / 1000.0)
    pyautogui.mouseDown(button='left')
    held_key = key_char

    duration = definition['hold_duration_ms'] / 1000.0
    if hold_timer:
        hold_timer.cancel()
    hold_timer = threading.Timer(duration, release_held_mouse)
    hold_timer.start()


def execute_macro(key_char):
    key_char = key_char.lower()
    if key_char not in macro_definitions:
        return

    definition = macro_definitions[key_char]
    if definition['type'] == 'press':
        definition['action']()
    elif definition['type'] == 'hold':
        start_hold_macro(key_char, definition)


def on_press(key):
    global hold_timer, macro_enabled
    try:
        if key == keyboard.Key.space:
            macro_enabled = True
            print('Macro mode enabled (space pressed).')
            return

        if not macro_enabled:
            return

        if key.char == '2':
            execute_macro('2')
        elif key.char.lower() == 't':
            execute_macro('t')
    except AttributeError:
        pass


def on_release(key):
    global hold_timer, held_key
    try:
        if key.char.lower() == 't' and held_key == 't':
            if hold_timer:
                hold_timer.cancel()
                hold_timer = None
            release_held_mouse()
    except AttributeError:
        pass



if __name__ == '__main__':
    print('Listening for key 2 and T. Press ESC to quit.')
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

