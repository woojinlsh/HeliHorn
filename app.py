import streamlit as st
import requests
import time  # 실시간 time_ms 계산을 위해 추가

# 페이지 설정
st.set_page_config(page_title="Verkada Horn Helix Controller", layout="wide")

st.title("📯 Verkada Horn Helix Controller")
st.caption("제공해주신 Video Tagging Event API 규격에 맞춘 Horn 우회 제어 도구입니다.")

# --------------------------------------------------------
# 1. 사이드바 설정 (API, 웹 입력 옵션값 정의)
# --------------------------------------------------------
st.sidebar.header("⚙️ 기본 설정 (Configuration)")

# 헤더에 들어갈 API Key 입력
api_key = st.sidebar.text_input(
    "Verkada API Key (x-verkada-auth)", 
    type="password", 
    help="curl의 x-verkada-auth 헤더에 들어갈 API Key를 입력하세요."
)

# URL 쿼리 파라미터에 들어갈 org_id 입력 (기본값 제공)
org_id = st.sidebar.text_input(
    "Organization ID (org_id)",
    value="61b8824a-14bd-4642-9165-1e7d7b173167",
    help="URL 쿼리 스트링(?org_id=...)에 들어갈 조직 ID입니다."
)

# attributes 내부 및 외부 구조에 공통으로 쓰일 Camera ID
camera_id = st.sidebar.text_input(
    "Camera ID", 
    value="유효한_카메라_ID_입력", 
    help="Helix 메시지와 연동할 Camera ID를 입력하세요."
)

# 요구하신 "웹에서 받아야 하는 event uid 정보" 입력 칸
event_type_uid = st.sidebar.text_input(
    "Event Type UID (event_type_uid)",
    value="9232f31e-a123-4da5-ba5b-7a77627fa62e",
    help="웹 화면에서 동적으로 변경할 수 있는 event_type_uid 정보입니다."
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
# 3. 핵심 로직: Verkada Video Tagging API 전송 함수
# --------------------------------------------------------
def send_video_tagging_event(api_key, org_id, cam_id, event_uid, dev_id, msg_type):
    # 요청하신 URL 양식에 맞춰 구성
    url = f"https://api.verkada.com/cameras/v1/video_tagging/event?org_id={org_id}"
    
    headers = {
        "content-type": "application/json",
        "x-verkada-auth": api_key
    }
    
    # 버튼 클릭 시점의 현재 시간을 밀리초(Epoch ms)로 자동 계산
    current_time_ms = int(time.time() * 1000)
    
    # 제공해주신 json 데이터 구조와 정확히 일치하게 매핑
    payload = {
        "attributes": {
            "Camera_ID": cam_id,
            "Device_ID": dev_id,
            "Message_Type": str(msg_type) # 1, 2, 3, 4 형태로 변환
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
st.info("버튼을 누르면 설정된 웹 옵션값과 현재 시간(time_ms)을 계산하여 Verkada API로 이벤트를 쏩니다.")

for i in range(num_horns):
    current_horn_id = horn_ids[i]
    st.write(f"### 📢 Horn {i+1} (ID: `{current_horn_id}`)")
    
    btn_cols = st.columns(num_buttons)
    for j in range(num_buttons):
        message_id = j + 1
        
        with btn_cols[j]:
            btn_label = f"Msg {message_id}"
            
            if st.button(btn_label, key=f"btn_{i}_{message_id}", use_container_width=True):
                if not api_key:
                    st.warning("⚠️ 사이드바에 API Key(x-verkada-auth)를 먼저 입력해주세요.")
                elif not camera_id or camera_id == "유효한_카메라_ID_입력":
                    st.warning("⚠️ 유효한 Camera ID를 입력해주세요.")
                else:
                    with st.spinner("Verkada API 전송 중..."):
                        try:
                            response, sent_payload = send_video_tagging_event(
                                api_key=api_key,
                                org_id=org_id,
                                cam_id=camera_id,
                                event_uid=event_type_uid,
                                dev_id=current_horn_id,
                                msg_type=message_id
                            )
                            
                            if response.status_code in [200, 201]:
                                st.success(f"✅ [성공] Horn {i+1} -> Message ID: {message_id} 전송 완료!")
                                # 디버깅용으로 실제 날아간 Payload 데이터를 화면에 투명하게 보여줍니다.
                                with st.expander("실제 전송된 데이터(Payload) 확인"):
                                    st.json(sent_payload)
                            else:
                                st.error(f"❌ [API 오류] 상태 코드: {response.status_code}")
                                st.text(response.text)
                                
                        except Exception as e:
                            st.error(f"💥 [시스템 오류] {e}")
                            
    st.markdown("---")
