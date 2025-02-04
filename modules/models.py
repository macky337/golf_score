from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Round(Base):
    __tablename__ = 'round'
    round_id = Column(Integer, primary_key=True, autoincrement=True)
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
    round_id = Column(Integer, ForeignKey('round.round_id'), nullable=False)
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
    # Round と Member とのリレーションシップを定義
    round = relationship("Round", back_populates="scores")
    member = relationship("Member", back_populates="scores")

class HandicapMatch(Base):
    __tablename__ = 'handicap_match'
    id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey('round.round_id'), nullable=False)
    player_1_id = Column(Integer, ForeignKey('member.member_id'), nullable=False)
    player_2_id = Column(Integer, ForeignKey('member.member_id'), nullable=False)
    player_1_to_2 = Column(Integer, default=0)
    player_2_to_1 = Column(Integer, default=0)
    total_only = Column(Boolean, default=False)  # total スコアのみで判定するフラグ
