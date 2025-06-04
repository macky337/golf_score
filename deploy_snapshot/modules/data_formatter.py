def highlight_total_only(row):
    """Total Only Modeがデータにない場合はスタイリングを適用しない（透明度を使用して他の色付けと両立）"""
    try:
        if "Total Only Mode" in row and row["Total Only Mode"] == "Yes":
            # Total Onlyモードの場合は金色のボーダーを追加
            return ['border: 3px solid #FFD700 !important; box-shadow: inset 0 0 0 1px #FFD700'] * len(row)
    except:
        pass
    return [''] * len(row)  # 何もスタイルを適用しない

def color_points(val):
    """数値に基づいて背景色を設定する（グラデーション対応）"""
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
            # プラス値: 薄緑色から濃い緑色へのグラデーション
            # 1-3: 薄緑, 4-6: 中緑, 7-9: 濃緑, 10+: 最濃緑
            if points <= 3:
                return 'background-color: #E8F5E8; color: black'  # 最薄緑
            elif points <= 6:
                return 'background-color: #C8E6C9; color: black'  # 薄緑
            elif points <= 9:
                return 'background-color: #A5D6A7; color: black'  # 中緑
            elif points <= 12:
                return 'background-color: #81C784; color: white'  # 濃緑
            else:
                return 'background-color: #66BB6A; color: white'  # 最濃緑
        elif points < 0:
            # マイナス値: 薄赤色から濃い赤色へのグラデーション
            # -1〜-3: 薄赤, -4〜-6: 中赤, -7〜-9: 濃赤, -10以下: 最濃赤
            abs_points = abs(points)
            if abs_points <= 3:
                return 'background-color: #FFEBEE; color: black'  # 最薄赤
            elif abs_points <= 6:
                return 'background-color: #FFCDD2; color: black'  # 薄赤
            elif abs_points <= 9:
                return 'background-color: #EF9A9A; color: black'  # 中赤
            elif abs_points <= 12:
                return 'background-color: #E57373; color: white'  # 濃赤
            else:
                return 'background-color: #EF5350; color: white'  # 最濃赤
        
        return 'background-color: #F0F0F0; color: black'  # 灰色（0点）
    except:
        return "background-color: transparent; color: black"  # 数値でない場合

def color_points_advanced(val):
    """数値に基づいて背景色を設定する（より細かいグラデーション対応）"""
    try:
        # 文字列として+や-が含まれる場合も処理
        if isinstance(val, str):
            val = val.strip()
            if val.startswith('+'):
                val = val[1:]  # "+"を除去
            if val == '' or val == '0':
                return 'background-color: #F0F0F0; color: black'  # 灰色（0点）
            points = int(val)
        else:
            points = int(val)
        
        if points > 0:
            # プラス値: より細かいグラデーション（1-15ポイントまで対応）
            intensity = min(points, 15)  # 最大15で制限
            # 緑色の透明度を段階的に調整
            if intensity <= 5:
                alpha = 0.2 + (intensity - 1) * 0.1  # 0.2-0.6
                return f'background-color: rgba(76, 175, 80, {alpha}); color: black'
            elif intensity <= 10:
                alpha = 0.6 + (intensity - 5) * 0.08  # 0.6-1.0
                return f'background-color: rgba(76, 175, 80, {alpha}); color: white'
            else:
                # 非常に高い値は最濃緑
                return 'background-color: #2E7D32; color: white'
                
        elif points < 0:
            # マイナス値: より細かいグラデーション
            abs_points = abs(points)
            intensity = min(abs_points, 15)  # 最大15で制限
            # 赤色の透明度を段階的に調整
            if intensity <= 5:
                alpha = 0.2 + (intensity - 1) * 0.1  # 0.2-0.6
                return f'background-color: rgba(244, 67, 54, {alpha}); color: black'
            elif intensity <= 10:
                alpha = 0.6 + (intensity - 5) * 0.08  # 0.6-1.0
                return f'background-color: rgba(244, 67, 54, {alpha}); color: white'
            else:
                # 非常に低い値は最濃赤
                return 'background-color: #C62828; color: white'
        
        return 'background-color: #F0F0F0; color: black'  # 灰色（0点）
    except:
        return "background-color: transparent; color: black"  # 数値でない場合


# 使用する色付け関数を選択する設定
USE_ADVANCED_COLORS = True  # Trueで高度なグラデーション、Falseで段階的グラデーション

def get_color_points_function():
    """使用する色付け関数を返す"""
    return color_points_advanced if USE_ADVANCED_COLORS else color_points

