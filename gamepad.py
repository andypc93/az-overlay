"""Xbox / PlayStation controller input via SDL's game-controller API (pygame-ce).

SDL maps both Xbox and DualShock/DualSense pads onto the same logical layout,
so templates use one vocabulary:

  buttons: a b x y back guide start leftstick rightstick leftshoulder
           rightshoulder dpup dpdown dpleft dpright misc1 touchpad
           paddle1 paddle2 paddle3 paddle4
  axes:    leftx lefty rightx righty lefttrigger righttrigger   (-1..1 / 0..1)

Input ids used in profiles are "gp:<name>". Everything degrades gracefully:
no pygame or no controller means poll() returns nothing.
"""

import os
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # no window, we only want input
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

try:
    import pygame
    from pygame._sdl2 import controller as sdl_controller
except Exception:  # pragma: no cover - optional dependency
    pygame = None
    sdl_controller = None

BUTTONS = {
    "a": "CONTROLLER_BUTTON_A", "b": "CONTROLLER_BUTTON_B",
    "x": "CONTROLLER_BUTTON_X", "y": "CONTROLLER_BUTTON_Y",
    "back": "CONTROLLER_BUTTON_BACK", "guide": "CONTROLLER_BUTTON_GUIDE",
    "start": "CONTROLLER_BUTTON_START",
    "leftstick": "CONTROLLER_BUTTON_LEFTSTICK", "rightstick": "CONTROLLER_BUTTON_RIGHTSTICK",
    "leftshoulder": "CONTROLLER_BUTTON_LEFTSHOULDER", "rightshoulder": "CONTROLLER_BUTTON_RIGHTSHOULDER",
    "dpup": "CONTROLLER_BUTTON_DPAD_UP", "dpdown": "CONTROLLER_BUTTON_DPAD_DOWN",
    "dpleft": "CONTROLLER_BUTTON_DPAD_LEFT", "dpright": "CONTROLLER_BUTTON_DPAD_RIGHT",
    "misc1": "CONTROLLER_BUTTON_MISC1", "touchpad": "CONTROLLER_BUTTON_TOUCHPAD",
    "paddle1": "CONTROLLER_BUTTON_PADDLE1", "paddle2": "CONTROLLER_BUTTON_PADDLE2",
    "paddle3": "CONTROLLER_BUTTON_PADDLE3", "paddle4": "CONTROLLER_BUTTON_PADDLE4",
}
AXES = {
    "leftx": "CONTROLLER_AXIS_LEFTX", "lefty": "CONTROLLER_AXIS_LEFTY",
    "rightx": "CONTROLLER_AXIS_RIGHTX", "righty": "CONTROLLER_AXIS_RIGHTY",
    "lefttrigger": "CONTROLLER_AXIS_TRIGGERLEFT", "righttrigger": "CONTROLLER_AXIS_TRIGGERRIGHT",
}
TRIGGER_AS_BUTTON = 0.5  # trigger axis above this also counts as "pressed"
STICK_DEADZONE = 0.12


def is_gamepad_input(token):
    return isinstance(token, str) and token.startswith("gp:")


class Gamepad:
    RESCAN_S = 2.0

    def __init__(self):
        self.ok = pygame is not None
        self.pad = None
        self._btn_ids = {}
        self._axis_ids = {}
        self._next_scan = 0.0
        if self.ok:
            try:
                pygame.init()
                sdl_controller.init()
                self._btn_ids = {n: getattr(pygame, c) for n, c in BUTTONS.items() if hasattr(pygame, c)}
                self._axis_ids = {n: getattr(pygame, c) for n, c in AXES.items() if hasattr(pygame, c)}
            except Exception:
                self.ok = False

    @property
    def connected(self):
        return self.pad is not None

    def name(self):
        if self.pad is None:
            return ""
        try:
            return self.pad.name
        except Exception:
            return "controller"

    def _scan(self):
        now = time.monotonic()
        if now < self._next_scan:
            return
        self._next_scan = now + self.RESCAN_S
        try:
            pygame.event.pump()
            n = sdl_controller.get_count()
            if self.pad is not None and not self.pad.attached():
                self.pad = None
            if self.pad is None and n > 0:
                for i in range(n):
                    if sdl_controller.is_controller(i):
                        self.pad = sdl_controller.Controller(i)
                        break
        except Exception:
            self.pad = None

    def poll(self):
        """Return (pressed: set[str], axes: dict[str, float]) with 'gp:' prefixed ids."""
        if not self.ok:
            return set(), {}
        self._scan()
        if self.pad is None:
            return set(), {}
        try:
            pygame.event.pump()
            pressed = {f"gp:{n}" for n, i in self._btn_ids.items() if self.pad.get_button(i)}
            axes = {}
            for n, i in self._axis_ids.items():
                v = self.pad.get_axis(i) / 32767.0
                if n.endswith("trigger"):
                    v = max(0.0, v)
                    if v > TRIGGER_AS_BUTTON:
                        pressed.add(f"gp:{n}")
                elif abs(v) < STICK_DEADZONE:
                    v = 0.0
                axes[f"gp:{n}"] = max(-1.0, min(1.0, v))
            return pressed, axes
        except Exception:
            self.pad = None
            return set(), {}
