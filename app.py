import streamlit as st
import requests

# 페이지 설정
st.set_page_config(page_title="Verkada Horn Helix Controller", layout="wide")

st.title("📯 Verkada Horn Helix Controller")
st.caption("Verkada API v2 보안 규격(단기 토큰 발급 후 Bearer 인증)을 준수하는 Horn 우회 제어 도구입니다.")

# --------------------------------------------------------
# 1. 사이드바 설정 (API 및 카메라 정보 입력)
# --------------------------------------------------------
st.sidebar.header("⚙️ 기본 설정 (Configuration)")

# Verkada API 기본 Base URL (ภูมิ역에 따라 다를 수 있으므로 입력 가능하게 설정)
api_base_url = st.sidebar.text_input(
    "Verkada API Base URL", 
    value="https://api.verkada.com",
    help="Verkada API의 기본 주소입니다. 일반적으로 https://api.verkada.com 입니다."
)

# 콘솔에서 발급받은 Top-level API Key
top_level_api_key = st.sidebar.text_input(
    "Top-level API Key", 
    type="password", 
    help="Verkada Command > Settings > API Keys 에서 생성한 최상위 API Key를 입력하세요."
)

camera_id = st.sidebar.text_input(
    "Camera ID", 
    value="유효한_카메라_ID_입력", 
    help="Helix 메시지와 연동할 Camera ID를 입력하세요."
)

st.sidebar.markdown("---")

# 동적 버튼 생성을 위한 개수 정의
num_horns = st.sidebar.number_input("Horn 개수 (개별 Device)", min_value=1, max_value=20, value=2)
num_buttons = st.sidebar.number_input("Horn당 메시지 버튼 개수", min_value=1, max_value=10, value=4)

# --------------------------------------------------------
# 2. 메인 화면: 각 Horn의 Device ID 입력 칸 생성
# --------------------------------------------------------
st.subheader("🆔 Horn별 Device ID 설정")
st.write("설정한 Horn 개수만큼 Device ID를 입력해주세요.")

horn_ids = []
id_cols = st.columns(min(num_horns, 4)) 

for i in range(num_horns):
    col_idx = i % 4
    with id_cols[col_idx]:
        h_id = st.text_input(
            f"Horn {i+1} Device ID", 
            value=f"HORN_DEV_{i+1}", 
            key=f"horn_input_{i}"
        )
        horn_ids.append(h_id)

st.markdown("---")

# --------------------------------------------------------
# 3. 핵심 로직: Verkada 인증 및 Helix 메시지 발송 함수
# --------------------------------------------------------

# 1단계: Top-level API Key로 30분짜리 short-lived API Token 가져오기
def get_short_lived_token(base_url, api_key):
    token_url = f"{base_url.rstrip('/')}/token"
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json"
    }
    
    response = requests.post(token_url, headers=headers)
    if response.status_code == 200:
        res_data = response.json()
        # 문서 구조에 따라 'token' 또는 'api_token' 키값을 추출합니다.
        return res_data.get("token") or res_data.get("api_token")
    else:
        raise Exception(f"토큰 발급 실패 (Status: {response.status_code}) - {response.text}")

# 2단계: 발급받은 Bearer Token을 사용해 Helix 메시지 발송하기
def send_helix_message(base_url, token, cam_id, dev_id, msg_type):
    # Helix 알림 엔드포인트 설정 (일반적인 웹훅/알림 경로 기준)
    helix_url = f"{base_url.rstrip('/')}/v1/helix/notification" 
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "Camera_ID": cam_id,
        "Device_ID": dev_id,
        "Message_Type": str(msg_type) # 요청하신 1, 2, 3, 4 형태
    }
    
    response = requests.post(helix_url, json=payload, headers=headers)
    return response

# --------------------------------------------------------
# 4. 메인 화면: 동적 제어 버튼 생성 및 이벤트 바인딩
# --------------------------------------------------------
st.subheader("🚀 Horn 제어 패널")
st.info("버튼을 누르면 실시간으로 API Token을 갱신/인증한 뒤 Verkada Command로 Helix 메시지를 보냅니다.")

for i in range(num_horns):
    current_horn_id = horn_ids[i]
    st.write(f"### 📢 Horn {i+1} (ID: `{current_horn_id}`)")
    
    btn_cols = st.columns(num_buttons)
    for j in range(num_buttons):
        message_id = j + 1
        
        with btn_cols[j]:
            btn_label = f"Msg {message_id}"
            
            if st.button(btn_label, key=f"btn_{i}_{message_id}", use_container_width=True):
                if not top_level_api_key:
                    st.warning("⚠️ 사이드바에 Top-level API Key를 먼저 입력해주세요.")
                else:
                    with st.spinner("Verkada 인증 및 메시지 전송 중..."):
                        try:
                            # 1단계 인증 진행
                            api_token = get_short_lived_token(api_base_url, top_level_api_key)
                            
                            # 2단계 메시지 전송 진행
                            response = send_helix_message(
                                base_url=api_base_url,
                                token=api_token,
                                cam_id=camera_id,
                                dev_id=current_horn_id,
                                msg_type=message_id
                            )
                            
                            if response.status_code in [200, 201]:
                                st.success(f"✅ [성공] {current_horn_id} -> Message ID: {msg_type} 발송 완료!")
                            else:
                                st.error(f"❌ [API 오류] 상태 코드: {response.status_code} | {response.text}")
                                
                        except Exception as e:
                            st.error(f"💥 [실패] {e}")
                            
    st.markdown("---")
