import streamlit as st
import requests
import time

# 페이지 설정
st.set_page_config(page_title="Verkada Horn Helix Controller", layout="wide")

# --------------------------------------------------------
# 📱 [수정] 아이패드/태블릿 터치 조작을 위한 초대형 버튼 CSS 스타일
# --------------------------------------------------------
st.markdown("""
    <style>
        /* 모든 버튼의 높이, 글자 크기를 아이패드 터치에 최적화 */
        div.stButton > button:first-child {
            height: 6.5rem !important;      /* 터치 영역을 대폭 확대 (기존 4.5rem -> 6.5rem) */
            font-size: 32px !important;     /* 멀리서도 잘 보이고 누르기 쉬운 폰트 크기 */
            font-weight: bold !important;   /* 글자 두껍게 */
            border-radius: 16px !important; /* 모서리를 더 둥글고 직관적이게 변경 */
            margin-bottom: 15px !important; /* 버튼 간 오터치(오클릭) 방지를 위한 충분한 여백 */
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.15) !important; /* 터치 대상이 명확히 보이도록 그림자 추가 */
            transition: all 0.15s ease;
        }
        
        /* 버튼을 누르거나 마우스를 올렸을 때 액션 효과 */
        div.stButton > button:first-child:active {
            transform: scale(0.98); /* 터치 시 눌리는 피드백 제공 */
        }
        div.stButton > button:first-child:hover {
            border-color: #ff4b4b !important;
            background-color: rgba(255, 75, 75, 0.05) !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📯 Verkada Horn Helix Controller")
st.caption("아이패드 터치 UI 최적화 및 Device Name 설정이 적용된 버전입니다.")

# --------------------------------------------------------
# 1. 사이드바 설정 (API 및 카메라 정보 입력)
# --------------------------------------------------------
st.sidebar.header("⚙️ 기본 설정 (Configuration)")

api_key = st.sidebar.text_input(
    "API Key", 
    type="password", 
    help="Verkada Command > Settings > API Keys 에서 생성한 API Key를 입력하세요."
)

org_id = st.sidebar.text_input(
    "Organization ID (org_id)",
    value="",
    placeholder="조직 ID(UUID)를 입력하세요",
    help="URL 쿼리 스트링(?org_id=...)에 들어갈 조직 ID입니다."
)

camera_id = st.sidebar.text_input(
    "Camera ID", 
    value="", 
    placeholder="카메라 ID(UUID)를 입력하세요",
    help="Helix 메시지와 연동할 Camera ID를 입력하세요."
)

event_type_uid = st.sidebar.text_input(
    "Event Type UID (event_type_uid)",
    value="",
    placeholder="이벤트 타입 UID(UUID)를 입력하세요",
    help="웹 화면에서 정의한 event_type_uid 정보입니다."
)

st.sidebar.markdown("---")

# 기본값: Horn 1개, 버튼 3개 유지
num_horns = st.sidebar.number_input("Horn 개수 (개별 Device)", min_value=1, max_value=20, value=1)
num_buttons = st.sidebar.number_input("Horn당 메시지 버튼 개수", min_value=1, max_value=10, value=3)

# --------------------------------------------------------
# 2. 메인 화면: [수정] 각 Horn의 Device Name 입력 칸 생성
# --------------------------------------------------------
st.subheader("🆔 Horn별 Device Name 설정")
st.write("설정한 Horn 개수만큼 Device Name을 입력해주세요.")

horn_names = []
id_cols = st.columns(min(num_horns, 4)) 

for i in range(num_horns):
    col_idx = i % 4
    with id_cols[col_idx]:
        # [수정] Device ID -> Device Name 명칭 변경
        h_name = st.text_input(
            f"Horn {i+1} Device Name", 
            value=f"HORN_NAME_{i+1}", 
            key=f"horn_input_{i}"
        )
        horn_names.append(h_name)

st.markdown("---")

# --------------------------------------------------------
# 3. 핵심 로직: 1단계 단기 토큰 발급 & 2단계 이벤트 전송
# --------------------------------------------------------

def get_short_lived_token(api_key):
    url = "https://api.verkada.com/token"
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json"
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        res_data = response.json()
        return res_data.get("token") or res_data.get("api_token")
    else:
        raise Exception(f"단기 토큰 생성 실패 (상태 코드: {response.status_code}) - {response.text}")


def send_video_tagging_event(token, org_id, cam_id, event_uid, dev_name, msg_type):
    url = f"https://api.verkada.com/cameras/v1/video_tagging/event?org_id={org_id}"
    
    headers = {
        "content-type": "application/json",
        "x-verkada-auth": token,
        "Authorization": f"Bearer {token}"
    }
    
    current_time_ms = int(time.time() * 1000)
    
    # [참고] API 스펙에 맞추어 키값은 'Device_ID'로 유지하되, 입력받은 dev_name 값을 매핑합니다.
    payload = {
        "attributes": {
            "Camera_ID": cam_id,
            "Device_ID": dev_name, 
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
st.subheader("🚀 Horn 제어 패널 (태블릿 터치 스크린용)")
st.info("아이패드 환경에서 검지나 엄지손가락으로 쉽게 누를 수 있도록 설계되었습니다.")

for i in range(num_horns):
    current_horn_name = horn_names[i]
    # [수정] UI 타이틀 명칭 변경
    st.write(f"### 📢 Horn {i+1} (Name: `{current_horn_name}`)")
    
    btn_cols = st.columns(num_buttons)
    for j in range(num_buttons):
        message_id = j + 1
        
        with btn_cols[j]:
            btn_label = f"Msg {message_id}"
            
            if st.button(btn_label, key=f"btn_{i}_{message_id}", use_container_width=True):
                if not api_key:
                    st.warning("⚠️ 사이드바에 API Key를 먼저 입력해주세요.")
                elif not org_id:
                    st.warning("⚠️ 사이드바에 Organization ID를 입력해주세요.")
                elif not camera_id:
                    st.warning("⚠️ 사이드바에 Camera ID를 입력해주세요.")
                elif not event_type_uid:
                    st.warning("⚠️ 사이드바에 Event Type UID를 입력해주세요.")
                else:
                    with st.spinner("Verkada 보안 인증 및 이벤트 전송 중..."):
                        try:
                            short_token = get_short_lived_token(api_key)
                            
                            response, sent_payload = send_video_tagging_event(
                                token=short_token,
                                org_id=org_id,
                                cam_id=camera_id,
                                event_uid=event_type_uid,
                                dev_name=current_horn_name, # Device Name 전달
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
