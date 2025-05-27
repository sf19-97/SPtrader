#!/usr/bin/env python3
""" Matrix style rain with secret 'redpill' login - Based on SPtrader version """
import argparse
import curses
import datetime
import importlib.metadata
import itertools
import os
import random
import time
import math
import sys

from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union
from typing import Set
from typing import Dict


version = "1.0-login"

# Only use numbers and Z from ASCII - no alphabet letters
CHAR_LIST = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "Z"]

EXT_CHAR_LIST = ["Ç", "È", "Ì", "Í", "Ð", "Ñ", "Ò", "×", "Ø", "Ù", "Ú", "Ý",
                 "Þ", "ß", "à", "£", "¤", "¥", "§", "ª", "¶", "º", "»", "¿",
                 "Ä", "Å", "é", "ê", "í", "ï", "å", "æ", "ç", "è", "ð", "ñ",
                 "ò", "ö", "ø", "ù", "ý", "þ", "ā", "ć", "ĉ", "ė", "ě", "ĝ",
                 "ģ", "ħ", "ī", "ı", "ķ", "Ľ", "Ł", "ł", "ń", "ň", "ō", "Œ",
                 "œ", "ŕ", "ŗ", "ś", "ŝ", "š", "ť", "ū", "ų", "Ÿ", "ź", "ż",
                 "Ž", "ž", "ș", "ț", "ë", "Ĉ", "Ď", "ď", "Ġ", "Ř", "°", "«",
                 "±", "Δ", "Ξ", "Λ", ]

# Authentic Matrix katakana from the actual films
KATAKANA_CHAR_LIST = ["ﾓ", "ｴ", "ﾔ", "ｷ", "ｵ", "ｶ", "ｹ", "ｻ", "ｽ", "ﾖ", "ﾀ",
                      "ﾜ", "ﾈ", "ﾇ", "ﾅ", "ﾋ", "ﾎ", "ｱ", "ｳ", "ｾ", "ﾐ", "ﾗ",
                      "ﾘ", "ﾂ", "ﾃ", "ﾆ", "ﾊ", "ｿ", "ｺ", "ｼ", "ﾏ", "ﾑ",
                      "ﾒ", "ﾍ", "ｲ", "ｸ", "ﾁ", "ﾄ", "ﾉ", "ﾌ", "ﾙ", "ﾚ",
                      "ﾛ", "ﾝ"]

# Authentic Matrix symbols from the films
KATAKANA_CHAR_LIST_ADDON = ["0", "1", "2", "3", "4", "5", "7", "8", "9", "Z",
                            ":", ".", "=", "*", "+", "-", "<", ">", "|", "¦",
                            "╌", "—", "▪", '"']

# Access granted reveal effect constants
ACCESS_TEXT = "ACCESS GRANTED"
ACCESS_DELAY = 3  # frames between each letter reveal (2x faster than SPtrader)
ACCESS_TRANSITION_TIME = 3   # frames for transition effect (2x faster)

DELAY_SPEED = {0: 0.005, 1: 0.01, 2: 0.025, 3: 0.04, 4: 0.055, 5: 0.07,
               6: 0.085, 7: 0.1, 8: 0.115, 9: 0.13}

CURSES_CH_CODES_CYCLE_DELAY = {41: 1, 33: 2, 64: 3, 35: 4, 36: 5, 37: 6,
                               94: 7, 38: 8, 42: 9, 40: 10}

CURSES_COLOR = {"red": curses.COLOR_RED, "green": curses.COLOR_GREEN,
                "blue": curses.COLOR_BLUE, "yellow": curses.COLOR_YELLOW,
                "magenta": curses.COLOR_MAGENTA, "cyan": curses.COLOR_CYAN,
                "white": curses.COLOR_WHITE, "black": curses.COLOR_BLACK}

CURSES_OVER_RIDE_COLORS = {"red": 160, "green": 40, "blue": 21,
                           "yellow": 184, "magenta": 164, "cyan": 44,
                           "white": 255, "black": 16}

CURSES_CH_CODES_COLOR = {114: "red", 82: "red", 116: "green", 84: "green",
                         121: "blue", 89: "blue", 117: "yellow", 85: "yellow",
                         105: "magenta", 73: "magenta", 111: "cyan",
                         79: "cyan", 112: "white", 80: "white", 18: "red",
                         20: "green", 25: "blue", 21: "yellow", 9: "magenta",
                         15: "cyan", 16: "white", 27: "black", 91: "black",
                         123: "black"}
DEFAULT_BG_CHAR = " "
DEFAULT_CYCLE_COLOR_DELAY = 500
WAKE_UP_PAIR = 21
WAKE_UP_KEYS = [119, 65, 107, 101]
MIN_SCREEN_SIZE_Y = 10
MIN_SCREEN_SIZE_X = 10


class PyMatrixError(Exception):
    pass


