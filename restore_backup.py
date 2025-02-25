import json
import datetime
from sqlalchemy.orm import sessionmaker
from modules.db import engine
from modules.models import Member, Round, Score, HandicapMatch
from sqlalchemy import select, text

# バックアップ JSON ファイルのパス
BACKUP_FILE = r"C:\Users\user\Documents\GitHub\golf_score\backups\golf_score_backup_20250219_231345.json"

SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

def restore_backup():
    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        backup_data = json.load(f)

    try:
        # 自動フラッシュを無効化
        with session.no_autoflush:
            # Members の復元
            for m in backup_data.get("members", []):
                # 既存メンバーの確認（member_id と name のみを使用）
                stmt = select(Member.member_id, Member.name).where(Member.member_id == m.get("member_id"))
                result = session.execute(stmt).first()
                
                if result:
                    # 既存メンバーの更新 - text() でラップした SQL を使用
                    session.execute(
                        text("UPDATE member SET name = :name WHERE member_id = :member_id"),
                        {"name": m.get("name"), "member_id": m.get("member_id")}
                    )
                else:
                    # 新規メンバーの追加 - text() でラップした SQL を使用
                    session.execute(
                        text("INSERT INTO member (member_id, name) VALUES (:member_id, :name)"),
                        {"member_id": m.get("member_id"), "name": m.get("name")}
                    )
                print(f"Restored Member: {m.get('name')}")
            
            session.flush()

            # Rounds の復元
            for r in backup_data.get("rounds", []):
                date_played = datetime.date.fromisoformat(r["date_played"]) if r.get("date_played") else None
                
                # 既存ラウンドの確認（必要なカラムのみを選択）
                stmt = text("""
                    SELECT round_id, date, date_played, course_name, num_players, has_extra, finalized 
                    FROM rounds 
                    WHERE round_id = :round_id
                """)
                result = session.execute(stmt, {"round_id": r.get("round_id")}).first()
                
                if result:
                    # 既存ラウンドの更新
                    session.execute(
                        text("""
                            UPDATE rounds 
                            SET date = :date, 
                                date_played = :date_played,
                                course_name = :course_name,
                                num_players = :num_players,
                                has_extra = :has_extra,
                                finalized = :finalized
                            WHERE round_id = :round_id
                        """),
                        {
                            "round_id": r.get("round_id"),
                            "date": date_played,
                            "date_played": date_played,
                            "course_name": r.get("course_name"),
                            "num_players": r.get("num_players", 4),
                            "has_extra": r.get("has_extra", False),
                            "finalized": r.get("finalized", False)
                        }
                    )
                else:
                    # 新規ラウンドの追加
                    session.execute(
                        text("""
                            INSERT INTO rounds 
                            (round_id, date, date_played, course_name, num_players, has_extra, finalized)
                            VALUES 
                            (:round_id, :date, :date_played, :course_name, :num_players, :has_extra, :finalized)
                        """),
                        {
                            "round_id": r.get("round_id"),
                            "date": date_played,
                            "date_played": date_played,
                            "course_name": r.get("course_name"),
                            "num_players": r.get("num_players", 4),
                            "has_extra": r.get("has_extra", False),
                            "finalized": r.get("finalized", False)
                        }
                    )
                print(f"Restored Round: {r.get('course_name')} on {date_played}")
            
            session.flush()

            # Scores の復元
            for s in backup_data.get("scores", []):
                # 既存スコアの確認（必要なカラムのみを選択）
                stmt = text("""
                    SELECT score_id, round_id, member_id, front_score, back_score, extra_score,
                           front_putt, back_putt, extra_putt, front_game_pt, back_game_pt,
                           extra_game_pt, match_front, match_back, match_total, match_extra,
                           match_pt, put_pt, total_pt
                    FROM score 
                    WHERE score_id = :score_id
                """)
                result = session.execute(stmt, {"score_id": s.get("score_id")}).first()
                
                if result:
                    # 既存スコアの更新
                    session.execute(
                        text("""
                            UPDATE score 
                            SET round_id = :round_id,
                                member_id = :member_id,
                                front_score = :front_score,
                                back_score = :back_score,
                                extra_score = :extra_score,
                                front_putt = :front_putt,
                                back_putt = :back_putt,
                                extra_putt = :extra_putt,
                                front_game_pt = :front_game_pt,
                                back_game_pt = :back_game_pt,
                                extra_game_pt = :extra_game_pt,
                                match_front = :match_front,
                                match_back = :match_back,
                                match_total = :match_total,
                                match_extra = :match_extra,
                                match_pt = :match_pt,
                                put_pt = :put_pt,
                                total_pt = :total_pt
                            WHERE score_id = :score_id
                        """),
                        {
                            "score_id": s.get("score_id"),
                            "round_id": s.get("round_id"),
                            "member_id": s.get("member_id"),
                            "front_score": s.get("front_score", 0),
                            "back_score": s.get("back_score", 0),
                            "extra_score": s.get("extra_score", 0),
                            "front_putt": s.get("front_putt", 0),
                            "back_putt": s.get("back_putt", 0),
                            "extra_putt": s.get("extra_putt", 0),
                            "front_game_pt": s.get("front_game_pt", 0),
                            "back_game_pt": s.get("back_game_pt", 0),
                            "extra_game_pt": s.get("extra_game_pt", 0),
                            "match_front": s.get("match_front", 0),
                            "match_back": s.get("match_back", 0),
                            "match_total": s.get("match_total", 0),
                            "match_extra": s.get("match_extra", 0),
                            "match_pt": s.get("match_pt", 0),
                            "put_pt": s.get("put_pt", 0),
                            "total_pt": s.get("total_pt", 0)
                        }
                    )
                else:
                    # 新規スコアの追加
                    session.execute(
                        text("""
                            INSERT INTO score (
                                score_id, round_id, member_id, front_score, back_score,
                                extra_score, front_putt, back_putt, extra_putt,
                                front_game_pt, back_game_pt, extra_game_pt,
                                match_front, match_back, match_total, match_extra,
                                match_pt, put_pt, total_pt
                            ) VALUES (
                                :score_id, :round_id, :member_id, :front_score, :back_score,
                                :extra_score, :front_putt, :back_putt, :extra_putt,
                                :front_game_pt, :back_game_pt, :extra_game_pt,
                                :match_front, :match_back, :match_total, :match_extra,
                                :match_pt, :put_pt, :total_pt
                            )
                        """),
                        {
                            "score_id": s.get("score_id"),
                            "round_id": s.get("round_id"),
                            "member_id": s.get("member_id"),
                            "front_score": s.get("front_score", 0),
                            "back_score": s.get("back_score", 0),
                            "extra_score": s.get("extra_score", 0),
                            "front_putt": s.get("front_putt", 0),
                            "back_putt": s.get("back_putt", 0),
                            "extra_putt": s.get("extra_putt", 0),
                            "front_game_pt": s.get("front_game_pt", 0),
                            "back_game_pt": s.get("back_game_pt", 0),
                            "extra_game_pt": s.get("extra_game_pt", 0),
                            "match_front": s.get("match_front", 0),
                            "match_back": s.get("match_back", 0),
                            "match_total": s.get("match_total", 0),
                            "match_extra": s.get("match_extra", 0),
                            "match_pt": s.get("match_pt", 0),
                            "put_pt": s.get("put_pt", 0),
                            "total_pt": s.get("total_pt", 0)
                        }
                    )
                print(f"Restored Score: {s.get('score_id')}")
            
            session.flush()

            # HandicapMatches の復元
            for hm in backup_data.get("handicap_matches", []):
                # 既存ハンディキャップマッチの確認（必要なカラムのみを選択）
                stmt = text("""
                    SELECT id, round_id, player_1_id, player_2_id, 
                           player_1_to_2, player_2_to_1, total_only
                    FROM handicap_match 
                    WHERE id = :id
                """)
                result = session.execute(stmt, {"id": hm.get("id")}).first()
                
                if result:
                    # 既存ハンディキャップマッチの更新
                    session.execute(
                        text("""
                            UPDATE handicap_match 
                            SET round_id = :round_id,
                                player_1_id = :player_1_id,
                                player_2_id = :player_2_id,
                                player_1_to_2 = :player_1_to_2,
                                player_2_to_1 = :player_2_to_1,
                                total_only = :total_only
                            WHERE id = :id
                        """),
                        {
                            "id": hm.get("id"),
                            "round_id": hm.get("round_id"),
                            "player_1_id": hm.get("player_1_id"),
                            "player_2_id": hm.get("player_2_id"),
                            "player_1_to_2": hm.get("player_1_to_2", 0),
                            "player_2_to_1": hm.get("player_2_to_1", 0),
                            "total_only": hm.get("total_only", False)
                        }
                    )
                else:
                    # 新規ハンディキャップマッチの追加
                    session.execute(
                        text("""
                            INSERT INTO handicap_match (
                                id, round_id, player_1_id, player_2_id,
                                player_1_to_2, player_2_to_1, total_only
                            ) VALUES (
                                :id, :round_id, :player_1_id, :player_2_id,
                                :player_1_to_2, :player_2_to_1, :total_only
                            )
                        """),
                        {
                            "id": hm.get("id"),
                            "round_id": hm.get("round_id"),
                            "player_1_id": hm.get("player_1_id"),
                            "player_2_id": hm.get("player_2_id"),
                            "player_1_to_2": hm.get("player_1_to_2", 0),
                            "player_2_to_1": hm.get("player_2_to_1", 0),
                            "total_only": hm.get("total_only", False)
                        }
                    )
                print(f"Restored HandicapMatch: {hm.get('id')}")

            session.flush()

            session.commit()
            print("Backup restoration complete.")
    except Exception as e:
        session.rollback()
        print(f"Error during restoration: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    restore_backup()