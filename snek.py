#!/usr/bin/env python3
from collections import deque
from contextlib import contextmanager
import curses
from curses import wrapper
import enum
import random
import time

hertz = 10 # Updates per second
TICK = 1/hertz


@enum.unique
class Color(enum.Enum):
    DEFAULT = 0
    APPLE = enum.auto()
    SNEK = enum.auto()


@enum.unique
class Direction(enum.Enum):
    UP = enum.auto()
    DOWN = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()
    DEFAULT = enum.auto()


OPPOSITE = {
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT,
}


def opposite(direction: Direction) -> Direction:
    return OPPOSITE.get(direction)


DIRECTION_MAP = {
    curses.KEY_UP: Direction.UP,
    curses.KEY_DOWN: Direction.DOWN,
    curses.KEY_LEFT: Direction.LEFT,
    curses.KEY_RIGHT: Direction.RIGHT,

    ord("w"): Direction.UP,
    ord("a"): Direction.LEFT,
    ord("d"): Direction.RIGHT,
    ord("s"): Direction.DOWN,

    ord("h"): Direction.LEFT,
    ord("j"): Direction.DOWN,
    ord("k"): Direction.UP,
    ord("l"): Direction.RIGHT,

    curses.ERR: Direction.DEFAULT,
}


@contextmanager
def draw(screen):
    yield screen
    screen.refresh()


class Snek:
    def __init__(self, direction: Direction, y: int, x: int):
        self.direction = direction
        self.head = (y, x)
        self.tail = deque()
        self._shorthand = {
            Direction.UP: (1, 0),
            Direction.DOWN: (-1, 0),
            Direction.LEFT: (0, -1),
            Direction.RIGHT: (0, 1),
        }
        self._alive = True

    def _move(self, direction: Direction, apple):
        delta_y, delta_x = self._shorthand[direction]
        current_y, current_x = self.head
        self.tail.appendleft(self.head)
        self.head = (current_y + delta_y, current_x + delta_x)

        if not self.head == apple:
            self.tail.pop()

        if self.head in self.tail:
            self._alive = False

    def advance(self, direction: Direction, apple):
        if (
            direction is not opposite(self.direction)
            and direction is not direction.DEFAULT
        ):
            self.direction = direction

        self._move(self.direction, apple)

    def eat(self):
        pass

    def kill(self):
        self._alive = False

    @property
    def alive(self):
        return self._alive

    @property
    def footprint(self):
        return [self.head] + list(self.tail)


def _trans_pos(screen, pos):
    height, _ = screen.getmaxyx()
    y, x = pos
    return (height - y, x)


def clear_snek(screen, snek: Snek):
    screen.addstr(
        *_trans_pos(screen, snek.head), " ", curses.color_pair(Color.DEFAULT.value)
    )
    for pos in snek.tail:
        screen.addstr(
            *_trans_pos(screen, pos), " ", curses.color_pair(Color.DEFAULT.value)
        )


def draw_snek(screen, snek: Snek):
    screen.addstr(
        *_trans_pos(screen, snek.head), "S", curses.color_pair(Color.SNEK.value)
    )
    for pos in snek.tail:
        screen.addstr(
            *_trans_pos(screen, pos), "%", curses.color_pair(Color.SNEK.value)
        )


def draw_apple(screen, apple):
    screen.addstr(*apple, "@", curses.color_pair(Color.APPLE.value))


def gen_position(screen, invalid):
    height, width = screen.getmaxyx()
    possible = {(y, x) for y in range(1, height-2) for x in range(1, width-2)} - invalid
    return random.choice(list(possible))


def init(screen):
    screen.clear()
    curses.init_pair(Color.APPLE.value, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(Color.SNEK.value, curses.COLOR_GREEN, curses.COLOR_BLACK)
    height, width = screen.getmaxyx()
    for x in range(width - 1):
        screen.addstr(0, x, "#", curses.color_pair(Color.DEFAULT.value))
        screen.addstr(height - 1, x, "#", curses.color_pair(Color.DEFAULT.value))

    for y in range(height - 1):
        screen.addstr(y, 0, "#", curses.color_pair(Color.DEFAULT.value))
        screen.addstr(y, width - 1, "#", curses.color_pair(Color.DEFAULT.value))

    snek_head = gen_position(screen, set())
    snek = Snek(Direction.UP, *_trans_pos(screen, snek_head))
    apple = gen_position(screen, {snek_head})

    draw_apple(screen, apple)
    draw_snek(screen, snek)
    snek.direction = DIRECTION_MAP.get(screen.getch(), Direction.DEFAULT)
    screen.nodelay(True)
    return snek, apple


def snek(stdscr):
    curses.curs_set(False)

    with draw(stdscr) as screen:
        snek, apple = init(screen)

    while snek.alive:
        start = time.process_time()
        direction = DIRECTION_MAP.get(stdscr.getch(), Direction.DEFAULT)
        with draw(stdscr) as screen:
            clear_snek(screen, snek)
            snek.advance(direction, _trans_pos(screen, apple))
            height, width = screen.getmaxyx()
            y, x = _trans_pos(screen, snek.head)
            if x < 1 or x > width - 2 or y < 1 or y > height - 2:
                snek.kill()
                continue
            elif (y, x) == apple:
                snek.eat()
                occupied = [_trans_pos(screen, pos) for pos in snek.footprint]
                apple = gen_position(screen, set(occupied))

            draw_snek(screen, snek)
            draw_apple(screen, apple)

        process = time.process_time() - start
        time.sleep(max(TICK - process, 0))


if __name__ == "__main__":
    wrapper(snek)