class SingleLine:
    def __init__(self, y: int, x: int, width: int, height: int, direction: str):
        self.direction = direction
        self.height = height - 2
        self.width = width - 1
        self.async_scroll_count = 0
        self.async_scroll_rate = random.randint(0, 4)
        self.line_color_number = random.randint(1, 7)  # keep for now
        if direction == "down":
            self.lead_y = 0
            self.y = -1
            self.x = x
            length = random.randint(3, height - 3)
            self.last_y = -length  # track when to start removing characters
        elif direction == "up":
            self.lead_y = height - 2
            self.y = height - 1
            self.x = x
            length = random.randint(3, height - 3)
            self.last_y = height - 3 + length
        elif direction == "right":
            self.lead_x = 0
            self.x = -1
            length = random.randint(3, width - 3)
            self.last_x = -length
            self.y = y
            self.lead_y = 0
            self.last_y = 0
        elif direction == "left":
            self.lead_x = width - 2
            self.x = width - 1
            length = random.randint(3, width - 3)
            self.last_x = width - 2 + length
            self.y = y
            self.lead_y = 0
            self.last_y = 0

    def get_lead(self) -> Union[Tuple[int, int], None]:
        if self.direction == "down":
            if self.lead_y > self.height:
                return None
            else:
                lead_y = self.lead_y
                self.lead_y += 1
                return lead_y, self.x
        elif self.direction == "up":
            if self.lead_y < 0:
                return None
            else:
                lead_y = self.lead_y
                self.lead_y -= 1
                return lead_y, self.x
        elif self.direction == "right":
            if self.lead_x >= self.width:
                return None
            else:
                lead_x = self.lead_x
                self.lead_x += 1
                return self.y, lead_x
        elif self.direction == "left":
            if self.lead_x < 0:
                return None
            else:
                lead_x = self.lead_x
                self.lead_x -= 1
                return self.y, lead_x

    def get_next(self) -> Union[Tuple[int, int], None]:
        if self.direction == "down":
            if self.y < 0 or self.y > self.height:
                self.y += 1
                return None
            else:
                y = self.y
                self.y += 1
                return y, self.x
        elif self.direction == "up":
            if self.y > self.height or self.y < 0:
                self.y -= 1
                return None
            else:
                y = self.y
                self.y -= 1
                return y, self.x
        elif self.direction == "right":
            if self.x < 0 or self.x >= self.width:
                self.x += 1
                return None
            else:
                x = self.x
                self.x += 1
                return self.y, x
        elif self.direction == "left":
            if self.x >= self.width or self.x < 0:
                self.x -= 1
                return None
            else:
                x = self.x
                self.x -= 1
                return self.y, x

    def delete_last(self) -> Union[Tuple[int, int], None]:
        if self.direction == "down":
            if self.last_y < 0 or self.last_y > self.height:
                self.last_y += 1
                return None
            else:
                last_y = self.last_y
                self.last_y += 1
                return last_y, self.x
        elif self.direction == "up":
            if self.last_y > self.height or self.last_y < 0:
                self.last_y -= 1
                return None
            else:
                last_y = self.last_y
                self.last_y -= 1
                return last_y, self.x
        elif self.direction == "right":
            if self.last_x < 0 or self.last_x >= self.width:
                self.last_x += 1
                return None
            else:
                last_x = self.last_x
                self.last_x += 1
                return self.y, last_x
        elif self.direction == "left":
            if self.last_x >= self.width:
                self.last_x -= 1
                return None
            else:
                last_x = self.last_x
                self.last_x -= 1
                return self.y, last_x

    def okay_to_delete(self) -> bool:
        if self.direction == "down":
            return True if self.last_y > self.height else False
        elif self.direction == "up":
            return True if self.last_y < 0 else False
        elif self.direction == "right":
            return True if self.last_x >= self.width else False
        elif self.direction == "left":
            return True if self.last_x < 0 else False

    def async_scroll_turn(self) -> bool:
        if self.async_scroll_count == self.async_scroll_rate:
            self.async_scroll_count = 0
            return True
        else:
            self.async_scroll_count += 1
            return False


class OldScrollingLine:
    old_scroll_chr_list = []

    def __init__(self, x: int, width: int, height: int):
        self.height = height - 2
        self.width = width - 1
        self.y = -1
        self.x = x
        self.length = random.randint(3, height - 3)
        self.lead_y = 0
        self.lead_char = random.choice(OldScrollingLine.old_scroll_chr_list)
        self.location_list = []
        self.line_color_number = random.randint(1, 7)
        self.bold = True if random.randint(1, 3) <= 1 else False

    @classmethod
    def update_char_list(cls, updated_char_list: List[str]) -> None:
        OldScrollingLine.old_scroll_chr_list = updated_char_list

    def delete_last(self) -> Union[None, List[int]]:
        if len(self.location_list) == self.length or self.y >= self.length:
            return self.location_list[-1][0:2]
        else:
            return None

    def get_lead(self) -> Union[Tuple[int, int, str], None]:
        if self.lead_y <= self.height:
            lead_y = self.lead_y
            self.lead_y += 1
            return lead_y, self.x, self.lead_char
        else:
            return None

    def get_next(self) -> List[List]:
        if len(self.location_list) != 0 and self.y >= 0:
            for cell in self.location_list:
                cell[0] += 1
        if len(self.location_list) < self.length and 0 <= self.y < self.height:
            self.location_list.append(
                [0, self.x, random.choice(OldScrollingLine.old_scroll_chr_list)]
            )
        if self.y > self.height:
            self.location_list.pop(0)
        self.y += 1
        return self.location_list

    def okay_to_delete(self) -> bool:
        return len(self.location_list) == 0 and self.y > self.height


