from modules.supabase_client import get_supabase_client
import streamlit as st
import time

def fix_foreign_key_constraint():
    """
    round_resultsテーブルの外部キー制約をmembersからmemberに変更する
    """
    try:
        supabase = get_supabase_client()
        
        # Step 1: 既存の外部キー制約を削除
        print("Step 1: 既存の外部キー制約の削除を試みます...")
        drop_constraint_sql = """
        ALTER TABLE IF EXISTS round_results
        DROP CONSTRAINT IF EXISTS round_results_member_id_fkey;
        """
        
        # 外部キー制約を削除
        supabase.table('round_results').select('*').limit(1).execute()  # テーブルが存在するか確認
        
        # カスタムSQLを実行（直接SQLを実行できない場合はRPCを使用）
        response = supabase.rest("rpc", {
            "method": "POST",
            "body": {
                "name": "sql_query",
                "type": "action",
                "query": drop_constraint_sql
            }
        }).execute()
        
        print(f"外部キー制約の削除結果: {response.data}")
        
        # Step 2: 新しい外部キー制約（memberテーブル参照）を追加
        print("Step 2: 新しい外部キー制約を追加します...")
        add_constraint_sql = """
        ALTER TABLE IF EXISTS round_results
        ADD CONSTRAINT round_results_member_id_fkey
        FOREIGN KEY (member_id) REFERENCES member(member_id);
        """
        
        response = supabase.rest("rpc", {
            "method": "POST",
            "body": {
                "name": "sql_query",
                "type": "action",
                "query": add_constraint_sql
            }
        }).execute()
        
        print(f"新規外部キー制約の追加結果: {response.data}")
        
        # 成功メッセージ
        print("外部キー制約の修正が完了しました。")
        return True
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False

def workaround_solution():
    """
    外部キー制約の修正が難しい場合の回避策を実装
    """
    try:
        supabase = get_supabase_client()
        
        # Step 1: round_resultsテーブルを一時退避
        print("Step 1: round_resultsテーブルを退避中...")
        backup_table_sql = """
        CREATE TABLE IF NOT EXISTS round_results_backup AS 
        SELECT * FROM round_results;
        """
        
        response = supabase.rest("rpc", {
            "method": "POST",
            "body": {
                "name": "sql_query",
                "type": "action",
                "query": backup_table_sql
            }
        }).execute()
        
        # Step 2: 既存のround_resultsテーブルを削除
        print("Step 2: 既存のround_resultsテーブルを削除中...")
        drop_table_sql = """
        DROP TABLE IF EXISTS round_results;
        """
        
        response = supabase.rest("rpc", {
            "method": "POST",
            "body": {
                "name": "sql_query",
                "type": "action",
                "query": drop_table_sql
            }
        }).execute()
        
        # Step 3: 正しい外部キー制約を持つ新しいテーブルを作成
        print("Step 3: 正しい外部キー制約を持つ新しいテーブルを作成中...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS round_results (
            id BIGSERIAL PRIMARY KEY,
            round_id BIGINT NOT NULL,
            member_id BIGINT NOT NULL,
            match_front INTEGER DEFAULT 0,
            match_back INTEGER DEFAULT 0,
            match_total INTEGER DEFAULT 0,
            match_extra INTEGER DEFAULT 0,
            match_pt INTEGER DEFAULT 0,
            putt_pt INTEGER DEFAULT 0,
            temp_game_pt INTEGER DEFAULT 0,
            total_game_pt INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            FOREIGN KEY (round_id) REFERENCES rounds(round_id),
            FOREIGN KEY (member_id) REFERENCES member(member_id),
            UNIQUE(round_id, member_id)
        );
        """
        
        response = supabase.rest("rpc", {
            "method": "POST",
            "body": {
                "name": "sql_query",
                "type": "action",
                "query": create_table_sql
            }
        }).execute()
        
        # Step 4: バックアップからデータを復元（memberテーブルに存在するIDのみ）
        print("Step 4: バックアップからデータを復元中...")
        restore_data_sql = """
        INSERT INTO round_results (
            round_id, member_id, match_front, match_back, match_total, match_extra,
            match_pt, putt_pt, temp_game_pt, total_game_pt, created_at, updated_at
        )
        SELECT 
            b.round_id, b.member_id, b.match_front, b.match_back, b.match_total, b.match_extra,
            b.match_pt, b.putt_pt, b.temp_game_pt, b.total_game_pt, b.created_at, b.updated_at
        FROM 
            round_results_backup b
        JOIN 
            member m ON b.member_id = m.member_id;
        """
        
        response = supabase.rest("rpc", {
            "method": "POST",
            "body": {
                "name": "sql_query",
                "type": "action",
                "query": restore_data_sql
            }
        }).execute()
        
        print("テーブルの再作成と外部キー制約の修正が完了しました。")
        return True
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False

def create_members_table_with_data():
    """
    membersテーブルを作成し、memberテーブルからデータをコピーする
    """
    try:
        supabase = get_supabase_client()
        
        # Step 1: membersテーブルを作成
        print("Step 1: membersテーブルを作成...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS members (
            member_id BIGSERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        response = supabase.rest("rpc", {
            "method": "POST",
            "body": {
                "name": "sql_query",
                "type": "action",
                "query": create_table_sql
            }
        }).execute()
        
        # Step 2: memberテーブルからデータをコピー
        print("Step 2: memberテーブルからデータをmembersテーブルへコピー...")
        copy_data_sql = """
        INSERT INTO members (member_id, name, created_at, updated_at)
        SELECT member_id, name, created_at, updated_at
        FROM member
        ON CONFLICT (member_id) DO NOTHING;
        """
        
        response = supabase.rest("rpc", {
            "method": "POST",
            "body": {
                "name": "sql_query",
                "type": "action",
                "query": copy_data_sql
            }
        }).execute()
        
        print("membersテーブルの作成とデータのコピーが完了しました。")
        return True
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False

def main():
    print("このスクリプトはround_resultsテーブルの外部キー制約の問題を修正します")
    print("以下の選択肢から実行する操作を選んでください:")
    print("1. 外部キー制約を修正する（membersからmemberへ）")
    print("2. テーブルの再作成による対応（データを保持）")
    print("3. membersテーブルを作成しデータをコピー")
    
    choice = input("選択肢の番号を入力してください (1-3): ")
    
    if choice == "1":
        fix_foreign_key_constraint()
    elif choice == "2":
        workaround_solution()
    elif choice == "3":
        create_members_table_with_data()
    else:
        print("無効な選択です。1、2、または3を入力してください。")

if __name__ == "__main__":
    main()