def color_score_columns(val):
    """スコア専用の色付け関数（正の数値のみ対応、より細かいグラデーション）"""
    try:
        if isinstance(val, str):
            val = val.strip()
            if val == '' or val == '0':
                return 'background-color: #F8F9FA; color: black'  # 極薄グレー（0スコア）
            score = int(val)
        else:
            score = int(val)
        
        if score <= 0:
            return 'background-color: #F8F9FA; color: black'  # 極薄グレー
        
        # スコア値に応じた青系グラデーション（低スコア=良い=濃い青、高スコア=悪い=薄い青）
        if score <= 30:
            # 30以下: 非常に良いスコア（濃い青）
            return 'background-color: #1565C0; color: white'
        elif score <= 35:
            # 31-35: 良いスコア（青）
            return 'background-color: #1976D2; color: white'
        elif score <= 40:
            # 36-40: まあまあのスコア（中青）
            return 'background-color: #2196F3; color: white'
        elif score <= 45:
            # 41-45: 普通のスコア（薄青）
            return 'background-color: #42A5F5; color: black'
        elif score <= 50:
            # 46-50: やや悪いスコア（更に薄い青）
            return 'background-color: #64B5F6; color: black'
        elif score <= 55:
            # 51-55: 悪いスコア（淡い青）
            return 'background-color: #90CAF9; color: black'
        elif score <= 60:
            # 56-60: かなり悪いスコア（極薄青）
            return 'background-color: #BBDEFB; color: black'
        else:
            # 61以上: 非常に悪いスコア（最薄青）
            return 'background-color: #E3F2FD; color: black'
            
    except:
        return "background-color: transparent; color: black"

def color_putt_columns(val):
    """パット専用の色付け関数（正の数値のみ対応、緑系グラデーション）"""
    try:
        if isinstance(val, str):
            val = val.strip()
            if val == '' or val == '0':
                return 'background-color: #F8F9FA; color: black'  # 極薄グレー（0パット）
            putt = int(val)
        else:
            putt = int(val)
        
        if putt <= 0:
            return 'background-color: #F8F9FA; color: black'  # 極薄グレー
        
        # パット数に応じた緑系グラデーション（少ないパット=良い=濃い緑、多いパット=悪い=薄い緑）
        if putt <= 12:
            # 12以下: 非常に良いパット（濃い緑）
            return 'background-color: #2E7D32; color: white'
        elif putt <= 15:
            # 13-15: 良いパット（緑）
            return 'background-color: #388E3C; color: white'
        elif putt <= 18:
            # 16-18: まあまあのパット（中緑）
            return 'background-color: #4CAF50; color: white'
        elif putt <= 21:
            # 19-21: 普通のパット（薄緑）
            return 'background-color: #66BB6A; color: black'
        elif putt <= 24:
            # 22-24: やや悪いパット（更に薄い緑）
            return 'background-color: #81C784; color: black'
        elif putt <= 27:
            # 25-27: 悪いパット（淡い緑）
            return 'background-color: #A5D6A7; color: black'
        elif putt <= 30:
            # 28-30: かなり悪いパット（極薄緑）
            return 'background-color: #C8E6C9; color: black'
        else:
            # 31以上: 非常に悪いパット（最薄緑）
            return 'background-color: #E8F5E8; color: black'
            
    except:
        return "background-color: transparent; color: black"

def get_color_function_for_column(column_name):
    """列名に応じて適切な色付け関数を返す"""
    score_columns = ['Front Score', 'Back Score', 'Extra Score', 'Total Score']
    putt_columns = ['Front Putt', 'Back Putt', 'Extra Putt', 'Putt Front', 'Putt Back', 'Putt Extra']
    
    if column_name in score_columns:
        return color_score_columns
    elif column_name in putt_columns:
        return color_putt_columns
    else:
        # ポイント列などは従来の関数を使用
        return get_color_points_function()

def get_ranking_colors_for_players(num_players):
    """プレイヤー数に応じた順位グラデーション色を返す"""
    if num_players == 3:
        return [
            'background-color: #FFD700; color: black; font-weight: bold',  # 1位: 金色
            'background-color: #C0C0C0; color: black; font-weight: bold',  # 2位: 銀色
            'background-color: #CD7F32; color: white; font-weight: bold'   # 3位: 銅色
        ]
    elif num_players == 4:
        return [
            'background-color: #FFD700; color: black; font-weight: bold',  # 1位: 金色
            'background-color: #C0C0C0; color: black; font-weight: bold',  # 2位: 銀色
            'background-color: #CD7F32; color: white; font-weight: bold',  # 3位: 銅色
            'background-color: #F0F0F0; color: black; font-weight: bold'   # 4位: 薄灰色
        ]
    else:
        # 5人以上の場合はより細かいグラデーション
        colors = [
            'background-color: #FFD700; color: black; font-weight: bold',  # 1位: 金色
            'background-color: #C0C0C0; color: black; font-weight: bold',  # 2位: 銀色
            'background-color: #CD7F32; color: white; font-weight: bold',  # 3位: 銅色
            'background-color: #E8E8E8; color: black; font-weight: bold',  # 4位: 薄灰色
            'background-color: #F5F5F5; color: black; font-weight: bold'   # 5位: 極薄灰色
        ]
        # 6位以降は段階的に薄くしていく
        for i in range(5, num_players):
            opacity = max(0.3, 1.0 - (i - 4) * 0.1)
            colors.append(f'background-color: rgba(200, 200, 200, {opacity}); color: black; font-weight: bold')
        return colors