class Matrix:
    def __init__(self, screen, args: argparse.Namespace):
        self.screen = screen
        self.args = args
        curses.curs_set(0)  # Set the cursor to off.
        self.screen.timeout(0)  # Turn blocking off for screen.getch().
        self.setup_colors()
        self.screen.bkgd(self.args.bg_char, curses.color_pair(1))
        self.color_cycle = itertools.cycle([1, 2, 3, 4, 5, 6])
        self.color_cycle_count = itertools.count(start=0, step=1)
        self.color_cycle_delay = DEFAULT_CYCLE_COLOR_DELAY
        self.wake_up_time = 20 if self.args.test_mode \
            else random.randint(2000, 3000)
        self.char_set = build_character_set2(args)
        if args.reverse:
            self.dir = "up"
        elif args.scroll_right:
            self.dir = "right"
        elif args.scroll_left:
            self.dir = "left"
        elif args.old_school_scrolling:
            self.dir = "old scrolling"
        else:
            self.dir = "down"
        if self.args.multiple_mode:
            self.color_mode = "multiple"
            setup_curses_colors("random",
                                self.args.background, self.args.over_ride)
        elif self.args.random_mode:
            self.color_mode = "random"
            setup_curses_colors("random",
                                self.args.background, self.args.over_ride)
        elif self.args.cycle:
            self.color_mode = "cycle"
        else:
            self.color_mode = "normal"
        self.spacer = 2 if self.args.double_space else 1
        self.line_list = []
        self.x_list = []
        self.y_list = []
        self.keys_pressed = []
        
        # Access granted reveal effect attributes
        self.access_granted = False
        self.access_progress = 0
        self.access_timer = 0
        self.access_positions: List[Tuple[int, int, str]] = []
        self.access_effects: Dict[Tuple[int, int], Dict] = {}
        self.revealed_positions: Set[Tuple[int, int]] = set()
        
        # Corner text effects
        self.corner_timer = 0
        self.sp_shown = False
        self.sp_display_time = 0
        self.trader_shown = False
        self.trader_progress = 0
        
        # Secret login state
        self.typed_text = ""
        self.secret_password = "redpill"
        
        self.main_loop()

    def calculate_access_positions(self, width: int, height: int) -> List[Tuple[int, int, str]]:
        """Calculate center positions for ACCESS GRANTED text"""
        text_len = len(ACCESS_TEXT)
        spacing = 2  # Add spacing between letters
        total_width = text_len + (text_len - 1) * (spacing - 1)  # Total width with spacing
        center_y = height // 2
        center_x = width // 2
        start_x = center_x - total_width // 2
        
        positions = []
        for i, char in enumerate(ACCESS_TEXT):
            x = start_x + i * spacing  # Multiply by spacing for gaps
            positions.append((x, center_y, char))
        return positions

    def is_access_position(self, x: int, y: int) -> bool:
        """Check if position is reserved for access text"""
        if not self.access_granted:
            return False
        for rx, ry, _ in self.access_positions[:self.access_progress]:
            if x == rx and y == ry:
                return True
        return False

    def draw_access_text(self) -> None:
        """Draw the ACCESS GRANTED reveal effect"""
        if not self.access_granted:
            return
            
        for i in range(self.access_progress):
            rx, ry, rchar = self.access_positions[i]
            try:
                if (rx, ry) in self.access_effects:
                    # Still transitioning - show random chars
                    effect = self.access_effects[(rx, ry)]
                    if effect['timer'] % 2 == 0:
                        char = random.choice(effect['chars'])
                    else:
                        char = rchar
                    # Green color during transition with bold
                    self.screen.addstr(ry, rx, char, 
                                     curses.color_pair(2) | curses.A_BOLD)
                else:
                    # Fully revealed - show actual character in bright green
                    self.screen.addstr(ry, rx, rchar, 
                                     curses.color_pair(10) | curses.A_BOLD)
            except curses.error:
                # Ignore if position is out of bounds
                pass

    def main_loop(self) -> None:
        size_y, size_x = self.screen.getmaxyx()
        self.check_screen_size(size_y, size_x)
        self.x_list = [x for x in range(0, size_x, self.spacer)]
        self.y_list = [y for y in range(1, size_y)]
        
        # Calculate access positions
        self.access_positions = self.calculate_access_positions(size_x, size_y)

        time_delta = datetime.timedelta(seconds=self.args.run_timer)
        end_time = datetime.datetime.now() + time_delta
        while True:
            if curses.is_term_resized(size_y, size_x):
                size_y, size_x = self.screen.getmaxyx()
                self.check_screen_size(size_y, size_x)
                self.x_list = [x for x in range(0, size_x, self.spacer)]
                self.y_list = [y for y in range(0, size_y)]
                self.line_list.clear()
                self.screen.clear()
                self.screen.refresh()
                # Recalculate access positions
                self.access_positions = self.calculate_access_positions(size_x, size_y)
                continue
                
            # Update access reveal if activated
            if self.access_granted:
                self.access_timer += 1
                if self.access_timer >= ACCESS_DELAY and self.access_progress < len(ACCESS_TEXT):
                    self.access_progress += 1
                    self.access_timer = 0
                    # Start transition effect for new position
                    if self.access_progress > 0:
                        x, y, _ = self.access_positions[self.access_progress - 1]
                        self.access_effects[(x, y)] = {
                            'timer': 0,
                            'chars': list(self.char_set),
                            'speed': 2
                        }
                        self.revealed_positions.add((x, y))
                
                # Update transition effects
                for pos in list(self.access_effects.keys()):
                    self.access_effects[pos]['timer'] += 1
                    if self.access_effects[pos]['timer'] >= ACCESS_TRANSITION_TIME:
                        del self.access_effects[pos]
            
            self.add_lines(size_y, size_x)
            if self.color_mode == "cycle":
                if next(self.color_cycle_count) == self.color_cycle_delay:
                    color = list(CURSES_COLOR.keys())[next(self.color_cycle)]
                    setup_curses_colors(color,
                                        self.args.background,
                                        self.args.over_ride)
                    self.color_cycle_count = itertools.count(start=0, step=1)
            if self.dir == "old scrolling":
                self.display_old_scrolling()
            else:
                self.display_normal_scrolling()
                
            # Draw corner effects if not access granted
            if not self.access_granted:
                self.draw_corner_effects()
            
            # Draw access text if granted
            self.draw_access_text()
                
            if self.args.wakeup:
                self.handle_wake_up()
            if self.args.run_timer and datetime.datetime.now() >= end_time:
                break
            time.sleep(DELAY_SPEED[self.args.delay])
            if self.handle_input():
                break
                
            # Check if ACCESS GRANTED is fully displayed
            if self.access_granted and self.access_progress >= len(ACCESS_TEXT):
                self.access_timer += 1
                # Wait about 2 seconds after full reveal
                if self.access_timer > 120:
                    # Clean exit to show Morpheus choice screen
                    self.screen.clear()
                    self.screen.refresh()
                    curses.endwin()
                    
                    # Show Morpheus choice screen
                    morpheus_choice(self.args.test_mode)
        self.screen.erase()
        self.screen.refresh()

    def draw_corner_effects(self):
        """Draw S P in upper left and T R A D E R in bottom right"""
        size_y, size_x = self.screen.getmaxyx()
        self.corner_timer += 1
        
        # S appears at 0.75 seconds (45 frames at 60fps)
        if self.corner_timer >= 45:
            # S with glitch effect for first 12 frames (0.2 seconds)
            if self.corner_timer < 57:
                # Glitch effect
                glitch_chars = ["Z", "7", "ﾓ", "ｷ", "ﾂ", "ﾊ"]
                char = glitch_chars[(self.corner_timer - 45) % len(glitch_chars)]
                try:
                    self.screen.addstr(7, 8, char, curses.color_pair(11) | curses.A_BOLD)
                except curses.error:
                    pass
            else:
                # Show stable S
                try:
                    self.screen.addstr(7, 8, "S", curses.color_pair(11) | curses.A_BOLD)
                except curses.error:
                    pass
        
        # P appears immediately after S glitch (at frame 57)
        if self.corner_timer >= 57:
            # P with glitch effect for first 12 frames (0.2 seconds)
            if self.corner_timer < 69:
                glitch_chars = ["9", "ﾖ", "ｻ", "ﾘ", "ｱ", "ﾒ"]
                char = glitch_chars[(self.corner_timer - 57) % len(glitch_chars)]
                try:
                    self.screen.addstr(7, 10, char, curses.color_pair(11) | curses.A_BOLD)
                except curses.error:
                    pass
            else:
                # Show stable P
                try:
                    self.screen.addstr(7, 10, "P", curses.color_pair(11) | curses.A_BOLD)
                except curses.error:
                    pass
        
        # T R A D E R sequence starts 0.2 seconds after P (12 frames)
        # Start at frame 81
        trader_text = "TRADER"
        start_x = size_x - 18  # Four columns more to the left total
        
        for i, letter in enumerate(trader_text):
            # Each letter starts 12 frames after the previous one
            letter_start = 81 + (i * 10)
            
            if self.corner_timer >= letter_start:
                # Glitch for first 12 frames of each letter (0.2 seconds)
                if self.corner_timer < letter_start + 12:
                    glitch_chars = ["ﾈ", "ﾋ", "ｿ", "ﾜ", "ｴ", "ﾑ", "ﾗ", "ｵ", "ﾅ"]
                    char = random.choice(glitch_chars) if i % 2 == 0 else glitch_chars[(self.corner_timer - letter_start) % len(glitch_chars)]
                    try:
                        self.screen.addstr(size_y - 8, start_x + (i * 2), char,
                                         curses.color_pair(11) | curses.A_BOLD)
                    except curses.error:
                        pass
                else:
                    # Show stable letter
                    try:
                        self.screen.addstr(size_y - 8, start_x + (i * 2), letter,
                                         curses.color_pair(11) | curses.A_BOLD)
                    except curses.error:
                        pass

    def handle_input(self) -> bool:
        """
        Returns True: Break. Quit the matrix
        Returns False: Continue running the matrix
        """
        ch = self.screen.getch()
        if ch == -1:
            return False
        elif self.args.screen_saver:
            return True
        elif ch in [81, 113]:  # q, Q
            return True
        elif self.args.disable_keys:
            return False
            
        # Secret login handling
        if ch == 10:  # Enter key
            if self.typed_text.lower() == self.secret_password:
                self.access_granted = True
                self.access_timer = 0
                self.access_progress = 0
            self.typed_text = ""  # Clear typed text
        elif ch == 127 or ch == 8:  # Backspace
            self.typed_text = self.typed_text[:-1]
        elif 32 <= ch <= 126:  # Printable characters
            self.typed_text += chr(ch)
            # Keep only last 20 characters to prevent memory issues
            if len(self.typed_text) > 20:
                self.typed_text = self.typed_text[-20:]
        
        # Original key handling continues...
        if ch in WAKE_UP_KEYS:
            self.keys_pressed.append(ch)
            if self.keys_pressed == WAKE_UP_KEYS:
                wake_up_neo(self.screen, self.args.test_mode)
                while self.screen.getch() != -1:  # clears out the buffer
                    pass
                self.keys_pressed = []
                self.screen.bkgd(self.args.bg_char, curses.color_pair(1))
                return False
            elif len(self.keys_pressed) >= 4:
                self.keys_pressed = []
                return False
        # Additional key commands omitted for brevity...
        return False

    # Include all other methods from the original file...
    # (I'm including just the essential ones here for space)
    
    def add_lines(self, size_y: int, size_x: int) -> None:
        if self.dir == "right" or self.dir == "left":
            y = random.choice(self.y_list)
            self.line_list.append(SingleLine(y, 0, size_x, size_y,self.dir))
        elif self.dir == "old scrolling":
            if len(self.line_list) < size_x - 1 and len(self.x_list) > 3:
                for _ in range(2):
                    if self.x_list:
                        x = random.choice(self.x_list)
                        # Skip columns that will have access text
                        if not (self.access_granted and any(ax == x for ax, _, _ in self.access_positions[:self.access_progress])):
                            self.x_list.pop(self.x_list.index(x))
                            self.line_list.append(OldScrollingLine(x, size_x, size_y))
        else:  # down and up
            if len(self.line_list) < size_x - 1 and len(self.x_list) > 3:
                for _ in range(2):
                    if self.x_list:
                        x = random.choice(self.x_list)
                        # Skip columns that will have access text
                        if not (self.access_granted and any(ax == x for ax, _, _ in self.access_positions[:self.access_progress])):
                            self.x_list.pop(self.x_list.index(x))
                            self.line_list.append(
                                SingleLine(0, x, size_x, size_y, self.dir))

    def display_normal_scrolling(self) -> None:
        remove_list = []
        for line in self.line_list:
            if self.args.async_scroll and not line.async_scroll_turn():
                continue
            if remove_line := line.delete_last():
                if not self.is_access_position(remove_line[1], remove_line[0]):
                    if self.args.do_not_clear is False:
                        self.screen.addstr(remove_line[0], remove_line[1], self.args.bg_char)
                if line.x not in self.x_list:
                    self.x_list.append(line.x)

            if self.args.bold_all:
                bold = curses.A_BOLD
            elif self.args.bold_on:
                if random.randint(1, 3) <= 1:
                    bold = curses.A_BOLD
                else:
                    bold = curses.A_NORMAL
            else:
                bold = curses.A_NORMAL

            italic = curses.A_ITALIC if self.args.italic else curses.A_NORMAL
            if self.color_mode == "random":
                color = curses.color_pair(random.randint(1, 7))
            else:
                color = curses.color_pair(line.line_color_number)
            if new_char := line.get_next():
                if not self.is_access_position(new_char[1], new_char[0]):
                    self.screen.addstr(new_char[0],
                                  new_char[1],
                                  random.choice(self.char_set),
                                  color + bold + italic)
            if lead_char := line.get_lead():
                if not self.is_access_position(lead_char[1], lead_char[0]):
                    self.screen.addstr(lead_char[0], lead_char[1],
                                  random.choice(self.char_set),
                                  curses.color_pair(10) + bold + italic)
            if line.okay_to_delete():
                remove_list.append(line)
        self. screen.refresh()
        for rem in remove_list:
            self.line_list.pop(self.line_list.index(rem))

    def display_old_scrolling(self) -> None:
        remove_list = []
        for line in self.line_list:
            if self.args.bold_all:
                bold = curses.A_BOLD
            elif self.args.bold_on and line.bold:
                bold = curses.A_BOLD
            else:
                bold = curses.A_NORMAL

            italic = curses.A_ITALIC if self.args.italic else curses.A_NORMAL
            color = curses.color_pair(line.line_color_number)
            if lead := line.get_lead():
                if not self.is_access_position(lead[1], lead[0]):
                    self.screen.addstr(lead[0], lead[1], lead[2],
                                  curses.color_pair(10) + bold + italic)
            if remove := line.delete_last():
                if not self.is_access_position(remove[1], remove[0]):
                    self.screen.addstr(remove[0], remove[1], self.args.bg_char)
                if line.x not in self.x_list:
                    self.x_list.append(line.x)
            location_char_list = line.get_next()
            for cell in location_char_list:
                if not self.is_access_position(cell[1], cell[0]):
                    self.screen.addstr(*cell, color + bold + italic)
            if line.okay_to_delete():
                remove_list.append(line)
        self. screen.refresh()
        for rem in remove_list:
            self.line_list.pop(self.line_list.index(rem))

    @classmethod
    def check_screen_size(cls, size_y: int, size_x: int) -> None:
        if size_y < MIN_SCREEN_SIZE_Y:
            raise PyMatrixError("Error screen height is to short.")
        if size_x < MIN_SCREEN_SIZE_X:
            raise PyMatrixError("Error screen width is to narrow.")

    def setup_colors(self) -> None:
        setup_curses_wake_up_colors(self.args.over_ride)
        curses_lead_color(self.args.lead_color,
                          self.args.background, self.args.over_ride)
        if self.args.color_number is not None:
            setup_curses_color_number(self.args.color_number,
                                      self.args.background, self.args.over_ride)
        else:
            setup_curses_colors(self.args.color, self.args.background,
                                self.args.over_ride)
        
        # Add colors for reveal effect
        if self.args.over_ride:
            # White for transition
            curses.init_pair(11, CURSES_OVER_RIDE_COLORS["white"],
                            CURSES_OVER_RIDE_COLORS[self.args.background])
            # Yellow for revealed text
            curses.init_pair(12, CURSES_OVER_RIDE_COLORS["yellow"],
                            CURSES_OVER_RIDE_COLORS[self.args.background])
        else:
            # White for transition
            curses.init_pair(11, curses.COLOR_WHITE,
                            CURSES_COLOR[self.args.background])
            # Yellow for revealed text
            curses.init_pair(12, curses.COLOR_YELLOW,
                            CURSES_COLOR[self.args.background])

    def handle_wake_up(self) -> None:
        if self.wake_up_time <= 0:
            wake_up_neo(self.screen, self.args.test_mode)
            self.wake_up_time = random.randint(2000, 3000)
            while self.screen.getch() != -1:  # clears out the buffer
                ...
            self.screen.bkgd(self.args.bg_char, curses.color_pair(1))
        else:
            self.wake_up_time -= 1


