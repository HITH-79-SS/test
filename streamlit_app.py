import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import math
import json

# ページ設定
st.set_page_config(
    page_title="日田市観光最適化ルートナビ",
    page_icon="🗾",
    layout="wide"
)

# CSSスタイル
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E8B57;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    .spot-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .route-info {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2E8B57;
    }
</style>
""", unsafe_allow_html=True)

class RouteOptimizer:
    """観光ルート最適化クラス"""
    
    def __init__(self, spots_df):
        self.spots_df = spots_df
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """ヒュベニの公式を使用して2点間の距離を計算"""
        # 度をラジアンに変換
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 平均緯度
        P = (lat1_rad + lat2_rad) / 2
        
        # 緯度・経度の差
        Dy = lat1_rad - lat2_rad
        Dx = lon1_rad - lon2_rad
        
        # 地球楕円体のパラメータ（WGS84）
        a = 6378137.0  # 長半径（m）
        b = 6356752.314245  # 短半径（m）
        e2 = (a**2 - b**2) / a**2  # 第一離心率の二乗
        
        # 子午線曲率半径
        M = a * (1 - e2) / math.pow(1 - e2 * math.sin(P)**2, 1.5)
        
        # 卯酉線曲率半径
        N = a / math.sqrt(1 - e2 * math.sin(P)**2)
        
        # ヒュベニの公式による距離計算
        distance = math.sqrt((Dy * M)**2 + (Dx * N * math.cos(P))**2)
        
        # メートルからキロメートルに変換
        return distance / 1000
    
    def calculate_time_decrease_rate_ranking(self, spots, current_time=0):
        """所要時間減少率ランキングを計算"""
        time_efficiency = {}
        
        for spot in spots:
            spot_data = self.spots_df[self.spots_df['スポット名'] == spot].iloc[0]
            efficiency = spot_data['おすすめ度'] / spot_data['最低所要時間']
            time_efficiency[spot] = efficiency
        
        sorted_spots = sorted(time_efficiency.items(), key=lambda x: x[1], reverse=True)
        
        ranking = {}
        for rank, (spot, _) in enumerate(sorted_spots, 1):
            ranking[spot] = rank
        
        return ranking
    
    def calculate_distance_ranking(self, current_spot, remaining_spots):
        """現在のスポットから他スポットまでの距離ランキングを計算"""
        if current_spot is None:
            return {spot: 1 for spot in remaining_spots}
        
        distances = {}
        current_spot_data = self.spots_df[self.spots_df['スポット名'] == current_spot].iloc[0]
        
        for spot in remaining_spots:
            spot_data = self.spots_df[self.spots_df['スポット名'] == spot].iloc[0]
            distance = self.calculate_distance(
                current_spot_data['緯度'], current_spot_data['経度'],
                spot_data['緯度'], spot_data['経度']
            )
            distances[spot] = distance
        
        sorted_spots = sorted(distances.items(), key=lambda x: x[1])
        
        ranking = {}
        for rank, (spot, _) in enumerate(sorted_spots, 1):
            ranking[spot] = rank
        
        return ranking
    
    def calculate_distance_ranking_from_location(self, lat, lon, remaining_spots):
        """指定位置から他スポットまでの距離ランキングを計算"""
        distances = {}
        
        for spot in remaining_spots:
            spot_data = self.spots_df[self.spots_df['スポット名'] == spot].iloc[0]
            distance = self.calculate_distance(
                lat, lon,
                spot_data['緯度'], spot_data['経度']
            )
            distances[spot] = distance
        
        sorted_spots = sorted(distances.items(), key=lambda x: x[1])
        
        ranking = {}
        for rank, (spot, _) in enumerate(sorted_spots, 1):
            ranking[spot] = rank
        
        return ranking
    
    def optimize_route(self, selected_spots, user_location=None):
        """最適化ルートを計算"""
        if len(selected_spots) <= 1:
            return selected_spots
        
        remaining_spots = selected_spots.copy()
        optimized_route = []
        current_spot = None
        
        # 最初のスポットを決定
        if user_location:
            distance_ranking = self.calculate_distance_ranking_from_location(
                user_location['lat'], user_location['lon'], remaining_spots
            )
            time_ranking = self.calculate_time_decrease_rate_ranking(remaining_spots)
            
            scores = {}
            for spot in remaining_spots:
                scores[spot] = distance_ranking[spot] + time_ranking[spot]
            
            first_spot = min(scores.items(), key=lambda x: x[1])[0]
            optimized_route.append(first_spot)
            remaining_spots.remove(first_spot)
            current_spot = first_spot
        else:
            best_spot = max(remaining_spots, key=lambda spot: 
                self.spots_df[self.spots_df['スポット名'] == spot]['おすすめ度'].iloc[0]
            )
            optimized_route.append(best_spot)
            remaining_spots.remove(best_spot)
            current_spot = best_spot
        
        # 残りのスポットを順次決定
        while remaining_spots:
            time_ranking = self.calculate_time_decrease_rate_ranking(remaining_spots)
            distance_ranking = self.calculate_distance_ranking(current_spot, remaining_spots)
            
            scores = {}
            for spot in remaining_spots:
                scores[spot] = time_ranking[spot] + distance_ranking[spot]
            
            next_spot = min(scores.items(), key=lambda x: x[1])[0]
            optimized_route.append(next_spot)
            remaining_spots.remove(next_spot)
            current_spot = next_spot
        
        return optimized_route

@st.cache_data
def load_tourism_data():
    """観光スポットデータを読み込む"""
    # デモデータ
    demo_data = {
        'スポット名': [
            '豆田町', '咸宜園跡', '日田祇園山鉾会館', '廣瀬資料館',
            '日田市豆田町伝統的建造物群保存地区', '小鹿田焼の里',
            '天領まちなみ資料館', '掛合の棚田', '高塚愛宕地蔵尊',
            '日田温泉', '三隈川', '大原大しだれ桜', '天瀬温泉',
            '杉乃井ホテル', '九重"夢"大吊橋', '慈恩の滝',
            '津江神社', '日田杉資料館', '薫長酒蔵', '木の花ガルテン'
        ],
        '緯度': [
            33.3225, 33.3219, 33.3228, 33.3215, 33.3220, 33.2845,
            33.3230, 33.2456, 33.3156, 33.3198, 33.3210, 33.2896,
            33.2345, 33.2789, 33.1245, 33.1567, 33.4567, 33.3189,
            33.3234, 33.3456
        ],
        '経度': [
            130.9425, 130.9438, 130.9420, 130.9445, 130.9430, 130.8923,
            130.9415, 130.8734, 130.9523, 130.9412, 130.9401, 130.8756,
            130.8234, 130.8456, 131.1234, 131.0987, 130.8765, 130.9387,
            130.9456, 130.9123
        ],
        '最低所要時間': [
            60, 45, 30, 40, 90, 120, 30, 45, 30, 180,
            40, 20, 120, 180, 60, 30, 45, 40, 45, 90
        ],
        'おすすめ度': [
            5, 4, 3, 4, 5, 5, 3, 4, 3, 4,
            4, 5, 4, 3, 5, 4, 3, 3, 4, 4
        ],
        '説明': [
            '江戸時代の町並みが残る歴史的な商家町。重要伝統的建造物群保存地区に指定されている。',
            '江戸後期の私塾跡。咸宜園は「日本最大の私塾」として知られ、全国から多くの門下生が学んだ。',
            '日田祇園祭で使用される豪華絢爛な山鉾を展示。祭りの歴史と文化を学べる。',
            '廣瀬淡窓と咸宜園の歴史を紹介する資料館。貴重な資料や文献が展示されている。',
            '江戸時代の面影を残す伝統的建造物群。国の重要伝統的建造物群保存地区に指定。',
            '約300年の伝統を持つ民陶の里。登り窯で焼かれる素朴で美しい陶器作りを見学できる。',
            '天領時代の日田の歴史と文化を紹介。代官所の歴史や当時の暮らしを学べる。',
            '美しい石積みの棚田群。四季折々の風景が楽しめる日本の原風景。',
            '商売繁盛・開運のご利益で知られる地蔵尊。多くの参拝者が訪れるパワースポット。',
            '歴史ある温泉街。三隈川沿いの風情ある景観とともに温泉を楽しめる。',
            '日田市を流れる清流。屋形船や鵜飼いなど川遊びが楽しめる。',
            '樹齢1000年を超える見事なしだれ桜。春には多くの花見客で賑わう。',
            '奥日田の温泉郷。自然豊かな環境で湯治を楽しめる静かな温泉地。',
            '由布院の老舗ホテル。温泉とグルメが楽しめるリゾート施設。',
            '高さ173mの大吊橋。九重連山の絶景が一望できる観光名所。',
            '落差83mの雄大な滝。マイナスイオンたっぷりの癒しスポット。',
            '由緒ある神社。地域の信仰の中心として親しまれている。',
            '日田杉の歴史と文化を紹介。林業の発展と技術を学べる施設。',
            '創業200年の老舗酒蔵。日本酒の製造工程を見学し試飲も楽しめる。',
            'ドイツ風の農業テーマパーク。ソーセージ作りやビール工場見学が人気。'
        ]
    }
    return pd.DataFrame(demo_data)

def get_user_location():
    """簡易的な位置情報取得（デモ用）"""
    if st.sidebar.button("📍 位置情報を取得（デモ）"):
        # 日田市中心部の座標
        demo_location = {
            'lat': 33.3220,
            'lon': 130.9430,
            'source': 'demo'
        }
        st.sidebar.success("位置情報を取得しました（デモ）")
        return demo_location
    return None

def create_map(spots_df, selected_spots=None, optimized_route=None, user_location=None):
    """地図を作成する"""
    center_lat = spots_df['緯度'].mean()
    center_lon = spots_df['経度'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    # ユーザーの現在位置を表示
    if user_location:
        folium.Marker(
            [user_location['lat'], user_location['lon']],
            popup="現在位置",
            icon=folium.Icon(color='red', icon='user', prefix='fa')
        ).add_to(m)
    
    # 選択されたスポットをハイライト
    for idx, row in spots_df.iterrows():
        color = 'green' if selected_spots and row['スポット名'] in selected_spots else 'blue'
        popup_text = f"""
        <b>{row['スポット名']}</b><br>
        所要時間: {row['最低所要時間']}分<br>
        おすすめ度: {'★' * row['おすすめ度']}<br>
        {row['説明'][:50]}...
        """
        
        folium.Marker(
            [row['緯度'], row['経度']],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(m)
    
    # 最適化ルートを表示
    if optimized_route and len(optimized_route) > 1:
        route_coords = []
        for i, spot_name in enumerate(optimized_route):
            spot_data = spots_df[spots_df['スポット名'] == spot_name].iloc[0]
            route_coords.append([spot_data['緯度'], spot_data['経度']])
            
            # ルート順序を表示
            folium.Marker(
                [spot_data['緯度'], spot_data['経度']],
                popup=f"順序: {i+1} - {spot_name}",
                icon=folium.DivIcon(
                    html=f'<div style="background-color: red; color: white; border-radius: 50%; width: 30px; height: 30px; text-align: center; line-height: 30px; font-weight: bold;">{i+1}</div>',
                    icon_size=(30, 30)
                )
            ).add_to(m)
        
        # ルートライン
        folium.PolyLine(
            route_coords,
            color='red',
            weight=3,
            opacity=0.8
        ).add_to(m)
    
    return m

def main():
    st.markdown('<h1 class="main-header">🗾 日田市観光最適化ルートナビ</h1>', unsafe_allow_html=True)
    
    # データ読み込み
    spots_df = load_tourism_data()
    
    # サイドバー
    st.sidebar.header("🎯 ルート設定")
    
    # 位置情報取得
    user_location = get_user_location()
    if user_location:
        st.session_state.user_location = user_location
    
    # スポット選択
    st.sidebar.subheader("観光スポット選択")
    selected_spots = st.sidebar.multiselect(
        "訪問したいスポットを選択してください（複数選択可）:",
        spots_df['スポット名'].tolist(),
        help="複数のスポットを選択すると最適ルートを計算します"
    )
    
    # メインコンテンツエリア
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗺️ 観光スポットマップ")
        
        # 最適化ルート計算
        optimized_route = None
        if len(selected_spots) > 1:
            optimizer = RouteOptimizer(spots_df)
            user_loc = st.session_state.get('user_location', None)
            optimized_route = optimizer.optimize_route(selected_spots, user_loc)
        
        # 地図表示
        user_location = st.session_state.get('user_location', None)
        map_obj = create_map(spots_df, selected_spots, optimized_route, user_location)
        map_data = st_folium(map_obj, width=800, height=500)
    
    with col2:
        st.subheader("📋 選択中のスポット")
        
        if not selected_spots:
            st.info("左側から観光スポットを選択してください")
        else:
            total_time = 0
            for spot in selected_spots:
                spot_data = spots_df[spots_df['スポット名'] == spot].iloc[0]
                total_time += spot_data['最低所要時間']
                
                st.markdown(f"""
                <div class="spot-card">
                    <h4>{spot}</h4>
                    <p><strong>所要時間:</strong> {spot_data['最低所要時間']}分</p>
                    <p><strong>おすすめ度:</strong> {'★' * spot_data['おすすめ度']}</p>
                    <p>{spot_data['説明'][:100]}...</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="route-info">
                <h4>📊 ルート情報</h4>
                <p><strong>選択スポット数:</strong> {len(selected_spots)}箇所</p>
                <p><strong>合計所要時間:</strong> 約{total_time}分</p>
            </div>
            """, unsafe_allow_html=True)
    
    # 最適化ルート表示
    if optimized_route and len(optimized_route) > 1:
        st.subheader("🛣️ 最適化ルート")
        
        route_info = []
        optimizer = RouteOptimizer(spots_df)
        total_distance = 0
        
        for i in range(len(optimized_route)):
            spot_name = optimized_route[i]
            spot_data = spots_df[spots_df['スポット名'] == spot_name].iloc[0]
            
            distance_to_next = 0
            if i < len(optimized_route) - 1:
                next_spot = spots_df[spots_df['スポット名'] == optimized_route[i+1]].iloc[0]
                distance_to_next = optimizer.calculate_distance(
                    spot_data['緯度'], spot_data['経度'],
                    next_spot['緯度'], next_spot['経度']
                )
                total_distance += distance_to_next
            
            route_info.append({
                '順序': i + 1,
                'スポット名': spot_name,
                '所要時間': f"{spot_data['最低所要時間']}分",
                '次スポットまでの距離': f"{distance_to_next:.2f}km" if distance_to_next > 0 else "-"
            })
        
        route_df = pd.DataFrame(route_info)
        st.dataframe(route_df, use_container_width=True)
        
        st.info(f"💡 総移動距離: 約{total_distance:.2f}km")
        
        # ナビゲーション機能
        st.subheader("🧭 ナビゲーション")
        if st.button("📱 ルートナビを開始"):
            st.success("ナビゲーションを開始します！各スポットを順番に訪問してください。")
            
            # Google Mapsリンク生成
            waypoints = []
            for spot in optimized_route:
                spot_data = spots_df[spots_df['スポット名'] == spot].iloc[0]
                waypoints.append(f"{spot_data['緯度']},{spot_data['経度']}")
            
            google_maps_url = f"https://www.google.com/maps/dir/{'/'.join(waypoints)}"
            st.markdown(f"[🗺️ Google Mapsで開く]({google_maps_url})")
    
    # スポット詳細情報
    st.subheader("📍 全観光スポット一覧")
    
    # フィルタリング機能
    col1, col2 = st.columns(2)
    with col1:
        min_recommend = st.slider("最低おすすめ度", 1, 5, 1)
    with col2:
        max_time = st.slider("最大所要時間（分）", 30, 300, 300)
    
    filtered_df = spots_df[
        (spots_df['おすすめ度'] >= min_recommend) & 
        (spots_df['最低所要時間'] <= max_time)
    ]
    
    st.dataframe(
        filtered_df[['スポット名', '最低所要時間', 'おすすめ度', '説明']],
        use_container_width=True
    )

if __name__ == "__main__":
    main()