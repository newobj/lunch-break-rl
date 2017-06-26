import tdl

import draw
import palette
import player
import level
from ui import playerwindow
from ui import levelwindow

from entities import item
from twitchchatmanager import TwitchChatManager


class TickEvent(object):
    def __init__(self):
        self.type = 'TICK'


class Scene(object):
    current_scene = None

    def __init__(self):
        self.entities = []
        self.seconds_per_tick = 2
        self.timer = 0

        self.entities.append(TwitchChatManager())
        w = levelwindow.LevelWindow(0, 0, 29, 30, 'Lunch Break RL')
        w.seconds_per_tick = self.seconds_per_tick
        self.entities.append(w)

        self.level = level.Level(1, 1, 27, 28)
        self.entities.append(self.level)

        w = playerwindow.PlayerWindow(29, 0, 11, 30, 'Players')
        self.entities.append(w)

        if not Scene.current_scene:
            Scene.current_scene = self

    def draw(self, console):
        #self.level.draw(console)

        for entity in self.entities:
            entity.draw(console)

    def handle_events(self, event):
        #self.level.handle_events(event)

        for entity in self.entities:
            entity.handle_events(event)

    def check_collision(self, x, y):
        """Returns True if player cannot move into coords"""

        #if not (x - self.level.x, y - self.level.y) in self.level.data:

        char, fg, bg = self.level.get_char(x - self.level.x, y - self.level.y)

        return char != ord(' ')

    def update(self, time):
        for entity in self.entities:
            entity.update(time)

        self.timer += time
        if self.timer > self.seconds_per_tick:
            self.timer = 0
            tdl.event.push(TickEvent())