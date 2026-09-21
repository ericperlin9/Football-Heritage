import os
os.environ["TLS_LIBRARY_PATH"] = os.path.join(os.path.dirname(__file__), "tls-client-darwin-amd64-1.13.1.dylib")

import soccerdata as sd

understat = sd.Understat(leagues="ENG-Premier League", seasons="2024")

print("SHOTS:", understat.read_shot_events().columns.tolist())
print("SCHEDULE:", understat.read_schedule().columns.tolist())
print("PLAYERS:", understat.read_player_season_stats().columns.tolist())