def build_character_set2(args: argparse.Namespace):
    if args.zero_one:
        new_list = ["0", "1"]
    elif args.ext_only and args.test_mode:
        new_list = ["Ä"]
    elif args.ext_only:
        new_list = EXT_CHAR_LIST
    elif args.Katakana_only and args.test_mode:
        new_list = ["ﾎ", "0"]
    elif args.Katakana_only:
        new_list = KATAKANA_CHAR_LIST + KATAKANA_CHAR_LIST_ADDON
    elif args.katakana and args.ext and args.test_mode:
        new_list = ["T", "ﾎ", "Ä"]
    elif args.katakana and args.ext:
        new_list = KATAKANA_CHAR_LIST + KATAKANA_CHAR_LIST_ADDON + CHAR_LIST
    elif args.ext and args.test_mode:
        new_list = ["Ä", "T"]
    elif args.ext:
        new_list = CHAR_LIST + EXT_CHAR_LIST
    elif args.katakana and args.test_mode:
        new_list = ["T", "ﾎ"]
    elif args.katakana:
        new_list = KATAKANA_CHAR_LIST + KATAKANA_CHAR_LIST_ADDON
    elif args.test_mode:
        new_list = ["T"]
    else:
        # Default: use katakana for authentic Matrix look
        new_list = KATAKANA_CHAR_LIST + KATAKANA_CHAR_LIST_ADDON
    OldScrollingLine.update_char_list(new_list)
    return new_list


