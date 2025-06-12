import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import math
from route_optimizer import RouteOptimizer
from geolocation import get_user_location
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

@st.cache_data
def load_tourism_data():
    """観光スポットデータを読み込む"""
    try:
        # Excelファイルから観光スポットデータを読み込み
        df = pd.read_excel('hita_tourism_spots.xlsx')
        return df
    except FileNotFoundError:
        # デモデータを返す
        demo_data = {
            'スポット名': [
                '豆田町', '咸宜園跡', '日田祇園山鉾会館', '廣瀬資料館',
                '日田市豆田町伝統的建造物群保存地区', '小鹿田焼の里',
                '天領まちなみ資料館', '掛合の棚田', '高塚愛宕地蔵尊',
                '日田温泉'
            ],
            '緯度': [
                33.3225, 33.3219, 33.3228, 33.3215,
                33.3220, 33.2845, 33.3230, 33.2456,
                33.3156, 33.3198
            ],
            '経度': [
                130.9425, 130.9438, 130.9420, 130.9445,
                130.9430, 130.8923, 130.9415, 130.8734,
                130.9523, 130.9412
            ],
            '最低所要時間': [60, 45, 30, 40, 90, 120, 30, 45, 30, 180],
            'おすすめ度': [5, 4, 3, 4, 5, 5, 3, 4, 3, 4],
            '説明': [
                '江戸時代の町並みが残る歴史的な商家町',
                '日本最大の私塾跡、教育の聖地',
                '日田祇園祭の山鉾を展示する資料館',
                '日田の歴史と文化を紹介する資料館',
                '重要伝統的建造物群保存地区',
                '伝統的な陶器作りの里',
                '天領時代の歴史を学べる資料館',
                '美しい棚田の風景が楽しめるスポット',
                '商売繁盛・開運のご利益で有名な地蔵尊',
                '歴史ある温泉街でリラックス'
            ]
        }
        return pd.DataFrame(demo_data)

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
        {row['説明']}
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
    if st.sidebar.button("📍 現在位置を取得"):
        user_location = get_user_location()
        if user_location:
            st.sidebar.success(f"位置取得成功！")
            st.session_state.user_location = user_location
        else:
            st.sidebar.error("位置情報の取得に失敗しました")
    
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
                    <p>{spot_data['説明']}</p>
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