def calculate_match_points(player_i, player_j, handicap_ij, handicap_ji, is_total_only=False):
    """1対1のマッチポイント計算（各セクション±10pt）- 修正版ロジック"""
    front_pt = back_pt = total_pt = extra_pt = 0

    # スコアの取得と安全化
    front_score_i = player_i.get('front_score', 0) or 0
    back_score_i = player_i.get('back_score', 0) or 0
    extra_score_i = player_i.get('extra_score', 0) or 0
    
    front_score_j = player_j.get('front_score', 0) or 0
    back_score_j = player_j.get('back_score', 0) or 0
    extra_score_j = player_j.get('extra_score', 0) or 0

    # バックとエキストラのプレイ状態を確認（両方とも0より大きい場合にプレイ済みと判断）
    has_back = back_score_i > 0 and back_score_j > 0
    has_extra = extra_score_i > 0 and extra_score_j > 0
    
    if is_total_only:
        # Total Onlyモードでは、バックスコアまたはエキストラスコアがある場合のみ判定
        # フロント9だけの場合は判定しない（0-0のまま）
        
        # フロントとバックのスコアが入力されている場合
        if has_back:
            # フロント+バックの合計を比較（ハンディキャップは相手のスコアから引く）
            # handicap_ijはプレイヤーiからjへのハンディキャップなのでjのスコアから引く
            net_score_i = front_score_i + back_score_i
            net_score_j = (front_score_j + back_score_j) - handicap_ij
            if net_score_i < net_score_j:
                # iの方がスコアが良い場合はプラスポイント
                total_pt = 10
            elif net_score_i > net_score_j:
                # iの方がスコアが悪い場合はマイナスポイント
                total_pt = -10
        else:
            # バックスコアがない場合は判定しない（0-0）
            total_pt = 0
            
        # エキストラスコアの比較（両方プレイしている場合のみ）
        if has_extra:
            # エキストラ9のハンディキャップは適用
            net_extra_i = extra_score_i
            net_extra_j = extra_score_j - handicap_ij
            if net_extra_i < net_extra_j:
                # iの方がスコアが良い場合はプラスポイント
                extra_pt = 10
            elif net_extra_i > net_extra_j:
                # iの方がスコアが悪い場合はマイナスポイント
                extra_pt = -10
                
        # Front/Backのポイントはゼロ（Total Only モードでは計算しない）
        front_pt = 0
        back_pt = 0
    else:
        # 通常モード - 各セクションごとに比較
        
        # フロントスコアの比較（フロントは必ず比較）
        # ハンディキャップは相手のスコアから引く
        net_front_i = front_score_i
        net_front_j = front_score_j - handicap_ij
        if net_front_i < net_front_j:
            # iの方がスコアが良い場合はプラスポイント
            front_pt = 10
        elif net_front_i > net_front_j:
            # iの方がスコアが悪い場合はマイナスポイント
            front_pt = -10
            
        # バックスコアの比較（両方のスコアが入力されている場合のみ）
        if has_back:
            # バック9のハンディキャップも適用
            net_back_i = back_score_i
            net_back_j = back_score_j - handicap_ij
            if net_back_i < net_back_j:
                # iの方がスコアが良い場合はプラスポイント
                back_pt = 10  
            elif net_back_i > net_back_j:
                # iの方がスコアが悪い場合はマイナスポイント
                back_pt = -10
            
            # トータルスコアはバックスコアが入力されている場合のみ比較
            net_total_i = front_score_i + back_score_i
            net_total_j = (front_score_j + back_score_j) - handicap_ij
            if net_total_i < net_total_j:
                # iの方がスコアが良い場合はプラスポイント
                total_pt = 10
            elif net_total_i > net_total_j:
                # iの方がスコアが悪い場合はマイナスポイント
                total_pt = -10
        else:
            # バックが入力されていない場合、バックとトータルのポイントは計算しない
            back_pt = 0
            total_pt = 0
                
        # エキストラスコアの比較（両方プレイしている場合のみ）
        if has_extra:
            # エキストラ9のハンディキャップも適用
            net_extra_i = extra_score_i
            net_extra_j = extra_score_j - handicap_ij
            if net_extra_i < net_extra_j:
                # iの方がスコアが良い場合はプラスポイント
                extra_pt = 10
            elif net_extra_i > net_extra_j:
                # iの方がスコアが悪い場合はマイナスポイント
                extra_pt = -10
        else:
            extra_pt = 0

    # 合計ポイントを計算
    total_points_i = front_pt + back_pt + total_pt + extra_pt
    total_points_j = -(front_pt + back_pt + total_pt + extra_pt)
    
    # デバッグ情報も返す
    details = {
        "front": front_pt,
        "back": back_pt, 
        "total": total_pt,
        "extra": extra_pt,
        "has_back": has_back,
        "has_extra": has_extra,
        # デバッグ用にネットスコアも追加（ハンディキャップ適用後）
        "front_net_i": front_score_i,
        "front_net_j": front_score_j - handicap_ij,
        "back_net_i": back_score_i if has_back else None,
        "back_net_j": back_score_j - handicap_ij if has_back else None,
        "total_net_i": front_score_i + back_score_i if has_back else None,
        "total_net_j": (front_score_j + back_score_j) - handicap_ij if has_back else None
    }
    
    return total_points_i, total_points_j, details
