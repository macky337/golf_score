# modules/models.py
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Member(Base):
    __tablename__ = "members"
    member_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    base_handicap = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # scoresとのリレーション
    scores = relationship("Score", back_populates="member")

class Round(Base):
    __tablename__ = "rounds"
    round_id = Column(Integer, primary_key=True, autoincrement=True)
    date_played = Column(Date, nullable=False)
    course_name = Column(String, nullable=False)
    num_players = Column(Integer, nullable=False)
    has_extra = Column(Boolean, default=False)
    finalized = Column(Boolean, default=False)

    # scoresとのリレーション
    scores = relationship("Score", back_populates="round")
    match_handicaps = relationship("MatchHandicap", back_populates="round")

class Score(Base):
    __tablename__ = "scores"
    score_id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey("rounds.round_id"))
    member_id = Column(Integer, ForeignKey("members.member_id"))

    front_score = Column(Integer, default=0)
    back_score = Column(Integer, default=0)
    extra_score = Column(Integer, default=0)

    front_putt = Column(Integer, default=0)
    back_putt = Column(Integer, default=0)
    extra_putt = Column(Integer, default=0)

    # ほかにもnet_front_scoreなど追加してもOK

    round = relationship("Round", back_populates="scores")
    member = relationship("Member", back_populates="scores")

class MatchHandicap(Base):
    __tablename__ = "match_handicap"
    match_handicap_id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey("rounds.round_id"))
    giver_id = Column(Integer, ForeignKey("members.member_id"))
    receiver_id = Column(Integer, ForeignKey("members.member_id"))
    half_hcp = Column(Integer, default=0)
    
    # ラウンドとのリレーション(必要なら)
    # round = relationship("Round", back_populates="match_handicaps")