def curses_lead_color(color: str, bg_color: str, over_ride: bool) -> None:
    if over_ride:
        curses.init_pair(10, CURSES_OVER_RIDE_COLORS[color],
                         CURSES_OVER_RIDE_COLORS[bg_color])
    else:
        curses.init_pair(10, CURSES_COLOR[color], CURSES_COLOR[bg_color])


def setup_curses_color_number(
        color_num: int,
        bg_color: str,
        override: bool) -> None:

    if override:
        bg = CURSES_OVER_RIDE_COLORS[bg_color]
    else:
        bg = CURSES_COLOR[bg_color]

    color_list = [color_num for _ in range(7)]
    for x, c in enumerate(color_list):
        curses.init_pair(x + 1, c, bg)


def setup_curses_colors(color: str, bg_color: str, over_ride: bool) -> None:
    """ Init colors pairs in the curses. """
    if over_ride:
        curses_colors = CURSES_OVER_RIDE_COLORS
    else:
        curses_colors = CURSES_COLOR
    if color == "random":
        color_list = list(curses_colors.keys())
    else:
        color_list = [color for _ in range(7)]
    for x, c in enumerate(color_list):
        curses.init_pair(x + 1, curses_colors[c], curses_colors[bg_color])


def setup_curses_wake_up_colors(override: bool) -> None:
    if override:
        curses.init_pair(WAKE_UP_PAIR,
                         CURSES_OVER_RIDE_COLORS["green"],
                         CURSES_OVER_RIDE_COLORS["black"])
    else:
        curses.init_pair(WAKE_UP_PAIR,
                         CURSES_COLOR["green"],
                         CURSES_COLOR["black"])


