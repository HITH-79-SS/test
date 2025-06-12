import math
import pandas as pd
import numpy as np

class RouteOptimizer:
    """観光ルート最適化クラス"""
    
    def __init__(self, spots_df):
        """
        初期化
        Args:
            spots_df: 観光スポットのDataFrame
        """
        self.spots_df = spots_df
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        ヒュベニの公式を使用して2点間の距離を計算
        Args:
            lat1, lon1: 地点1の緯度・経度
            lat2, lon2: 地点2の緯度・経度
        Returns:
            距離（km）
        """
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
    
    def calculate_distance_matrix(self, spots):
        """
        選択されたスポット間の距離行列を計算
        Args:
            spots: スポット名のリスト
        Returns:
            距離行列（DataFrame）
        """
        n = len(spots)
        distance_matrix = np.zeros((n, n))
        
        for i, spot1 in enumerate(spots):
            for j, spot2 in enumerate(spots):
                if i != j:
                    spot1_data = self.spots_df[self.spots_df['スポット名'] == spot1].iloc[0]
                    spot2_data = self.spots_df[self.spots_df['スポット名'] == spot2].iloc[0]
                    
                    distance = self.calculate_distance(
                        spot1_data['緯度'], spot1_data['経度'],
                        spot2_data['緯度'], spot2_data['経度']
                    )
                    distance_matrix[i][j] = distance
        
        return pd.DataFrame(distance_matrix, index=spots, columns=spots)
    
    def calculate_time_decrease_rate_ranking(self, spots, current_time=0):
        """
        所要時間減少率ランキングを計算
        Args:
            spots: 残りのスポット名のリスト
            current_time: 現在の累計時間
        Returns:
            ランキング辞書（スポット名: ランク）
        """
        time_efficiency = {}
        
        for spot in spots:
            spot_data = self.spots_df[self.spots_df['スポット名'] == spot].iloc[0]
            # 所要時間とおすすめ度を考慮した効率スコア
            efficiency = spot_data['おすすめ度'] / spot_data['最低所要時間']
            time_efficiency[spot] = efficiency
        
        # 効率の高い順にソート（効率が高い=ランクが低い）
        sorted_spots = sorted(time_efficiency.items(), key=lambda x: x[1], reverse=True)
        
        ranking = {}
        for rank, (spot, _) in enumerate(sorted_spots, 1):
            ranking[spot] = rank
        
        return ranking
    
    def calculate_distance_ranking(self, current_spot, remaining_spots):
        """
        現在のスポットから他スポットまでの距離ランキングを計算
        Args:
            current_spot: 現在のスポット名
            remaining_spots: 残りのスポット名のリスト
        Returns:
            距離ランキング辞書（スポット名: ランク）
        """
        if current_spot is None:
            # 開始地点が不明な場合は均等なランクを返す
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
        
        # 距離の近い順にソート（距離が近い=ランクが低い）
        sorted_spots = sorted(distances.items(), key=lambda x: x[1])
        
        ranking = {}
        for rank, (spot, _) in enumerate(sorted_spots, 1):
            ranking[spot] = rank
        
        return ranking
    
    def calculate_distance_ranking_from_location(self, lat, lon, remaining_spots):
        """
        指定位置から他スポットまでの距離ランキングを計算
        Args:
            lat, lon: 現在位置の緯度・経度
            remaining_spots: 残りのスポット名のリスト
        Returns:
            距離ランキング辞書（スポット名: ランク）
        """
        distances = {}
        
        for spot in remaining_spots:
            spot_data = self.spots_df[self.spots_df['スポット名'] == spot].iloc[0]
            distance = self.calculate_distance(
                lat, lon,
                spot_data['緯度'], spot_data['経度']
            )
            distances[spot] = distance
        
        # 距離の近い順にソート
        sorted_spots = sorted(distances.items(), key=lambda x: x[1])
        
        ranking = {}
        for rank, (spot, _) in enumerate(sorted_spots, 1):
            ranking[spot] = rank
        
        return ranking
    
    def optimize_route(self, selected_spots, user_location=None):
        """
        最適化ルートを計算
        Args:
            selected_spots: 選択されたスポット名のリスト
            user_location: ユーザーの現在位置（辞書: {'lat': 緯度, 'lon': 経度}）
        Returns:
            最適化されたルート（スポット名のリスト）
        """
        if len(selected_spots) <= 1:
            return selected_spots
        
        remaining_spots = selected_spots.copy()
        optimized_route = []
        current_spot = None
        
        # 最初のスポットを決定
        if user_location:
            # ユーザー位置から最も近いスポットを最初に選択
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
            # ユーザー位置が不明な場合は、おすすめ度が最も高いスポットを選択
            best_spot = max(remaining_spots, key=lambda spot: 
                self.spots_df[self.spots_df['スポット名'] == spot]['おすすめ度'].iloc[0]
            )
            optimized_route.append(best_spot)
            remaining_spots.remove(best_spot)
            current_spot = best_spot
        
        # 残りのスポットを順次決定
        while remaining_spots:
            # 所要時間減少率ランキング
            time_ranking = self.calculate_time_decrease_rate_ranking(remaining_spots)
            
            # 距離ランキング
            distance_ranking = self.calculate_distance_ranking(current_spot, remaining_spots)
            
            # 合計スコア計算（Si = RW,i + RD,i）
            scores = {}
            for spot in remaining_spots:
                scores[spot] = time_ranking[spot] + distance_ranking[spot]
            
            # スコアが最小のスポットを選択
            next_spot = min(scores.items(), key=lambda x: x[1])[0]
            optimized_route.append(next_spot)
            remaining_spots.remove(next_spot)
            current_spot = next_spot
        
        return optimized_route
    
    def calculate_route_stats(self, route):
        """
        ルートの統計情報を計算
        Args:
            route: スポット名のリスト
        Returns:
            統計情報の辞書
        """
        if not route:
            return {}
        
        total_time = 0
        total_distance = 0
        total_recommend_score = 0
        
        for i, spot in enumerate(route):
            spot_data = self.spots_df[self.spots_df['スポット名'] == spot].iloc[0]
            total_time += spot_data['最低所要時間']
            total_recommend_score += spot_data['おすすめ度']
            
            # 次のスポットまでの距離
            if i < len(route) - 1:
                next_spot = route[i + 1]
                next_spot_data = self.spots_df[self.spots_df['スポット名'] == next_spot].iloc[0]
                distance = self.calculate_distance(
                    spot_data['緯度'], spot_data['経度'],
                    next_spot_data['緯度'], next_spot_data['経度']
                )
                total_distance += distance
        
        return {
            'total_spots': len(route),
            'total_time_minutes': total_time,
            'total_distance_km': round(total_distance, 2),
            'average_recommend_score': round(total_recommend_score / len(route), 1),
            'efficiency_score': round(total_recommend_score / (total_time / 60), 2)  # おすすめ度/時間
        }