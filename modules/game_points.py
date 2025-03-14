"""
ゲームポイント計算ロジックを提供するモジュール
各セクション（フロント、バック、エキストラ）のゲームポイントは
ユーザーが手動で入力し、最終的なGame Ptのみを計算します。
"""

def calculate_game_pt(player_pts, other_pts):
    """3人プレイ時の最終ゲームポイントを計算する
    
    Args:
        player_pts (int): プレイヤーの一時的なゲームポイント合計
        other_pts (list): 他のプレイヤーの一時的なゲームポイント合計のリスト
    
    Returns:
        int: 計算された最終ゲームポイント
    
    Note:
        3人プレーの場合：自分のポイント×2 - 他の2人の合計
        4人プレーの場合：そのままのポイント
    """
    if len(other_pts) == 2:  # 3人プレー
        return player_pts * 2 - sum(other_pts)
    return player_pts  # 4人プレー

def calculate_total_game_points(front_gp, back_gp, extra_gp, n_players):
    """最終的なGame Ptを計算する
    
    Args:
        front_gp (dict): プレイヤーIDとフロントゲームポイントのマッピング
        back_gp (dict): プレイヤーIDとバックゲームポイントのマッピング
        extra_gp (dict): プレイヤーIDとエキストラゲームポイントのマッピング
        n_players (int): プレイヤー数
    
    Returns:
        dict: プレイヤーIDと最終ゲームポイントのマッピング
    """
    # 一時的なGame Ptを計算（各セクションの合計）
    temp_game_pts = {}
    for player_id in front_gp:
        temp_game_pts[player_id] = (
            front_gp.get(player_id, 0) +
            back_gp.get(player_id, 0) +
            extra_gp.get(player_id, 0)
        )
    
    # プレイヤー数に応じて最終的なGame Ptを計算
    final_game_pts = {}
    if n_players == 3:
        # 3人の場合: 自分のポイント×2 - 他の2人の合計
        for player_id in temp_game_pts:
            others_pts = [pt for pid, pt in temp_game_pts.items() if pid != player_id]
            final_game_pts[player_id] = calculate_game_pt(temp_game_pts[player_id], others_pts)
    else:
        # 4人の場合: そのまま採用
        final_game_pts = temp_game_pts
    
    return final_game_pts