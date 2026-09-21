import soccerdata as sd
u = sd.Understat(leagues='ENG-Premier League', seasons='2024')
print("SHOTS:", u.read_shot_events().columns.tolist())
print("SCHEDULE:", u.read_schedule().columns.tolist())
print("PLAYERS:", u.read_player_season_stats().columns.tolist())
