#!/usr/bin/env python3
import sqlite3
import pandas as pd

def analyze_point_balance():
    # データベースに接続
    conn = sqlite3.connect('data/golf_data.db')
    
    try:
        # 全てのポイントを確認
        query = '''
        SELECT 
            round_id,
            player_name,
            total_pt,
            receive_amount,
            pay_amount
        FROM results
        ORDER BY round_id DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        print('最近のラウンドのポイント詳細:')
        print(df.head(20))
        
        # 全体のポイント合計を確認
        total_pts = df['total_pt'].sum()
        total_receive = df['receive_amount'].sum()
        total_pay = df['pay_amount'].sum()
        
        print(f'\n=== ポイントバランス分析 ===')
        print(f'全Total Pt合計: {total_pts}')
        print(f'全Receive合計: {total_receive}')
        print(f'全Pay合計: {total_pay}')
        print(f'Receive - Pay: {total_receive - total_pay}')
        
        # ラウンド別の合計を確認
        round_summary = df.groupby('round_id').agg({
            'total_pt': 'sum',
            'receive_amount': 'sum',
            'pay_amount': 'sum'
        }).reset_index()
        
        round_summary['balance'] = round_summary['total_pt']
        
        print(f'\n=== ラウンド別バランス ===')
        print(round_summary)
        
        # バランスが0でないラウンドを特定
        unbalanced_rounds = round_summary[round_summary['balance'] != 0]
        if not unbalanced_rounds.empty:
            print(f'\n=== バランスが取れていないラウンド ===')
            print(unbalanced_rounds)
            
            # 詳細を確認
            for round_id in unbalanced_rounds['round_id']:
                print(f'\nラウンド {round_id} の詳細:')
                round_details = df[df['round_id'] == round_id]
                print(round_details[['player_name', 'total_pt', 'receive_amount', 'pay_amount']])
                print(f'合計: Total Pt={round_details["total_pt"].sum()}, Receive={round_details["receive_amount"].sum()}, Pay={round_details["pay_amount"].sum()}')
        
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_point_balance()