def create_ranking_color_function(df, column_name):
    """指定された列の値に基づいて順位グラデーション関数を作成する"""
    try:
        # DataFrameから指定された列の値を取得して順位を計算
        score_columns = ['Front Score', 'Back Score', 'Extra Score', 'Total Score']
        putt_columns = ['Front Putt', 'Back Putt', 'Extra Putt', 'Putt Front', 'Putt Back', 'Putt Extra']
        
        if column_name in score_columns or column_name in putt_columns:
            # スコア・パット列は昇順（少ない方が良い）
            ascending = True
        else:
            # ポイント列は降順（多い方が良い）
            ascending = False
        
        # 数値に変換して順位を計算
        values = []
        row_indices = []
        
        for idx, val in df[column_name].items():
            try:
                if isinstance(val, str):
                    val = val.strip()
                    if val.startswith('+'):
                        val = val[1:]
                    if val == '' or val == '-':
                        continue
                num_val = float(val)
                values.append((num_val, idx))
                row_indices.append(idx)
            except:
                continue
        
        if not values:
            # 値が取得できない場合は通常の色付け関数を返す
            return get_color_function_for_column(column_name)
        
        # 順位を計算
        if ascending:
            values.sort(key=lambda x: x[0])  # 昇順
        else:
            values.sort(key=lambda x: x[0], reverse=True)  # 降順
        
        # 順位に基づく色を取得
        num_players = len(values)
        ranking_colors = get_ranking_colors_for_players(num_players)
        
        # プレイヤーごとの色マッピングを作成
        color_mapping = {}
        for rank, (val, idx) in enumerate(values):
            if rank < len(ranking_colors):
                color_mapping[idx] = ranking_colors[rank]
            else:
                color_mapping[idx] = 'background-color: #FFFFFF; color: black'
        
        def ranking_color_func(val):
            # 現在の行のインデックスを取得するために、DataFrameの行名を利用
            # この関数はmap()で呼び出されるため、行のコンテキストが必要
            return 'background-color: transparent; color: black'
        
        # より良いアプローチ: 行全体に適用する関数を返す
        return lambda val: 'background-color: transparent; color: black'
        
    except Exception as e:
        # エラーが発生した場合は通常の色付け関数を使用
        return get_color_function_for_column(column_name)

def apply_ranking_colors_to_dataframe(df, column_name):
    """DataFrameの特定列に対して順位ベースの色付けを適用（改良版）"""
    try:
        score_columns = ['Front Score', 'Back Score', 'Extra Score', 'Total Score']
        putt_columns = ['Front Putt', 'Back Putt', 'Extra Putt', 'Putt Front', 'Putt Back', 'Putt Extra']
        
        if column_name in score_columns or column_name in putt_columns:
            ascending = True  # スコア・パット列は昇順（少ない方が良い）
        else:
            ascending = False  # ポイント列は降順（多い方が良い）
        
        # 数値に変換して順位を計算
        numeric_values = {}
        for idx, val in df[column_name].items():
            try:
                if isinstance(val, str):
                    val = val.strip()
                    if val.startswith('+'):
                        val = val[1:]
                    if val == '' or val == '-':
                        continue
                numeric_values[idx] = float(val)
            except:
                continue
        
        if not numeric_values:
            return ['background-color: transparent; color: black'] * len(df)
        
        # 順位を計算（同点の場合は同順位）
        sorted_values = sorted(set(numeric_values.values()), reverse=not ascending)
        
        # 順位に基づく色を取得
        num_players = len(numeric_values)
        ranking_colors = get_ranking_colors_for_players(num_players)
        
        # 各行の色を決定
        row_colors = []
        for idx in df.index:
            if idx in numeric_values:
                player_value = numeric_values[idx]
                # この値の順位を取得
                rank = sorted_values.index(player_value)
                if rank < len(ranking_colors):
                    row_colors.append(ranking_colors[rank])
                else:
                    row_colors.append('background-color: #FFFFFF; color: black')
            else:
                row_colors.append('background-color: transparent; color: black')
        
        return row_colors
        
    except Exception as e:
        print(f"Error in apply_ranking_colors_to_dataframe: {e}")
        return ['background-color: transparent; color: black'] * len(df)

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
