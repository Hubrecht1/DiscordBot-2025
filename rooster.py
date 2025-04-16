from ics import Calendar
from datetime import datetime, timedelta

class rooster:
  def openRooster(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
      rooster = Calendar(file.read())
      return rooster

  # 0 = today, 1 = tomorrow...
  def printEvents(rooster,day):
    date = datetime.today().date() + timedelta(days=day)
    events = [event for event in rooster.events if event.begin.date() == date]
    if events:
      print(f"Events for {date.strftime('%B %A')}:")
      for event in events:
        print(f"{event.name} from {event.begin.strftime('%H:%M')} to {event.end.strftime('%H:%M')}")
        print(f"at {event.location}")
    else:
      print("No events scheduled.")
