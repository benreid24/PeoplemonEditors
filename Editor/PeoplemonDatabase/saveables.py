from Editor.saveable.composite import Composite
from Editor.saveable.saveableInt import U8, U16
from Editor.saveable.saveableArray import array
from Editor.saveable.saveableString import SaveableString


class Stats(Composite):
    hp = U16
    attack = U16
    defense = U16
    accuracy = U16
    evade = U16
    speed = U16
    critical = U16
    special_attack = U16
    special_defense = U16


class AvailableMove(U16):
    def __str__(self):
        return 'ID: {}'.format(self.get())


class LearnMove(Composite):
    learn_level = U8
    move_id = U16

    def __str__(self):
        return 'Learn Level: {}, ID: {}'.format(self.learn_level.get(), self.move_id.get())


class Peoplemon(Composite):
    id = U16
    name = SaveableString
    description = SaveableString
    type = U8
    special_ability_id = U8
    base_stats = Stats
    valid_moves = array(AvailableMove)
    learn_moves = array(LearnMove)
    evolve_level = U8
    evolve_id = U8
    base_xp_yield = U16
    xp_group = U8
    ev_stats = Stats

    def __str__(self):
        return 'ID: {:^3} | Name: "{}" | Desc: {}'.format(self.id.get(), self.name.get(), self.description.get()[:20])
