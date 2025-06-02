import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, Date, Boolean, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

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
    round_id = Column(Integer, ForeignKey('rounds.round_id'), nullable=False)
    player_1_id = Column(Integer, ForeignKey('member.member_id'), nullable=False)
    player_2_id = Column(Integer, ForeignKey('member.member_id'), nullable=False)
    player_1_to_2 = Column(Integer, default=0)
    player_2_to_1 = Column(Integer, default=0)
    total_only = Column(Boolean, default=False)  # total スコアのみで判定するフラグ

    # リレーションシップを追加
    player_1 = relationship("Member", foreign_keys=[player_1_id])
    player_2 = relationship("Member", foreign_keys=[player_2_id])

from modules.db import supabase

def get_course_list():
    """コース一覧を取得する"""
    try:
        result = supabase.table('courses').select('*').order('name').execute()
        return result.data
    except Exception as e:
        print(f"コース一覧取得エラー: {str(e)}")
        return []

def get_course_by_id(course_id):
    """IDでコースを取得する"""
    try:
        result = supabase.table('courses').select('*').eq('id', course_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"コース取得エラー: {str(e)}")
        return None

def get_course_by_name(course_name):
    """名前でコースを検索する"""
    try:
        result = supabase.table('courses').select('*').ilike('name', course_name).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"コース検索エラー: {str(e)}")
        return None

def create_course(course_name):
    """新しいコースを作成する"""
    try:
        # 既存のコースをチェック
        existing = get_course_by_name(course_name)
        if existing:
            return existing
        
        # 新しいコースを追加
        result = supabase.table('courses').insert({'name': course_name}).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"コース作成エラー: {str(e)}")
        return None

def get_or_create_course(course_name):
    """コースを取得または作成する"""
    course = get_course_by_name(course_name)
    if course:
        return course
    return create_course(course_name)

def is_course_in_use(course_id):
    """コースがラウンドで使用されているか確認する"""
    try:
        result = supabase.table('rounds').select('count').eq('course_id', course_id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"コース使用確認エラー: {str(e)}")
        return False

def get_unused_courses():
    """使用されていないゴルフ場の一覧を取得する"""
    try:
        # 全てのコースを取得
        courses_result = supabase.table('courses').select('*').order('name').execute()
        courses = courses_result.data
        
        # 使用されているコースIDを取得
        used_courses_result = supabase.table('rounds').select('course_id').execute()
        used_course_ids = set()
        for round_data in used_courses_result.data:
            if round_data.get('course_id'):
                used_course_ids.add(round_data['course_id'])
        
        # 未使用のコースをフィルタリング
        unused_courses = []
        for course in courses:
            if course['id'] not in used_course_ids:
                unused_courses.append(course)
        
        return unused_courses
    except Exception as e:
        print(f"未使用コース取得エラー: {str(e)}")
        return []

def delete_unused_courses():
    """未使用のゴルフ場を一括削除する"""
    try:
        unused_courses = get_unused_courses()
        if not unused_courses:
            return 0, "削除対象の未使用ゴルフ場がありません"
        
        deleted_count = 0
        deleted_names = []
        
        for course in unused_courses:
            try:
                result = supabase.table('courses').delete().eq('id', course['id']).execute()
                if result.data:
                    deleted_count += 1
                    deleted_names.append(course['name'])
            except Exception as e:
                print(f"コース {course['name']} の削除に失敗: {str(e)}")
        
        if deleted_count > 0:
            return deleted_count, f"以下の{deleted_count}個の未使用ゴルフ場を削除しました: {', '.join(deleted_names)}"
        else:
            return 0, "ゴルフ場の削除に失敗しました"
        
    except Exception as e:
        return 0, f"未使用ゴルフ場削除エラー: {str(e)}"

def get_members_list():
    """メンバー一覧を取得する（ID昇順）"""
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        supabase = create_client(supabase_url, supabase_key)
        
        response = supabase.table('member').select('*').order('member_id').execute()
        return response.data
    except Exception as e:
        print(f"メンバー一覧取得エラー: {str(e)}")
        return []

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
    provided_date_played = datetime.date.today()  # Define provided_date_played with today's date or any specific date

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
