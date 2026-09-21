import soccerdata as sd
u = sd.Understat(leagues="ENG-Premier League", seasons="2024")
print([m for m in dir(u) if m.startswith("read")])
