import streamlit as st
import streamlit.components.v1 as components

def get_user_location():
    """
    JavaScriptを使用してユーザーの位置情報を取得
    Returns:
        位置情報の辞書 {'lat': 緯度, 'lon': 経度} または None
    """
    
    # JavaScript コードで位置情報を取得
    location_component = """
    <script>
    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const location = {
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    };
                    
                    // Streamlitに結果を送信
                    window.parent.postMessage({
                        type: 'streamlit:location',
                        data: location
                    }, '*');
                    
                    document.getElementById('status').innerHTML = 
                        `位置情報取得成功！<br>緯度: ${location.lat.toFixed(6)}<br>経度: ${location.lon.toFixed(6)}`;
                },
                function(error) {
                    let errorMsg = '';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            errorMsg = "位置情報の取得が拒否されました。ブラウザの設定で位置情報を許可してください。";
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMsg = "位置情報が利用できません。";
                            break;
                        case error.TIMEOUT:
                            errorMsg = "位置情報の取得がタイムアウトしました。";
                            break;
                        default:
                            errorMsg = "位置情報の取得中にエラーが発生しました。";
                            break;
                    }
                    document.getElementById('status').innerHTML = errorMsg;
                    
                    window.parent.postMessage({
                        type: 'streamlit:location',
                        data: null,
                        error: errorMsg
                    }, '*');
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 60000
                }
            );
        } else {
            const errorMsg = "このブラウザでは位置情報がサポートされていません。";
            document.getElementById('status').innerHTML = errorMsg;
            window.parent.postMessage({
                type: 'streamlit:location',
                data: null,
                error: errorMsg
            }, '*');
        }
    }
    
    // ページロード時に自動実行
    window.onload = function() {
        document.getElementById('status').innerHTML = "位置情報を取得中...";
        getLocation();
    }
    </script>
    
    <style>
    .location-container {
        padding: 20px;
        background-color: #f0f2f6;
        border-radius: 10px;
        text-align: center;
        font-family: Arial, sans-serif;
    }
    .status {
        margin-top: 10px;
        padding: 10px;
        border-radius: 5px;
        background-color: white;
    }
    .retry-button {
        margin-top: 10px;
        padding: 8px 16px;
        background-color: #ff4b4b;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    .retry-button:hover {
        background-color: #ff6b6b;
    }
    </style>
    
    <div class="location-container">
        <h3>📍 位置情報取得</h3>
        <div id="status" class="status">位置情報を取得中...</div>
        <button class="retry-button" onclick="getLocation()">再取得</button>
    </div>
    """
    
    # Streamlitでコンポーネントを表示
    result = components.html(location_component, height=200)
    
    # セッション状態から位置情報を取得
    if 'location_data' in st.session_state:
        return st.session_state.location_data
    
    return None

def create_location_js_component():
    """
    位置情報取得用のJavaScriptコンポーネントを作成
    """
    return """
    <script>
    function requestLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const locationData = {
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        timestamp: Date.now()
                    };
                    
                    // LocalStorageに保存（Streamlitでは使用不可のため、代替手段）
                    sessionStorage.setItem('user_location', JSON.stringify(locationData));
                    
                    // 成功メッセージを表示
                    document.getElementById('location-status').innerHTML = 
                        `<div style="color: green;">✅ 位置情報取得成功！<br>緯度: ${locationData.lat.toFixed(6)}<br>経度: ${locationData.lon.toFixed(6)}</div>`;
                },
                function(error) {
                    let errorMessage = '';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            errorMessage = "❌ 位置情報の取得が拒否されました。";
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMessage = "❌ 位置情報が利用できません。";
                            break;
                        case error.TIMEOUT:
                            errorMessage = "❌ 位置情報の取得がタイムアウトしました。";
                            break;
                        default:
                            errorMessage = "❌ 位置情報の取得に失敗しました。";
                            break;
                    }
                    document.getElementById('location-status').innerHTML = 
                        `<div style="color: red;">${errorMessage}</div>`;
                },
                {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 300000
                }
            );
        } else {
            document.getElementById('location-status').innerHTML = 
                '<div style="color: red;">❌ このブラウザは位置情報をサポートしていません。</div>';
        }
    }
    
    function getStoredLocation() {
        const stored = sessionStorage.getItem('user_location');
        if (stored) {
            const locationData = JSON.parse(stored);
            const age = Date.now() - locationData.timestamp;
            // 5分以内のデータなら使用
            if (age < 300000) {
                return locationData;
            }
        }
        return null;
    }
    </script>
    
    <div style="padding: 15px; background-color: #f8f9fa; border-radius: 8px; margin: 10px 0;">
        <button onclick="requestLocation()" style="
            background-color: #007bff; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer;
            font-size: 16px;
        ">📍 現在位置を取得</button>
        <div id="location-status" style="margin-top: 10px; font-size: 14px;"></div>
    </div>
    """

def get_location_from_browser():
    """
    ブラウザから位置情報を取得（簡易版）
    """
    # デモ用：日田市周辺の座標を返す
    # 実際の実装では、より高度な位置情報取得機能が必要
    demo_location = {
        'lat': 33.3220,  # 日田市豆田町周辺
        'lon': 130.9430,
        'accuracy': 100,
        'source': 'demo'
    }
    
    return demo_location