import tdl

import instances
import palette

from entities import entity


class Animation(entity.Entity):
    def __init__(self):
        super().__init__(' ')

    def on_done(self):
        pass


class FlashBackground(Animation):
    def __init__(self, bg=palette.BLACK, interval=0.25, repeat=2):
        super().__init__()

        self.time = 0
        self.interval = interval
        self.times_flashed = 0
        self.times_to_flash = repeat * 2
        self.bg = bg
        self.current_bg = bg

    def update(self, time):
        self.time += time
        if self.time > self.interval:
            self.time = 0
            self.times_flashed += 1

            if self.current_bg == self.bg:
                self.current_bg = self.parent.bg
            else:
                self.current_bg = self.bg

        if self.times_flashed > self.times_to_flash:
            self.parent.children.remove(self)
            self.on_done()

    def draw(self, console):
        if not self.parent.visible:
            return

        pos = self.parent.position
        char = self.parent.char
        fg = self.parent.fg

        console.draw_char(*pos, char, fg, self.current_bg)


class Flash(Animation):
    def __init__(self, char, fg=palette.BRIGHT_WHITE, bg=palette.BLACK, interval=0.25, repeat=2):
        super().__init__()

        self.time = 0
        self.interval = interval
        self.times_flashed = 0
        self.times_to_flash = repeat * 2
        self.char = char
        self.fg = fg
        self.bg = bg
        self.current_bg = bg
        self.hidden = False

    def update(self, time):
        self.time += time
        if self.time > self.interval:
            self.time = 0
            self.times_flashed += 1

            self.hidden = not self.hidden

        if self.times_flashed > self.times_to_flash:
            self.parent.children.remove(self)
            self.on_done()

    def draw(self, console):
        if not self.visible or not self.parent.visible:
            return

        console.draw_char(*self.offset, self.char, self.fg, self.bg)


class ThrowMotion(Animation):
    def __init__(self, source, dest, time):
        super().__init__()

        self.points = tdl.map.bresenham(*source, *dest)
        self.dest = dest
        self.time = time
        self.time_to_next = 0
        self.frame_time = time / len(self.points)
        self.current_point = self.points.pop(0)

    def update(self, time):
        self.parent.hidden = True
        self.time_to_next += time
        if self.time_to_next >= self.frame_time:
            self.time_to_next = 0

            if self.points:
                self.current_point = self.points.pop(0)

            else:
                self.parent.hidden = False
                self.parent.remove(self)
                self.on_done()

    def draw(self, console):
        if not instances.scene_root.check_visibility(*self.current_point):
            return

        p = self.parent
        console.draw_char(*self.current_point, p.char, p.fg, p.bg)