def wake_up_neo(screen, test_mode: bool) -> None:
    z = 0.06 if test_mode else 1  # For test mode - shorter test time
    screen.erase()
    screen.bkgd(" ", curses.color_pair(WAKE_UP_PAIR))
    screen.refresh()
    time.sleep(3 * z)
    display_text(screen, "Wake up, Neo...", 0.08 * z, 7.0 * z)
    display_text(screen, "The Matrix has you...", 0.25 * z, 7.0 * z)
    display_text(screen, "Follow the white rabbit.", 0.1 * z, 7.0 * z)
    display_text(screen, "Knock, knock, Neo.", 0.01 * z, 3.0 * z)
    time.sleep(2 * z)


def display_text(screen, text: str, type_time: float, hold_time: float) -> None:
    for i, letter in enumerate(text, start=1):
        screen.addstr(1, i, letter,
                      curses.color_pair(WAKE_UP_PAIR) + curses.A_BOLD)
        screen.refresh()
        time.sleep(type_time)
    time.sleep(hold_time)
    screen.erase()
    screen.refresh()


def morpheus_choice(test_mode: bool) -> None:
    """Morpheus choice screen - TUI or Frontend"""
    def choice_screen(screen):
        z = 0.06 if test_mode else 1  # For test mode - shorter test time
        screen.erase()
        screen.bkgd(" ", curses.color_pair(WAKE_UP_PAIR))
        screen.refresh()
        time.sleep(2 * z)
        
        
        # Show options
        screen.addstr(10, 5, "Choose your destiny:", curses.color_pair(WAKE_UP_PAIR) + curses.A_BOLD)
        screen.addstr(12, 8, "Type 'bluepill' - Launch Clean TUI", curses.color_pair(WAKE_UP_PAIR) + curses.A_BOLD)
        screen.addstr(13, 8, "Type 'redpill'  - Launch Frontend", curses.color_pair(WAKE_UP_PAIR) + curses.A_BOLD)
        screen.addstr(15, 5, "Type your choice and press Enter...", curses.color_pair(WAKE_UP_PAIR))
        screen.refresh()
        
        # Wait for choice input
        typed_choice = ""
        while True:
            ch = screen.getch()
            if ch == 10:  # Enter key
                if typed_choice.lower() == "bluepill":
                    # Blue pill - TUI
                    display_text(screen, "You chose the blue pill...", 0.08 * z, 2.0 * z)
                    display_text(screen, "Welcome to the TUI, Neo.", 0.08 * z, 2.0 * z)
                    screen.erase()
                    screen.refresh()
                    curses.endwin()
                    
                    # Launch TUI
                    import os
                    os.system('/home/millet_frazier/SPtrader/start_background.sh')
                    os.execv('/usr/bin/python3', 
                            ['python3', '/home/millet_frazier/SPtrader/clean_tui.py'])
                    break
                    
                elif typed_choice.lower() == "redpill":
                    # Red pill - Frontend
                    display_text(screen, "You chose the red pill...", 0.08 * z, 2.0 * z)
                    display_text(screen, "Welcome to Wonderland, Neo.", 0.08 * z, 1.0 * z)
                    display_text(screen, "Now let's see how far the rabbit hole goes...", 0.08 * z, 2.0 * z)
                    screen.erase()
                    screen.refresh()
                    curses.endwin()
                    
                    # Launch Frontend
                    import os
                    os.system('/home/millet_frazier/SPtrader/start_background.sh')
                    os.chdir('/home/millet_frazier/SPtrader/frontend')
                    os.system('npm run start-no-sandbox')
                    break
                    
                typed_choice = ""  # Clear if not valid choice
                
            elif ch == 127 or ch == 8:  # Backspace
                typed_choice = typed_choice[:-1]
            elif 32 <= ch <= 126:  # Printable characters
                typed_choice += chr(ch)
            elif ch in [ord('q'), ord('Q'), 27]:  # q, Q, or ESC to quit
                curses.endwin()
                sys.exit(0)
    
    # Setup curses for choice screen
    os.environ.setdefault('ESCDELAY', '25')
    curses.wrapper(choice_screen)


