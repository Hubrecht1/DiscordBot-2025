import json




class rooster:
  def openRooster():
    with open("rooster.py", "r") as f:
      data = json.load(f)

  def writeRooster():
    with open("rooster.py", "w") as f:
      data = json.dump(data, f)

class day:
  events = []
  def __new__(dayName):
    instance = day.__new__(dayName)
    return instance

  def addEvent(event):
    self.events.append(event)

  def getEventList():
    return events

class event:
  def __new__(eventName, eventInfo, eventLocation, color, start, end):
    instance = event.__new__(eventName ,eventInfo ,eventLocation , color, start ,end )
    return instance
