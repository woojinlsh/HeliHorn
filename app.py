import streamlit as st
import requests
import time

# 페이지 설정
st.set_page_config(page_title="Verkada Horn Helix Controller", layout="wide")

st.title("📯 Verkada Horn Helix Controller")
st.caption("Verkada API v2 단기 토큰 자동 발급 메커니즘이 내장된 Horn 우회 제어 도구입니다.")

# --------------------------------------------------------
# 1. 사이드바 설정 (API, 웹 입력 옵션값 정의)
# --------------------------------------------------------
st.sidebar.header("⚙️ 기본 설정 (Configuration)")

# [수정] Command 콘솔에서 복사한 최상위 API Key를 입력받습니다.
top_level_api_key = st.sidebar.text_input(
    "Top-level API Key", 
    type="password", 
    help="Verkada Command > Settings > API Keys 에서 생성한 최상위 API Key를 입력하세요."
)

org_id = st.sidebar.text_input(
    "Organization ID (org_id)",
    value="61b8824a-14bd-4642-9165-1e7d7b173167",
    help="URL 쿼리 스트링(?org_id=...)에 들어갈 조직 ID입니다."
)

camera_id = st.sidebar.text_input(
    "Camera ID", 
    value="유효한_카메라_ID_입력", 
    help="Helix 메시지와 연동할 Camera ID를 입력하세요."
)

event_type_uid = st.sidebar.text_input(
    "Event Type UID (event_type_uid)",
    value="9232f31e-a123-4da5-ba5b-7a77627fa62e",
    help="웹 화면에서 동적으로 변경할 수 있는 event_type_uid 정보입니다."
)

st.sidebar.markdown("---")

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
# 3. 핵심 로직: 1단계 단기 토큰 발급 & 2단계 이벤트 전송
# --------------------------------------------------------

# [추가] 최상위 API Key로 30분짜리 단기 토큰을 받아오는 함수
def get_short_lived_token(api_key):
    url = "https://api.verkada.com/token"
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json"
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        res_data = response.json()
        # API 응답 규격에 맞는 토큰 문자열 반환
        return res_data.get("token") or res_data.get("api_token")
    else:
        raise Exception(f"단기 토큰 생성 실패 (상태 코드: {response.status_code}) - {response.text}")


# 발급받은 단기 토큰을 사용하여 최종 이벤트를 전송하는 함수
def send_video_tagging_event(token, org_id, cam_id, event_uid, dev_id, msg_type):
    url = f"https://api.verkada.com/cameras/v1/video_tagging/event?org_id={org_id}"
    
    # [수정] 시스템 요구 규격에 맞춰 x-verkada-auth와 Bearer 토큰을 모두 적용하여 안정성 보장
    headers = {
        "content-type": "application/json",
        "x-verkada-auth": token,
        "Authorization": f"Bearer {token}"
    }
    
    current_time_ms = int(time.time() * 1000)
    
    payload = {
        "attributes": {
            "Camera_ID": cam_id,
            "Device_ID": dev_id,
            "Message_Type": str(msg_type)
        },
        "event_type_uid": event_uid,
        "camera_id": cam_id,
        "time_ms": current_time_ms
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response, payload

# --------------------------------------------------------
# 4. 메인 화면: 동적 제어 버튼 생성 및 이벤트 바인딩
# --------------------------------------------------------
st.subheader("🚀 Horn 제어 패널")
st.info("버튼을 누르면 실시간으로 단기 토큰을 발급받아 무인증 에러(401)를 우회하고 메시지를 전송합니다.")

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
                elif not camera_id or camera_id == "유효한_카메라_ID_입력":
                    st.warning("⚠️ 유효한 Camera ID를 입력해주세요.")
                else:
                    with st.spinner("Verkada 보안 인증 및 이벤트 전송 중..."):
                        try:
                            # 1단계: 실시간 단기 토큰 가져오기 (자동화)
                            short_token = get_short_lived_token(top_level_api_key)
                            
                            # 2단계: 가져온 토큰으로 최종 API 전송
                            response, sent_payload = send_video_tagging_event(
                                token=short_token,
                                org_id=org_id,
                                cam_id=camera_id,
                                event_uid=event_type_uid,
                                dev_id=current_horn_id,
                                msg_type=message_id
                            )
                            
                            if response.status_code in [200, 201]:
                                st.success(f"✅ [성공] Horn {i+1} -> Message ID: {message_id} 전송 완료!")
                                with st.expander("실제 전송된 데이터(Payload) 확인"):
                                    st.json(sent_payload)
                            else:
                                st.error(f"❌ [API 오류] 상태 코드: {response.status_code}")
                                st.json(response.json() if response.text else response.text)
                                
                        except Exception as e:
                            st.error(f"💥 [시스템 오류] {e}")
                            
    st.markdown("---")
