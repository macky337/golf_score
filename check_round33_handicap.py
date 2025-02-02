from modules.db import SessionLocal
from modules.models import HandicapMatch

session = SessionLocal()
matches = session.query(HandicapMatch).filter_by(round_id=37).all()
for m in matches:
    print(f"Match: {m.player_1_id} -> {m.player_2_id} : {m.player_1_to_2}")
    print(f"Match: {m.player_2_id} -> {m.player_1_id} : {m.player_2_to_1}")
session.close()