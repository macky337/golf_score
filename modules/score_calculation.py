import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_putt_points(putt_scores):
    """
    より堅牢なパット戦ポイント計算
    
    Args:
        putt_scores (dict): プレイヤーIDとパットスコアのマッピング
        
    Returns:
        dict: プレイヤーIDとパットポイントのマッピング
    """
    if not putt_scores:
        return {}
    
    try:
        # None値や無効な値を0に置換したコピーを作成
        clean_scores = {}
        for player_id, score in putt_scores.items():
            try:
                clean_score = 0 if score is None else int(score)
                clean_scores[player_id] = clean_score
            except (ValueError, TypeError):
                logger.warning(f"Invalid putt score for player {player_id}: {score}. Using 0.")
                clean_scores[player_id] = 0
        
        # プレイヤー数を取得
        n_players = len(clean_scores)
        if n_players == 0:
            return {}
        
        # 最小スコアとそのプレイヤーを特定
        min_score = min(clean_scores.values())
        winners = [p_id for p_id, score in clean_scores.items() if score == min_score]
        n_winners = len(winners)
        
        # 初期ポイント配列
        points = {p_id: 0 for p_id in clean_scores}
        
        # プレイヤー数に基づいて処理
        if n_players == 3:
            # 3人プレー
            if n_winners == 1:
                # 1人勝ち: 勝者+20, 他-10
                points[winners[0]] = 20
                for p_id in clean_scores:
                    if p_id not in winners:
                        points[p_id] = -10
            elif n_winners == 2:
                # 2人勝ち: 勝者+5, 他-10
                for p_id in clean_scores:
                    if p_id in winners:
                        points[p_id] = 5
                    else:
                        points[p_id] = -10
            # 3人同点: 全員0
        
        elif n_players == 4:
            # 4人プレー
            if n_winners == 1:
                # 1人勝ち: 勝者+30, 他-10
                points[winners[0]] = 30
                for p_id in clean_scores:
                    if p_id not in winners:
                        points[p_id] = -10
            elif n_winners == 2:
                # 2人勝ち: 勝者+10, 他-10
                for p_id in clean_scores:
                    if p_id in winners:
                        points[p_id] = 10
                    else:
                        points[p_id] = -10
            elif n_winners == 3:
                # 3人勝ち: 勝者+10, 他-30
                for p_id in clean_scores:
                    if p_id in winners:
                        points[p_id] = 10
                    else:
                        points[p_id] = -30
            # 4人同点: 全員0
            
        else:
            # それ以外のプレイヤー数の場合はゼロサム原則を適用
            logger.warning(f"Unusual player count: {n_players}. Using zero-sum principle.")
            if n_winners < n_players:
                # 勝者には正のポイント、敗者には負のポイント
                winner_points = 10 * (n_players - n_winners)
                loser_points = -1 * (n_winners * winner_points) / (n_players - n_winners)
                
                for p_id in clean_scores:
                    if p_id in winners:
                        points[p_id] = winner_points
                    else:
                        points[p_id] = loser_points
        
        # ポイント合計が0であることを検証
        total = sum(points.values())
        if abs(total) > 0.01:  # 浮動小数点誤差を許容
            logger.warning(f"Point calculation error: sum is not zero ({total}). Adjusting...")
            # 調整（最初のプレイヤーのポイントを調整）
            if clean_scores:
                first_player = next(iter(clean_scores))
                points[first_player] -= total
        
        return points
        
    except Exception as e:
        logger.error(f"Error calculating putt points: {e}")
        return {p_id: 0 for p_id in putt_scores}
