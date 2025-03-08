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
        points = int(val)
        if points > 0:
            return 'background-color: #90EE90; color: black'  # 薄緑色
        elif points < 0:
            return 'background-color: #FFB6C6; color: black'  # 薄赤色
        return 'background-color: #F0F0F0; color: black'  # 灰色（0点）
    except:
        return "background-color: transparent; color: black"  # 数値でない場合
