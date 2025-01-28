# modules/models.py
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from modules.db import Base

class Member(Base):
    __tablename__ = "members"
    member_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    base_handicap = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    scores = relationship("Score", back_populates="member")
    match_handicaps_given = relationship(
        "MatchHandicap", 
        back_populates="giver", 
        foreign_keys='MatchHandicap.giver_id'
    )
    match_handicaps_received = relationship(
        "MatchHandicap", 
        back_populates="receiver", 
        foreign_keys='MatchHandicap.receiver_id'
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
    front_game_pt = Column(Integer, default=0)
    back_game_pt = Column(Integer, default=0)
    extra_game_pt = Column(Integer, default=0)

    round = relationship("Round", back_populates="scores")
    member = relationship("Member", back_populates="scores")

class MatchHandicap(Base):
    __tablename__ = "match_handicap"
    match_handicap_id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey("rounds.round_id"))
    giver_id = Column(Integer, ForeignKey("members.member_id"))
    receiver_id = Column(Integer, ForeignKey("members.member_id"))
    half_hcp = Column(Integer, default=0)
    
    round = relationship("Round", back_populates="match_handicaps")
    giver = relationship(
        "Member", 
        back_populates="match_handicaps_given", 
        foreign_keys=[giver_id]
    )
    receiver = relationship(
        "Member", 
        back_populates="match_handicaps_received", 
        foreign_keys=[receiver_id]
    )
