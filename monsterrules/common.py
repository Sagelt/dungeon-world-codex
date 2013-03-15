import datetime
from collections import OrderedDict


class Option(object):
  """An option for a multiple choice question.
  
  Attributes:
    value: a object that will be passed to the question method if this option
      is selected.
    subquestions: an OrderedDict of methods/questions that will need to be
      option if this answer is selected."""
  def __init__(self, value):
    self.value = value
    self.subquestions = OrderedDict()


def Question(order, option=None):
  """Decorator for Builder methods that represent questions.
  
  Args:
    order: Unique id for this question which will be used to order it when
      presented to the user. Most commonly an int, but any comparable should
      work.
    option: The parent option (default None). Providing this marks the question
      as a subquestion: it will only be applied (and, in a future version, 
      shown) if the parent option is selected.
    """
  def decorate(func):
    func.order = order
    if option:
      option.subquestions[order] = func
    else:
      func.is_question = True
    return func
  return decorate


def Description(description):
  """Decorator for Builder questions that have a description.
  
  Args:
    description: The string description."""
  def decorate(func):
    func.description = description
    return func
  return decorate

  
def Prompt(prompt):
  """Decorator for Builder questions that sets the user-visible prompt.
  
  Args:
    prompt: The string to be displayed to the user to explain the question."""
  def decorate(func):
    func.prompt = prompt
    return func
  return decorate

def ExpectsShortText(func):
  """Decorator for Builder questions that indicates an expected value of str.
  
  This decorator indicates to the renderer that the question will be answered
  by a text input (single line)."""
  func.expectsShortText = True
  return func
  
def ExpectsLongText(func):
  """Decorator for Builder questions that indicates an expected value of str.
  
  This decorator indicates to the renderer that the question will be answered
  by a text area (multi line)."""
  func.expectsLongText = True
  return func
  
def ExpectsOne(options):
  """Decorator for questions that indicates an expected value from a list

   This decorator indicates to the renderer that the question will be answered
   by a series of radio boxes.
   
   Args:
     options: An OrderedDict of Options where the key is the text to be 
       presented to the user and the Option is the value that will be passed
       to the question if the radio button is selected."""
  def decorate(func):
    func.expectsOne = True
    func.options = options
    return func
  return decorate

def ExpectsMultiple(options):
  """Decorator for questions that indicates expected values from a list

   This decorator indicates to the renderer that the question will be answered
   by a series of check boxes.
   
   Args:
     options: An OrderedDict of Options where the key is the text to be 
       presented to the user and the Option is the value that will be passed
       to the question if the checkbox is selected."""
  def decorate(func):
    func.expectsMultiple = True
    func.options = options
    return func
  return decorate

def Required(func):
  """Decorator for Builder questions that must be answered.
  
  This decorator indicates to the renderer that the question must be answered. Radio
  buttons will have their first option selected by default. Text inputs will have the
  reuired attribute (sorry Safari)."""
  func.required = True
  return func

class MonsterBuilder(object):
  """Common case class for monster building rules.
  
  A subclass of MonsterBuilder is a set of rules for building a monster. It
  contains one or more methods decorated with the @Question annotation. When
  the monster is created each of these of these methods will be called if the
  user has answered it."""
  
  # Questions to answer
  @classmethod
  def questions(self):
    """Returns all top-level questions of this builder."""
    questions = sorted([getattr(self, method)
          for method in dir(self) 
          if (callable(getattr(self, method)) and hasattr(getattr(self, method), 'is_question'))],
          key=lambda question: question.order);
          
    return questions
    
    
class DiceBuilder(object):
  """Convenience class for building up a dice roll."""
  
  DieSizes = [4, 6, 8, 10, 12]
  
  def __init__(self):
    self.number_of_dice = 1
    self.bonuses = 0
    self.best = False
    self.worst = False
    
  def SetDieSize(self, value):
    if value not in DiceBuilder.DieSizes:
      raise TypeError("Not a valid die size")
    self.base_dice = value
  
  def IncreaseDieSize(self):
    if self.base_dice == 12:
      return
    self.base_dice += 2
    
  def DecreaseDieSize(self):
    if self.base_dice == 4:
      return
    self.base_dice -= 2
    
  def AddBonus(self, value):
    self.bonuses += value
    
  def SetBest(self):
    self.number_of_dice += 1
    self.best = True
    
  def SetWorst(self):
    self.number_of_dice += 1
    self.worst = True
    
  def Build(self):
    """Returns a string representing this roll."""
    result = ""
    if self.best:
      result += "b["
      result += str(self.number_of_dice)
      
    if self.worst:
      result += "w["
      result += str(self.number_of_dice)
    
    result += "d"+str(self.base_dice)
      
    if self.bonuses > 0:
      result += "+"
      result += str(self.bonuses)
    elif self.bonuses < 0:
      result += str(self.bonuses)
      
    if self.best or self.worst:
      result += "]"
      
    return result
      
    
  
  
  