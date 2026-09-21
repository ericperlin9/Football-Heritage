import os
os.environ["TLS_LIBRARY_PATH"] = os.path.join(os.path.dirname(__file__), "tls-client-darwin-amd64-1.13.1.dylib")

import soccerdata as sd

understat = sd.Understat(leagues="ENG-Premier League", seasons="2024")
schedule = understat.read_schedule().reset_index()

# Get unique team name -> team_id pairs
teams = schedule[['home_team', 'home_team_id']].drop_duplicates().sort_values('home_team')
print(teams.to_string(index=False))