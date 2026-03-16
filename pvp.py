from pynput import keyboard
import pyautogui


def on_press(key):
    try:
        if key.char == '2':
            # first left click
            pyautogui.click(button='left')
            # very short delay per requirement
            # press and release key 3
            pyautogui.press('3')
            # final left click
            pyautogui.click(button='left')
    except AttributeError:
        # ignore special keys
        pass


if __name__ == '__main__':
    print('Listening for key 2. Press ESC to quit.')
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

