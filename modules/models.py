# modules/models.py
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from modules.db import Base

class HandicapMatch(Base):
    __tablename__ = 'handicap_match'

    match_id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey('rounds.round_id'), nullable=False)
    player_1_id = Column(Integer, ForeignKey('members.member_id'), nullable=False)
    player_2_id = Column(Integer, ForeignKey('members.member_id'), nullable=False)
    player_1_to_2 = Column(Integer, default=0)  # Player 1 gives Handicap to Player 2
    player_2_to_1 = Column(Integer, default=0)  # Player 2 gives Handicap to Player 1

    # Relationships
    round = relationship("Round", back_populates="handicap_matches")
    player_1 = relationship("Member", foreign_keys=[player_1_id], back_populates="match_handicaps_given")
    player_2 = relationship("Member", foreign_keys=[player_2_id], back_populates="match_handicaps_received")

class Member(Base):
    __tablename__ = "members"
    member_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    base_handicap = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    scores = relationship("Score", back_populates="member")
    match_handicaps_given = relationship(
        "HandicapMatch", 
        back_populates="player_1", 
        foreign_keys='HandicapMatch.player_1_id'
    )
    match_handicaps_received = relationship(
        "HandicapMatch", 
        back_populates="player_2", 
        foreign_keys='HandicapMatch.player_2_id'
    )

class Round(Base):
    __tablename__ = "rounds"
    round_id = Column(Integer, primary_key=True, autoincrement=True)
    date_played = Column(Date, nullable=False)
    course_name = Column(String, nullable=False)
    num_players = Column(Integer, nullable=False)
    has_extra = Column(Boolean, default=False)
    finalized = Column(Boolean, default=False)

    scores = relationship("Score", back_populates="round")
    handicap_matches = relationship("HandicapMatch", back_populates="round")

class Score(Base):
    __tablename__ = "scores"
    score_id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey('rounds.round_id'), nullable=False)
    member_id = Column(Integer, ForeignKey('members.member_id'), nullable=False)
    front_score = Column(Integer, default=0)
    back_score = Column(Integer, default=0)
    extra_score = Column(Integer, default=0)
    front_putt = Column(Integer, default=0)
    back_putt = Column(Integer, default=0)
    extra_putt = Column(Integer, default=0)
    front_game_pt = Column(Integer, default=0)
    back_game_pt = Column(Integer, default=0)
    extra_game_pt = Column(Integer, default=0)

    member = relationship("Member", back_populates="scores")
    round = relationship("Round", back_populates="scores")
