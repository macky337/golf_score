import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, Date, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Round(Base):
    __tablename__ = 'rounds'
    round_id = Column(Integer, primary_key=True, autoincrement=True)
    # dateは新規登録時に指定がなければ本日の日付を設定
    date = Column(Date, default=datetime.date.today, nullable=False)
    date_played = Column(Date, nullable=False)
    course_name = Column(String, nullable=False)
    num_players = Column(Integer, nullable=False)
    has_extra = Column(Boolean, default=False)
    finalized = Column(Boolean, default=False)
    # ラウンドとスコアのリレーションシップ
    scores = relationship("Score", back_populates="round")

class Member(Base):
    __tablename__ = 'member'
    member_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    # メンバーとスコアのリレーションシップ
    scores = relationship("Score", back_populates="member")

class Score(Base):
    __tablename__ = 'score'
    score_id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey('rounds.round_id'), nullable=False)
    member_id = Column(Integer, ForeignKey('member.member_id'), nullable=False)
    front_score = Column(Integer, default=0)
    back_score = Column(Integer, default=0)
    extra_score = Column(Integer, default=0)
    front_putt = Column(Integer, default=0)
    back_putt = Column(Integer, default=0)
    extra_putt = Column(Integer, default=0)
    front_game_pt = Column(Integer, default=0)
    back_game_pt = Column(Integer, default=0)
    extra_game_pt = Column(Integer, default=0)
    match_front = Column(Integer, default=0)
    match_back = Column(Integer, default=0)
    match_total = Column(Integer, default=0)
    match_extra = Column(Integer, default=0)
    match_pt = Column(Float, default=0)
    put_pt = Column(Float, default=0)
    total_pt = Column(Float, default=0)
    # Round と Member とのリレーションシップを定義
    round = relationship("Round", back_populates="scores")
    member = relationship("Member", back_populates="scores")

class HandicapMatch(Base):
    __tablename__ = 'handicap_match'
    id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey('rounds.round_id'), nullable=False)  # 修正済み
    player_1_id = Column(Integer, ForeignKey('member.member_id'), nullable=False)
    player_2_id = Column(Integer, ForeignKey('member.member_id'), nullable=False)
    player_1_to_2 = Column(Integer, default=0)
    player_2_to_1 = Column(Integer, default=0)
    total_only = Column(Boolean, default=False)  # total スコアのみで判定するフラグ

# 例: 新規ラウンド登録時（デバッグ用のサンプルコード）
if __name__ == "__main__":
    import datetime
    from sqlalchemy.orm import sessionmaker
    from modules.db import engine  # engineの定義がある前提

    # サンプル用のセッションを作成
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # サンプルデータ用の値を定義
    provided_date = None

    new_round = Round(
        date = provided_date or provided_date_played,  # provided_dateがNoneの場合はdate_playedを利用
        date_played = provided_date_played,
        course_name = "千葉よみうり",
        num_players = 4,
        has_extra = False,
        finalized = False
    )
    session.add(new_round)
    session.commit()
