def highlight_total_only(row):
    """Total Only Modeがデータにない場合はスタイリングを適用しない"""
    try:
        if "Total Only Mode" in row and row["Total Only Mode"] == "Yes":
            return ['background-color: #FFD700; color: black'] * len(row)
    except:
        pass
    return ['background-color: #E6F3FF; color: black'] * len(row)

def color_points(val):
    """数値に基づいて背景色を設定する"""
    try:
        # 文字列として+や-が含まれる場合も処理
        if isinstance(val, str):
            # "+10", "-5", "10", "-10" などの文字列を数値に変換
            val = val.strip()
            if val.startswith('+'):
                val = val[1:]  # "+"を除去
            # 空文字列や"0"でない場合のみ数値変換を試行
            if val == '' or val == '0':
                return 'background-color: #F0F0F0; color: black'  # 灰色（0点）
            points = int(val)
        else:
            points = int(val)
        
        if points > 0:
            return 'background-color: #C8E6C9; color: black'  # 薄緑色の塗りつぶし
        elif points < 0:
            return 'background-color: #FFCDD2; color: black'  # 薄赤色の塗りつぶし
        return 'background-color: #F0F0F0; color: black'  # 灰色（0点）
    except:
        return "background-color: transparent; color: black"  # 数値でない場合

def initialize_player_data(scores, round_results):
    player_data = {}
    for sc in scores:
        member_id = sc['member_id']
        player_name = sc['member']['name'] if ('member' in sc and sc['member']) else f"Player {member_id}"
        # DB側のキーがスネークケースの場合
        round_result_data = round_results.get(member_id, {}) if round_results else {}
        
        player_data[member_id] = {
            "Player": player_name,
            "Front Score": sc.get('front_score', 0) or 0,
            "Back Score": sc.get('back_score', 0) or 0,
            "Extra Score": sc.get('extra_score', 0) or 0,
            "Total Score": (sc.get('front_score', 0) or 0) + (sc.get('back_score', 0) or 0),
            "Front GP": sc.get('front_game_pt', 0) or 0,
            "Back GP": sc.get('back_game_pt', 0) or 0,
            "Extra GP": sc.get('extra_game_pt', 0) or 0,
            "Game Pt": ((sc.get('front_game_pt', 0) or 0)
                       + (sc.get('back_game_pt', 0) or 0)
                       + (sc.get('extra_game_pt', 0) or 0)),
            # キー名を DB のテーブル構造に合わせる（両方のケースを試す）
            "Match Front": round_result_data.get("Match Front", round_result_data.get("match_front", 0)),
            "Match Back":  round_result_data.get("Match Back", round_result_data.get("match_back", 0)),
            "Match Total": round_result_data.get("Match Total", round_result_data.get("match_total", 0)),
            "Match Extra": round_result_data.get("Match Extra", round_result_data.get("match_extra", 0)),
            "Match Pt":    round_result_data.get("Match Pt", round_result_data.get("match_pt", 0)),
            # パット情報の両方の命名規則に対応（互換性確保）
            "Putt Front": sc.get('front_putt', 0) or 0,
            "Front Putt": sc.get('front_putt', 0) or 0,  # 追加: 別形式のキー名でも対応
            "Putt Back": sc.get('back_putt', 0) or 0,
            "Back Putt": sc.get('back_putt', 0) or 0,    # 追加: 別形式のキー名でも対応
            "Putt Extra": sc.get('extra_putt', 0) or 0,
            "Extra Putt": sc.get('extra_putt', 0) or 0,  # 追加: 別形式のキー名でも対応
            "Putt Pt": round_result_data.get("Putt Pt", round_result_data.get("putt_pt", 0)),
            "Total Pt": sc.get('total_pt', 0) or 0
        }
    return player_data
