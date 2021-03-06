import tdl

import instances
import palette
import utils

from ai import brain
from ai.actions import attackaction
from ai.actions import swappositionaction

from entities import animation
from entities import entity
from entities.items.consumables import corpse
from entities.items.weapons import debris
from entities.items.weapons import fist


class Creature(entity.Entity):
    def __init__(self, char, position=(0, 0), fg=palette.BRIGHT_WHITE, bg=palette.BLACK):
        super().__init__(char, position, fg, bg)
        self.brain = brain.Brain(self)
        self.name = 'Creature'
        self.current_health = 10
        self.max_health = 10
        self.weapon = None
        self.visible_tiles = set()
        self.state = 'NORMAL'
        self.sight_radius = 7.5

        self.equip_weapon(fist.Fist())

    @property
    def alive(self):
        return self.current_health > 0

    def move(self, x, y):
        dest = self.position[0] + x, self.position[1] + y

        action_to_perform = None
        target_entity = None

        for target_entity in instances.scene_root.get_entity_at(*dest):
            # Get bumped entity's default action
            action_to_perform = self.weapon.get_special_action(self, target_entity)

            if not action_to_perform:
                action_to_perform = target_entity.get_action(self)

            if action_to_perform:
                break

        # Perform the action if possible
        if action_to_perform and action_to_perform.prerequisite():
            action_to_perform.perform()

            # Because we have bumped, cancel our move action
            next_action = self.brain.actions[0] if self.brain.actions else None
            if next_action and \
                not action_to_perform.isinstance('SwapPositionAction') and \
                next_action.isinstance('MoveAction') and \
                next_action.parent:

                next_action.fail()

        if target_entity and target_entity.position == dest and action_to_perform:
            return

        if self.can_move(x, y):
            self.position = self.position[0] + x, self.position[1] + y

    def can_move(self, x, y):
        if not self.position:
            return False

        dest = self.position[0] + x, self.position[1] + y
        return instances.scene_root.check_collision(*dest)

    def can_see(self, target):
        """Returns true if target entity is in sight"""
        if not target or not target.position:
            return False

        return target.position in self.visible_tiles

    def update(self, time):
        super().update(time)

    def update_fov(self):
        if not self.position:
            return

        x, y = self.position
        self.visible_tiles = tdl.map.quick_fov(x, y, lambda x, y: not instances.scene_root.is_visibility_blocked(x, y), radius=self.sight_radius)

    def equip_weapon(self, new_item):
        self.weapon = new_item
        self.weapon.hidden = True
        self.append(new_item)

    def drop_weapon(self):
        if not self.weapon.isinstance('Fist'):
            i = self.weapon
            i.remove()
            i.hidden = False
            i.position = self.position
            instances.scene_root.append(i)
            self.equip_weapon(fist.Fist())
            instances.console.describe(self, '{} drops {}'.format(self.display_string, i.display_string), 'Something clatters to the ground')

    def break_weapon(self):
        if not self.weapon.isinstance('Fist'):
            i = self.weapon
            i.remove()
            self.equip_weapon(debris.Debris())
            instances.console.describe(self, '{}\'s {} breaks!'.format(self.display_string, i.display_string))

    def die(self):
        if self.current_health > 0:
            self.current_health = 0

        c = corpse.Corpse(self)
        c.position = self.position
        instances.scene_root.append(c)

        self.drop_weapon()
        instances.console.describe(self, '{} perishes!'.format(self.display_string), 'Something cries its last')
        self.remove()

    def make_blood_trail(self):
        level_entity = instances.scene_root.get_level_entity_at(*self.position)
        level_entity.fg = palette.BRIGHT_RED

    def remove(self, child=None):
        super().remove(child)

        if not child:
            self.brain.clear()

    def tick(self, tick):
        super().tick(tick)

        self.brain.tick(tick)
        self.brain.perform_action()
        self.update_fov()

        if not self.alive:
            self.die()

        if self.current_health == 1 and self.max_health > 1:
            self.make_blood_trail()

    def get_action(self, requester=None):
        # TODO: Put this specialization into player.py?
        if self.isinstance('Player') and requester.isinstance('Player'):
            return swappositionaction.SwapPositionAction(requester, self)

        direction = utils.math.sub(self.position, requester.position)
        return attackaction.AttackAction(requester, self, direction)

    @property
    def visible_entities(self):
        current_scene = instances.scene_root
        result = []

        for e in current_scene.children:
            if not e.isinstance('Entity'):
                continue

            if e == self:
                continue

            if e.position in self.visible_tiles:
                result.append(e)

        return result

    def can_attack(self, target):
        """Determines if performer can attack target
        
        target: An entity
        """
        return self.weapon.state.can_attack(target)

    def allow_attack(self, action):
        """Determines if target will allow attack"""
        return self.weapon.state.allow_attack(action)

    def before_attacked(self, action):
        """Called on target before attack occurs"""
        self.weapon.state.before_attacked(action)

    def on_attacked(self, action):
        """Called on target to handle being attacked"""
        self.weapon.state.on_attacked(action)

        damage_dealt = action.performer.weapon.damage
        verb = action.performer.weapon.verb

        instances.console.describe(action.performer, '{} {} {}'.format(action.performer.display_string, verb, action.target.display_string))

        self.current_health -= damage_dealt

        if damage_dealt > 0:
            ani = animation.FlashBackground(bg=palette.BRIGHT_RED)
            self.append(ani)

            self.make_blood_trail()

        if not self.alive:
            self.die()

    def after_attacked(self, action):
        """Called on target after attack has occurred"""
        self.weapon.state.after_attacked(action)

    def before_attack(self, action):
        """Called on performer before attack occurs"""
        self.weapon.state.before_attack(action)

    def after_attack(self, action):
        """Called on performer after attack has occurred"""
        self.weapon.state.after_attack(action)
