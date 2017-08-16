from entities.items import weapon


class Fist(weapon.Weapon):
    def __init__(self, char='f', position=(0, 0)):
        super().__init__(char, position)

        self.damage = 1
        self.verb = 'punches'

    def on_use(self):
        pass