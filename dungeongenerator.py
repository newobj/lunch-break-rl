import random

import tdl

import helpers
import level
import palette
import registry
import utils

from data import room_templates
from entities import creatures
from entities import door
from entities import items
from entities import stairs

creatures.register()
items.register()


def generate_level(width, height, player_count):
    new_entities = []
    new_level = level.Level(0, 0, width, height)

    new_level.data.draw_str(0, 0, 'X' * width * height)

    TOP = 0b0001
    RIGHT = 0b0010
    BOTTOM = 0b0100
    LEFT = 0b1000
    MASK = 0b1111
    STAIRDOWN = 0b010000
    STAIRUP = 0b100000

    floor = [0x0,0x0,0x0,
             0x0,0x0,0x0,
             0x0,0x0,0x0]

    cursor = random.randint(0, 2)
    floor[cursor] |= STAIRUP

    def up():
        nonlocal floor
        nonlocal cursor
        if cursor >= 3:
            floor[cursor] |= TOP
            cursor -= 3
            floor[cursor] |= BOTTOM

            return cursor

        return None

    def down():
        nonlocal floor
        nonlocal cursor
        if cursor <= 5:
            floor[cursor] |= BOTTOM
            cursor += 3
            floor[cursor] |= TOP
            return cursor

        return None

    def right():
        nonlocal floor
        nonlocal cursor
        if cursor not in [2, 5, 8]:
            floor[cursor] |= RIGHT
            cursor += 1
            floor[cursor] |= LEFT
            return cursor
        return None

    def left():
        nonlocal floor
        nonlocal cursor
        if cursor not in [0, 3, 6]:
            floor[cursor] |= LEFT
            cursor -= 1
            floor[cursor] |= RIGHT
            return cursor
        return None

    possible_moves = [up, down, left, right]

    moves = random.randint(8, 20)
    while moves > 0:
        current_cursor = random.choice(possible_moves)()
        if current_cursor:
            moves -= 1

    floor[cursor] |= STAIRDOWN

    # Build out floor
    for i, m in enumerate(floor):
        x = i % 3 * 9 + 1
        y = i // 3 * 7

        current_room = tdl.Console(9, 7)
        templates = room_templates[m & MASK]
        room = templates[random.randint(0, len(templates) - 1)]
        current_room.draw_str(0, 0, room)

        new_level.data.blit(current_room, x, y)

        if m & STAIRUP:
            rect = utils.rect(x, y, 9, 7)
            potential_coords = []
            for point in rect:
                ch, fg, bg = new_level.data.get_char(*point)
                if ch == ord('.'):
                    potential_coords.append(point)

            coord = potential_coords[random.randint(0, len(potential_coords) - 1)]

            ent = stairs.Stairs(position=coord)
            new_entities.append(ent)

        if m & STAIRDOWN:
            rect = utils.rect(x, y, 9, 7)
            potential_coords = []
            for point in rect:
                ch, fg, bg = new_level.data.get_char(*point)
                if ch == ord('.'):
                    potential_coords.append(point)

            coord = potential_coords[random.randint(0, len(potential_coords) - 1)]

            ent = stairs.StairsDown(position=coord)
            new_entities.append(ent)

    color_table = {
        '#': palette.WHITE,
        'X': palette.get_nearest((171, 82, 54)),
        '.': palette.BRIGHT_BLACK
    }

    #temp_level = new_level.data.__copy__()

    # Colorize tiles
    for x, y in new_level.data:
        char, fg, bg = new_level.data.get_char(x, y)

        if chr(char) == '+':
            char = ord('.')

            coords = helpers.DirectionHelper.directions
            coords = [utils.math.add(c, (x, y)) for c in coords]
            chars = [new_level.data.get_char(*c)[0] for c in coords if c in new_level.data]

            if ord('+') not in chars:
                d = door.Door(position=(x, y))
                new_entities.append(d)

        fg = color_table.get(chr(char))
        if not fg:
            fg = palette.WHITE

        new_level.data.draw_char(x, y, char, fg, bg)

    # Placing Entities
    for (x, y) in new_level.data:
        ch, fg, bg = new_level.data.get_char(x, y)
        if ch == ord('.'):
            if random.random() < 1 / 25 * max(1.0, player_count / 3):
                MonsterClass = registry.Registry.get('monster')
                mon = MonsterClass(position=(x, y))
                new_entities.append(mon)

            elif random.random() < 1 / 80:
                WeaponClass = registry.Registry.get('weapon')
                weapon = WeaponClass(position=(x, y))
                new_entities.append(weapon)

            elif random.random() < 1 / 80:
                ItemClass = registry.Registry.get('item')
                item = ItemClass(position=(x, y))
                new_entities.append(item)

    return new_level, new_entities