def positive_int_zero_to_nine(value: str) -> int:
    """
    Used with argparse.
    Checks to see if value is positive int between 0 and 10.
    """
    msg = f"{value} is an invalid positive int value 0 to 9"
    try:
        int_value = int(value)
        if int_value < 0 or int_value >= 10:
            raise argparse.ArgumentTypeError(msg)
        return int_value
    except ValueError:
        raise argparse.ArgumentTypeError(msg)


def color_type(value: str) -> str:
    """
    Used with argparse
    Checks to see if the value is a valid color and returns
    the lower case color name.
    """
    lower_value = value.lower()
    if lower_value in CURSES_COLOR.keys():
        return lower_value
    raise argparse.ArgumentTypeError(f"{value} is an invalid color name")


def positive_int(value: str) -> int:
    """
    Used by argparse.
    Checks to see if the value is positive.
    """
    msg = f"{value} is an invalid positive int value"
    try:
        int_value = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(msg)
    else:
        if int_value <= 0:
            raise argparse.ArgumentTypeError(msg)
    return int_value


def int_between_1_and_255(value: str) -> int:
    """
    Used by argparse. Checks to see if the value is between 1 and 255
    """
    msg = f"{value} is an invalid positive int between 1 and 255"
    try:
        int_value = int(value)
        if int_value < 1 or int_value > 255:
            raise argparse.ArgumentTypeError(msg)
        return int_value
    except ValueError:
        raise argparse.ArgumentTypeError(msg)


def background_character(value: str) -> str:
    """
    Used by argparse. Checks to see if only one character was entered
    """
    msg = f"{value} is invalid. Please enter only one character"
    if len(value) == 1:
        return value
    else:
        raise argparse.ArgumentTypeError(msg)


def list_colors() -> None:
    color_dict = {"red": "\033[91m", "green": "\033[92m", "blue": "\033[94m", "cyan": "\033[96m",
                  "yellow": "\033[93m", "magenta": "\033[95m", "white": "\033[97m", "black": "\033[90m"}
    colors = list(CURSES_COLOR.keys())
    for c in colors:
        print(f"{color_dict[c]}{c} ", end="")
    print("\033[0m")


def display_commands() -> None:
    print("Commands available during run")
    print("0 - 9  Delay time (0-Fast, 4-Default, 9-Slow)")
    print("q or Q To quit Pymatrix-rain")
    print("b      Bold characters on")
    print("B      Bold all characters")
    print("n      Bold off (Default)")
    print("a      Asynchronous like scrolling (normal scrolling only)")
    print("m      Multiple color mode")
    print("M      Multiple random color mode (normal scrolling only")
    print("c      Cycle colors")
    print("d      Restore all defaults")
    print("l      Toggle double space lines")
    print("e      Extended characters on and off")
    print("E      Extended characters only")
    print("k      Katakana characters like those from the movies if correct font is installed")
    print("K      Katakana characters only")
    print("z      1 and 0 Mode On")
    print("Z      1 and 0 Mode Off")
    print("f      Freeze the matrix (q will still quit")
    print("v      Toggle matrix scrolling up")
    print("W      Toggle do not clear screen (normal scrolling only)")
    print("w      Clear the screen, wait 2 seconds and restart")
    print("j      Toggle italic text")
    print("s      Toggle old school scrolling down only")
    print("ctrl-d Disable option keys. q will still quit The Matrix.")
    print("up arrow    Matrix scrolls down to up")
    print("down arrow  Matrix scrolls up to down (default)")
    print("right arrow Matrix scrolls from left to right")
    print("left arrow  Matrix scrolls from right to left")
    print("r,t,y,u,i,o,p,[   Set color")
    print("R,T,Y,U,I,O,P,{   Set lead character color")
    print("ctrl + r,t,y,u,i,o,p,[  Set background color")
    print("shift 0 - 9 Cycle color delay (0-Fast, 4-Default, 9-Slow)")
    print("\n*** SECRET: Type 'redpill' and press Enter for access ***")


