from monsterrules.common import *
from collections import OrderedDict

class CoreMonsterBuilder(MonsterBuilder):
  """A MonsterBuilder for the core rules.
  
  Builds a monster based on the rules presented in the published version of
  Dungeon World."""
  
  def __init__(self):
    self.monster = Monster()
    self.monster.creation_rules = CoreMonsterBuilder.id
    self.damage = DiceBuilder()
    self.hp = 0
    self.armor = 0
    self.piercing = 0
    self.weapon = ""
  
  # Name to be displayed in UI
  name = "Core"
  
  # Unique ID to identify these rules
  id =  "core"
  
  # Builder
  # The build method returns the completed monster
  def Build(self):
    self.monster.damage = self.weapon +" "+ self.damage.Build()
    self.monster.hp = str(self.hp)
    self.monster.armor = str(self.armor)
    self.monster.creation_rules = CoreMonsterBuilder.id
    if self.piercing > 0:
      self.monster.damage_tags.append(str(self.piercing)+" piercing")
    return self.monster
    
  # Deltas
  # This class and the ___apply_delta method provide a simple pattern for
  # declaring modifications to be made to the monster under construction
  class CoreMonsterDelta(object):
    """A delta between the current state of a monster and a desired state."""

    def __init__(self):
      self.damage_die = 0
      self.hp_bonus = 0
      self.tags_to_add = []
      self.damage_tags_to_add = []
      self.damage_bonus = 0
      self.armor_bonus = 0
      self.best_damage = False
      self.worst_damage = False
      self.piercing = 0
      self.die_size_increases = 0

    def SetDamageDie(self, dicesize):
      self.damage_die = dicesize
      return self

    def AddHP(self, value):
      self.hp_bonus += value
      return self

    def AddTag(self, tag):
      self.tags_to_add.append(tag)
      return self

    def AddDamageTag(self, tag):
      self.damage_tags_to_add.append(tag)
      return self

    def AddDamage(self, value):
      self.damage_bonus += value
      return self

    def AddArmor(self, value):
      self.armor_bonus += value
      return self

    def SetBest(self):
      self.best_damage = True
      return self

    def SetWorst(self):
      self.worst_damage = True
      return self

    def AddPiercing(self, value):
      self.piercing += value
      return self

    def IncreaseDieSize(self):
      self.die_size_increases += 1
      return self
  
  def ___apply_delta(self, delta):
    """Apply a delta object.
    
    Args:
      delta: the delta object to be applied"""
    if delta.damage_die:
      self.damage.SetDieSize(delta.damage_die)
    self.hp += delta.hp_bonus
    self.damage.AddBonus(delta.damage_bonus)
    self.monster.tags.extend(delta.tags_to_add)
    self.monster.damage_tags.extend(delta.damage_tags_to_add)
    self.armor += delta.armor_bonus
    self.piercing += delta.piercing
    if delta.best_damage:
      self.damage.SetBest()
    if delta.worst_damage:
      self.damage.SetWorst()
    for i in xrange(0, delta.die_size_increases):
      self.damage.IncreaseDieSize()
  
  # Questions
  @Question(0)
  @Prompt("What is it called?")
  @ExpectsShortText
  def name(self, value):
    self.monster.name = value
  
  @Question(1)
  @Prompt("What is it known to do?")
  @ExpectsShortText
  def firstMove(self, value):
    self.monster.moves.append(value)
  
  @Question(2)
  @Prompt("What does it want that causes problems for others?")
  @ExpectsShortText
  def instinct(self, value):
    self.monster.instinct = value
  
  organizationOptions = OrderedDict([
    ("In large groups" , Option(CoreMonsterDelta()
      .SetDamageDie(6)
      .AddHP(3)
      .AddTag("Horde"))),
    ("In small groups" , Option(CoreMonsterDelta()
      .SetDamageDie(8)
      .AddHP(6)
      .AddTag("Group"))),
    ("All by its lonesome" , Option(CoreMonsterDelta()
      .SetDamageDie(10)
      .AddHP(12)
      .AddTag("Solitary"))),
  ])
  @Question(3)
  @Prompt("How does it usually hunt or fight?")
  @ExpectsOne(organizationOptions)
  def organization(self, value):
    self.___apply_delta(value)
  
  sizeOptions = OrderedDict([
    ("Smaller than a house cat" , Option(CoreMonsterDelta()
      .AddTag("Tiny")
      .AddDamage(-2)
      .AddDamageTag("Hand"))),
    ("Halfling-esque" , Option(CoreMonsterDelta()
      .AddTag("Small")
      .AddDamageTag("Close"))),
    ("About human size" , Option(CoreMonsterDelta()
      .AddDamageTag("Close"))),
    ("As big as a cart" , Option(CoreMonsterDelta()
      .AddTag("Large")
      .AddDamageTag(["Close", "Reach"])
      .AddHP(4))),
    ("Much larger than a cart" , Option(CoreMonsterDelta()
      .AddTag("Huge")
      .AddDamageTag("Reach")
      .AddHP(8)
      .AddDamage(3))),
  ])
  @Question(4)
  @Prompt("How big is it?")
  @ExpectsOne(sizeOptions)
  def size(self, value):
    self.___apply_delta(value)
  
  defenseOptions = OrderedDict([
    ("Cloth or flesh", Option(CoreMonsterDelta()
      .AddArmor(0))),
    ("Leathers or thick hide", Option(CoreMonsterDelta()
      .AddArmor(1))),
    ("Mail or scales", Option(CoreMonsterDelta()
      .AddArmor(2))),
    ("Plate or bone", Option(CoreMonsterDelta()
      .AddArmor(3))),
    ("Permanent magical protection", Option(CoreMonsterDelta()
      .AddTag("Magical")
      .AddArmor(4))),
  ])
  @Question(5)
  @Prompt("What is its most important defense?")
  @ExpectsOne(defenseOptions)
  def defense(self, value):
    self.___apply_delta(value)
  
  reputationOptions = OrderedDict([
    ("Unrelenting strength" , Option(CoreMonsterDelta()
      .AddDamage(2)
      .AddDamageTag("Forceful"))),
    ("Skill in offense" , Option(CoreMonsterDelta()
      .SetBest())),
    ("Skill in defense" , Option(CoreMonsterDelta()
      .AddArmor(2))),
    ("Deft Strikes" , Option(CoreMonsterDelta()
      .AddPiercing(1))),
    ("Uncanny endurance" , Option(CoreMonsterDelta()
      .AddHP(4))),
    ("Deceit and trickery" , Option(CoreMonsterDelta()
      .AddTag("Stealthy"))),
    ("A useful adaptation", Option(CoreMonsterDelta())),
    ("Divine power" , Option(CoreMonsterDelta()
      .AddDamage(2)
      .AddTag("Divine"))),
    ("Divine health" , Option(CoreMonsterDelta()
      .AddHP(2)
      .AddTag("Divine"))),
    ("Spells and magic" , Option(CoreMonsterDelta()
      .AddTag("Magical"))),
    
  ])
  @Question(6)
  @Prompt("What is it known for?")
  @ExpectsMultiple(reputationOptions)
  def reputation(self, value):
    self.___apply_delta(value)
  
  @Question(1, reputationOptions["A useful adaptation"])
  @Prompt("List the adaptiations")
  @ExpectsShortText
  def specialQualities(self, value):
    for item in value.split(', '):
      self.monster.special_qualities.append(item)
  
  @Question(1, reputationOptions["Deceit and trickery"])
  @Prompt("Write a move about dirty tricks")
  @ExpectsShortText
  def stealthmove(self, value):
    self.monster.moves.append(value)
  
  @Question(1, reputationOptions["Spells and magic"])
  @Prompt("Write a move about its spells")
  @ExpectsShortText
  def spellmove(self, value):
    self.monster.moves.append(value)
  
  @Question(7)
  @Prompt("What is its most common form of attack?")
  @ExpectsShortText
  def attack(self, value):
    self.weapon = value
  
  weaponModifierOptions = OrderedDict([
    ("Its armaments are vicious and obvious" , Option(CoreMonsterDelta()
      .AddDamage(2))),
    ("It lets the monster keep others at bay" , Option(CoreMonsterDelta()
      .AddDamageTag("Reach"))),
    ("Its armaments are small and weak" , Option(CoreMonsterDelta()
      .IncreaseDieSize())),
    ("Its armaments can slice or pierce metal" , Option(CoreMonsterDelta()
      .AddPiercing(1))),
    ("It can just tear metal apart" , Option(CoreMonsterDelta()
      .AddPiercing(2))),
    ("Armor doesn't help with the damage it deals (due to magic, size, etc.)" , Option(CoreMonsterDelta()
      .AddDamageTag("Ignores Armor"))),
    ("It can attack from a few paces" , Option(CoreMonsterDelta()
      .AddDamageTag("Near"))),
    ("It can attack from anywhere it can see you" , Option(CoreMonsterDelta()
      .AddDamageTag("Far"))),
  ])
  @Question(8)
  @Prompt("Which of these apply to its form of attack?")
  @ExpectsMultiple(weaponModifierOptions)
  def weaponModifier(self, value):
    self.___apply_delta(value)
  
  generalOptions = OrderedDict([
    ("It isn't dangerous because of the wounds it inflicts, but for other reasons", Option(CoreMonsterDelta()
      .AddTag("Devious"))),
    ("It organizes into larger groups that it can call on for support", Option(CoreMonsterDelta()
      .AddTag("Organized"))),
    ("It's as smart as a human or thereabouts", Option(CoreMonsterDelta()
      .AddTag("Intelligent"))),
    ("It actively defends itself with a shield or similar", Option(CoreMonsterDelta()
      .AddArmor(1)
      .AddTag("Cautious"))),
    ("It collects trinkets that humans would consider valuable (gold, gems, secrets)", Option(CoreMonsterDelta()
      .AddTag("Hoarder"))),
    ("It's from beyond this world", Option(CoreMonsterDelta()
      .AddTag("Planar"))),
    ("It's kept alive by something beyond simple biology", Option(CoreMonsterDelta()
      .AddHP(4))),
    ("It was made by someone", Option(CoreMonsterDelta()
      .AddTag("Construct"))),
    ("Its appearance is disturbing, terrible, or horrible", Option(CoreMonsterDelta()
      .AddTag("Terrifying"))),
    ("It doesn't have organs or discernible anatomy", Option(CoreMonsterDelta()
      .AddTag("Amorphous")
      .AddHP(3)
      .AddArmor(1))),
    ("It (or its species) is ancient, older than man, elves, and dwarves", Option(CoreMonsterDelta()
      .IncreaseDieSize())),
    ("It abhors violence", Option(CoreMonsterDelta()
      .SetWorst())),
  ])
  @Question(9)
  @Prompt("Which of these describe it?")
  @ExpectsMultiple(generalOptions)
  def general(self, value):
    self.___apply_delta(value)
  
  @Question(1, generalOptions["It isn't dangerous because of the wounds it inflicts, but for other reasons"])
  @Prompt("Write a move about why it's dangerous")
  @ExpectsShortText
  def craftymove(self, value):
    self.monster.moves.append(value)
  
  @Question(1, generalOptions["It organizes into larger groups that it can call on for support"])
  @Prompt("Write a move about calling on others for help")
  @ExpectsShortText
  def organizedmove(self, value):
    self.monster.moves.append(value)
  
  @Question(1, generalOptions["It's from beyond this world"])
  @Prompt("Write a move about using its otherworldly knowledge and power")
  @ExpectsShortText
  def planarmove(self, value):
    self.monster.moves.append(value)
  
  @Question(1, generalOptions["It was made by someone"])
  @Prompt("Give it a special quality or two about its construction or purpose")
  @ExpectsShortText
  def morespecialqualities(self, value):
    for item in value.split(', '):
      self.monster.special_qualities.append(item)
  
  @Question(1, generalOptions["Its appearance is disturbing, terrible, or horrible"])
  @Prompt("Write a special quality about why it's so horrendous")
  @ExpectsShortText
  def horriblequality(self, value):
    for item in value.split(', '):
      self.monster.special_qualities.append(item)
  
  @Question(11)
  @Prompt("Describe the monster:")
  @ExpectsLongText
  def describe(self, value):
    self.monster.description = value
  