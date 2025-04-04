from modules.calculation_logic import calculate_player_points  # モジュールパスを修正

def test_3player_game_point_calculation():
    """3人プレイのゲームポイント計算をテストする関数"""
    print("===== 3人プレイのゲームポイント計算テスト =====")
    
    # テスト用プレイヤーデータを作成（荒巻、吉井、福澤の例）
    player_data = {
        1: {  # 荒巻
            "Front Score": 40, 
            "Back Score": 43,
            "Front Putt": 15,
            "Back Putt": 16,
            "Front GP": 39,  # 既に決定されたフロントのゲームポイント
            "Back GP": 30
        },
        2: {  # 吉井
            "Front Score": 42, 
            "Back Score": 41,
            "Front Putt": 17,
            "Back Putt": 14,
            "Front GP": 6,  # 既に決定されたフロントのゲームポイント
            "Back GP": 0 
        },
        3: {  # 福澤
            "Front Score": 41, 
            "Back Score": 42,
            "Front Putt": 16,
            "Back Putt": 15,
            "Front GP": 9,  # 既に決定されたフロントのゲームポイント
            "Back GP": -30
        }
    }
    
    # 入力データを保存して後で比較できるようにする
    original_data = {
        pid: {
            "Front GP": data["Front GP"],
            "Back GP": data["Back GP"]
        } for pid, data in player_data.items()
    }
    
    player_ids = [1, 2, 3]
    handicaps = {}  # テスト用に空のハンディキャップ
    total_only_set = set()  # トータルオンリーでないと仮定
    
    # テスト用のアクティブラウンド情報
    active_round = {
        'round_id': 999,  # テスト用ID
        'has_extra': False,
        'is_test': True   # テストフラグを追加
    }
    
    print("テスト入力データ:")
    for pid, data in player_data.items():
        print(f"Player {pid}: Front GP={data['Front GP']}, Back GP={data['Back GP']}")
    
    print("\nゲームポイント計算実行中...")
    results = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)
    
    print("\n入力値と計算前の値の比較:")
    for pid, data in results.items():
        original = original_data[pid]
        print(f"Player {pid}: 元のFront GP={original['Front GP']}, 計算前Front GP={data['Front GP']}")
        print(f"Player {pid}: 元のBack GP={original['Back GP']}, 計算前Back GP={data['Back GP']}")
        if original['Front GP'] != data['Front GP'] or original['Back GP'] != data['Back GP']:
            print(f"ERROR: Player {pid}のGPが変更されています！")
    
    print("\nテスト結果:")
    print("期待される結果:")
    print("荒巻(1): Front=39*2-(6+9)=63, Back=30*2-(0-30)=90, 合計=153")
    print("吉井(2): Front=6*2-(39+9)=-36, Back=0*2-(30-30)=0, 合計=-36")
    print("福澤(3): Front=9*2-(39+6)=-27, Back=-30*2-(30+0)=-90, 合計=-117")
    
    print("\n実際の計算結果:")
    for pid, data in results.items():
        print(f"Player {pid}: Game Pt={data['Game Pt']}, Total Game Pt={data.get('total_game_pt', '未設定')}")

        # Front/Back別の計算結果も表示
        front_gp = data["Front GP"]
        back_gp = data["Back GP"]
        others_front_gp = sum(results[oid]["Front GP"] for oid in player_ids if oid != pid)
        others_back_gp = sum(results[oid]["Back GP"] for oid in player_ids if oid != pid)
        
        front_calc = front_gp * 2 - others_front_gp
        back_calc = back_gp * 2 - others_back_gp
        
        print(f"  Front: {front_gp}*2-{others_front_gp}={front_calc}")
        print(f"  Back: {back_gp}*2-{others_back_gp}={back_calc}")
        print(f"  合計: {front_calc + back_calc}\n")
    
    # データベースのテーブル構造確認のための情報を追加
    print("\nデータベースカラム名とコードの変数名マッピング:")
    print("round_results テーブルではプレイヤーIDは 'member_id' カラムに保存されます")
    print("score テーブルでもプレイヤーIDは 'member_id' カラムに保存されます")  # 'player_id'から'member_id'に修正
    
    print("テスト完了")
    
    return results

if __name__ == "__main__":
    test_3player_game_point_calculation()
