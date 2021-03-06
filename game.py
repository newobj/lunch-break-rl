import configparser
import os
import time

import tdl
from twitchobserver import Observer

import instances

from scenes import gamescene


class TickEvent(object):
    def __init__(self, tick_number):
        self.type = 'TICK'
        self.tick_number = tick_number


class HalfTickEvent(object):
    def __init__(self):
        self.type = 'HALF-TICK'


class Game(object):
    args = None
    scene_root = None
    config = None
    instance = None

    def __init__(self, args):
        Game.args = args

        # Configure game settings
        config = configparser.ConfigParser()
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.cfg')
        config.read(cfg_path)
        Game.config = config

        # Configure tdl
        tdl.set_font(Game.config['ENGINE']['font'])
        tdl.set_fps(int(Game.config['ENGINE']['fps']))
        self.console = tdl.init(54, 30, 'lunch break roguelike', renderer=Game.config['ENGINE']['renderer'])
        self._last_time = time.time()

        # Set static attributes
        Game.scene_root = gamescene.GameScene()

        # Twitch Observer
        nickname = Game.config['TWITCH']['Nickname']
        password = Game.config['TWITCH']['Password']
        self.channel = Game.config['TWITCH']['Channel']
        self.observer = Observer(nickname, password)
        self.observer.start()
        self.observer.join_channel(self.channel)

        if not Game.instance:
            Game.instance = self
            instances.register('game', self)

    def run(self):
        tick_count = 0
        timer = 0
        last_time = 0
        do_half_tick = True
        seconds_per_tick = float(Game.config['GAME']['turn'])

        running = True
        while running:
            # Draw the scene
            self.console.clear()
            Game.scene_root.draw(self.console)
            tdl.flush()

            # Handle input/events
            for event in list(tdl.event.get()) + self.observer.get_events():
                Game.scene_root.handle_events(event)

                if event.type == 'QUIT':
                    running = False
                    self.observer.stop()

            # Update scene
            time_elapsed = time.time() - last_time
            timer += time_elapsed
            last_time = time.time()
            Game.scene_root.update(time_elapsed)

            # Send out tick event
            if timer > seconds_per_tick:
                timer = 0
                tick_count += 1
                Game.scene_root.tick(tick_count)
                do_half_tick = True

            elif timer >= seconds_per_tick / 2 and do_half_tick:
                tdl.event.push(HalfTickEvent())
                do_half_tick = False