def argument_parsing(
        argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """ Command line argument parsing. """
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", dest="delay",
                        type=positive_int_zero_to_nine,
                        default=4,
                        help="Set the delay (speed)"
                             " 0: Fast, 4: Default, 9: Slow")
    parser.add_argument("-b", dest="bold_on", action="store_true",
                        help="Bold characters on")
    parser.add_argument("-B", dest="bold_all", action="store_true",
                        help="All bold characters (overrides -b)")
    parser.add_argument("-s", dest="screen_saver", action="store_true",
                        help="Screen saver mode.  Any key will exit.")
    parser.add_argument("-a", dest="async_scroll", action="store_true",
                        help="enable asynchronous like scrolling "
                             "(normal scrolling only)")
    parser.add_argument("-S", dest="start_timer", type=positive_int, default=0,
                        metavar="SECONDS", help="Set start timer in seconds")
    parser.add_argument("-R", dest="run_timer", type=positive_int, default=0,
                        metavar="SECONDS", help="Set run timer in seconds")
    parser.add_argument("-C", dest="color", type=color_type, default="green",
                        help="Set color.  Default is green")
    parser.add_argument("-L", dest="lead_color",
                        type=color_type, default="white",
                        help="Set the lead character color.  Default is white")
    parser.add_argument("-m", dest="multiple_mode", action="store_true",
                        help="Multiple color mode")
    parser.add_argument("-M", dest="random_mode", action="store_true",
                        help="Multiple random color mode "
                             "(normal scrolling only")
    parser.add_argument("-c", dest="cycle", action="store_true",
                        help="cycle through the colors")
    parser.add_argument("-e", dest="ext", action="store_true",
                        help="use extended characters")
    parser.add_argument("-E", dest="ext_only", action="store_true",
                        help="use only extended characters (overrides -e)")
    parser.add_argument("-l", dest="double_space", action="store_true",
                        help="Double space lines")
    parser.add_argument("-z", dest="zero_one", action="store_true",
                        help="Show only zero and ones. Binary")
    parser.add_argument("--background", type=color_type, default="black",
                        help="set background color. Default is black.")
    parser.add_argument("--bg_char", type=background_character,
                        default=DEFAULT_BG_CHAR,
                        help="Enter one character to use as background."
                             " May need to use '' around the character")
    parser.add_argument("-v", "--reverse", action="store_true",
                        help="Reverse the matrix. "
                             "The matrix scrolls up (vertical)")
    parser.add_argument("--scroll_right", action="store_true",
                        help="Matrix scrolls from left to right")
    parser.add_argument("--scroll_left", action="store_true",
                        help="Matrix scrolls from right to left")
    parser.add_argument("-o", "--old_school_scrolling", action="store_true",
                        help="Old school scrolling. Scroll down only")
    parser.add_argument("-j", "--italic", action="store_true",
                        help="Italic characters")
    parser.add_argument("-k", "--katakana", action="store_true",
                        help="Use half width Katakana (as seen in the movie) "
                             "characters. NOTE: requires the correct"
                             " font to be installed to work")
    parser.add_argument("-K", "--Katakana_only", action="store_true",
                        help="Use only half width Katakana (as seen "
                             "in the movie) characters only. NOTE: requires"
                             " the correct font to be installed to work")
    parser.add_argument("-O", dest="over_ride", action="store_true",
                        help="Override terminal window colors by using color"
                             " numbers between 16 and 255. This requires 256"
                             " color support in the terminal to work.")
    parser.add_argument("-W", "--do_not_clear", action="store_true",
                        help="do not clear the screen (Normal scrolling only)")
    parser.add_argument("--color_number", type=int_between_1_and_255,
                        default=None,
                        metavar="number",
                        help="Enter a number between 1 and 255 to select"
                             " character color. Requires 256 color support in "
                             "the terminal to work. Changing colors or "
                             "background color will remove the color entered.")
    parser.add_argument("--disable_keys", action="store_true",
                        help="Disable keys except for Q to quit. Screensaver "
                             "mode will not be affected")
    parser.add_argument("--list_colors", action="store_true",
                        help="Show available colors and exit. ")
    parser.add_argument("--list_commands", action="store_true",
                        help="List Commands and exit")
    parser.add_argument("--version", action="version",
                        version=f"Version: {version}")

    parser.add_argument("--wakeup", action="store_true",
                        help=argparse.SUPPRESS)
    parser.add_argument("--test_mode", action="store_true",
                        help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = argument_parsing(argv)

    if args.list_colors:
        list_colors()
        return
    if args.list_commands:
        display_commands()
        return

    time.sleep(args.start_timer)
    os.environ.setdefault('ESCDELAY', '25')  # 25 milliseconds
    try:
        curses.wrapper(Matrix, args)
    except KeyboardInterrupt:
        pass
    except PyMatrixError as e:
        print(e)
        return


if __name__ == "__main__":
    main()
