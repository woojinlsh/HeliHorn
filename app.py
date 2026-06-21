import streamlit as st
import requests
import time

# 페이지 설정
st.set_page_config(page_title="Verkada Horn Helix Controller", layout="wide")

# --------------------------------------------------------
# 🌐 다국어 텍스트 사전 정의 (English & Korean Dictionary)
# --------------------------------------------------------
T = {
    "en": {
        "title": "📯 Verkada Horn Helix Controller",
        "caption": "A control tool designed for bypassing direct control limitations of Horns via Verkada Video Tagging API.",
        "sidebar_header": "⚙️ Configuration",
        "lang_label": "🌐 Language Selection",
        "api_key": "API Key",
        "api_key_help": "Enter the API Key generated from Verkada Command > Settings > API Keys.",
        "org_id": "Organization ID (org_id)",
        "org_id_placeholder": "Enter Organization ID (UUID)",
        "org_id_help": "Organization ID used in the URL query string (?org_id=...).",
        "camera_id": "Camera ID",
        "camera_id_placeholder": "Enter Camera ID (UUID)",
        "camera_id_help": "The Camera ID linked with the Helix/Tagging event.",
        "event_type_uid": "Event Type UID (event_type_uid)",
        "event_type_uid_placeholder": "Enter Event Type UID (UUID)",
        "event_type_uid_help": "The event_type_uid defined in your Verkada Command console.",
        "num_horns": "Number of Horns (Individual Devices)",
        "num_buttons": "Number of Message Buttons per Horn",
        "horn_setup_header": "🆔 Horn별 Device Name 설정 / Horn Device Name Setup",
        "horn_setup_subheader": "Please enter the Device Name for each configured Horn.",
        "horn_name_label": "Horn {} Device Name",
        "panel_header": "🚀 Horn Control Panel (Tablet Touch Screen Optimized)",
        "panel_info": "Designed for easy operation with fingers on iPad environments. Tapping a button automatically issues a short-lived token and sends the event.",
        "horn_title": "### 📢 Horn {} (Name: `{}`)",
        "warn_api_key": "⚠️ Please enter the API Key in the sidebar first.",
        "warn_org_id": "⚠️ Please enter the Organization ID in the sidebar.",
        "warn_camera_id": "⚠️ Please enter the Camera ID in the sidebar.",
        "warn_event_uid": "⚠️ Please enter the Event Type UID in the sidebar.",
        "spinner": "Verkada authentication and event transmission in progress...",
        "success": "✅ [Success] Horn {} -> Message ID: {} Transmission Complete!",
        "payload_expander": "View Actual Transmitted Data (Payload)",
        "api_error": "❌ [API Error] Status Code: {}",
        "system_error": "💥 [System Error] {}"
    },
    "ko": {
        "title": "📯 Verkada Horn Helix Controller",
        "caption": "Verkada Video Tagging API를 통해 호른의 직접 제어 한계를 우회하도록 설계된 제어 도구입니다.",
        "sidebar_header": "⚙️ 기본 설정 (Configuration)",
        "lang_label": "🌐 언어 선택 (Language)",
        "api_key": "API Key",
        "api_key_help": "Verkada Command > Settings > API Keys 에서 생성한 API Key를 입력하세요.",
        "org_id": "Organization ID (org_id)",
        "org_id_placeholder": "조직 ID(UUID)를 입력하세요",
        "org_id_help": "URL 쿼리 스트링(?org_id=...)에 들어갈 조직 ID입니다.",
        "camera_id": "Camera ID",
        "camera_id_placeholder": "카메라 ID(UUID)를 입력하세요",
        "camera_id_help": "Helix 메시지와 연동할 Camera ID를 입력하세요.",
        "event_type_uid": "Event Type UID (event_type_uid)",
        "event_type_uid_placeholder": "이벤트 타입 UID(UUID)를 입력하세요",
        "event_type_uid_help": "웹 화면에서 정의한 event_type_uid 정보입니다.",
        "num_horns": "Horn 개수 (개별 Device)",
        "num_buttons": "Horn당 메시지 버튼 개수",
        "horn_setup_header": "🆔 Horn별 Device Name 설정 / Horn Device Name Setup",
        "horn_setup_subheader": "설정한 Horn 개수만큼 Device Name을 입력해주세요.",
        "horn_name_label": "Horn {} Device Name",
        "panel_header": "🚀 Horn 제어 패널 (태블릿 터치 스크린용)",
        "panel_info": "아이패드 환경에서 검지나 엄지손가락으로 쉽게 누를 수 있도록 설계되었습니다. 버튼을 누르면 실시간으로 단기 토큰을 생성해 전송합니다.",
        "horn_title": "### 📢 Horn {} (Name: `{}`)",
        "warn_api_key": "⚠️ 사이드바에 API Key를 먼저 입력해주세요.",
        "warn_org_id": "⚠️ 사이드바에 Organization ID를 입력해주세요.",
        "warn_camera_id": "⚠️ 사이드바에 Camera ID를 입력해주세요.",
        "warn_event_uid": "⚠️ 사이드바에 Event Type UID를 입력해주세요.",
        "spinner": "Verkada 보안 인증 및 이벤트 전송 중...",
        "success": "✅ [성공] Horn {} -> Message ID: {} 전송 완료!",
        "payload_expander": "실제 전송된 데이터(Payload) 확인",
        "api_error": "❌ [API 오류] 상태 코드: {}",
        "system_error": "💥 [시스템 오류] {}"
    }
}

# --------------------------------------------------------
# 🤖 브라우저 환경 언어 자동 감지 및 세션 초기화
# --------------------------------------------------------
if "lang" not in st.session_state:
    try:
        # 사용자의 브라우저 Accept-Language 헤더 추출
        accept_lang = st.context.headers.get("Accept-Language", "")
        # 한국어('ko')가 포함되어 있으면 ko, 그 외 모든 언어는 en으로 기본 설정
        if "ko" in accept_lang.lower():
            st.session_state.lang = "ko"
        else:
            st.session_state.lang = "en"
    except:
        st.session_state.lang = "en"  # 예외 상황 발생 시 영어 기본 세팅

# --------------------------------------------------------
# 📱 아이패드 터치 조작을 위한 초대형 버튼 CSS 스타일
# --------------------------------------------------------
st.markdown("""
    <style>
        div.stButton > button:first-child {
            height: 6.5rem !important;      
            font-size: 32px !important;     
            font-weight: bold !important;   
            border-radius: 16px !important; 
            margin-bottom: 15px !important; 
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.15) !important; 
            transition: all 0.15s ease;
        }
        div.stButton > button:first-child:active {
            transform: scale(0.98); 
        }
        div.stButton > button:first-child:hover {
            border-color: #ff4b4b !important;
            background-color: rgba(255, 75, 75, 0.05) !important;
        }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------
# 1. 사이드바 설정 (언어 변경 메뉴 포함)
# --------------------------------------------------------
st.sidebar.header("⚙️ Settings")

# 수동으로 언어를 변경할 수 있는 셀렉트박스 메뉴 배치
lang_options = {"en": "English", "ko": "한국어"}
current_idx = list(lang_options.keys()).index(st.session_state.lang)

selected_lang_name = st.sidebar.selectbox(
    "🌐 Language / 언어 선택",
    options=list(lang_options.values()),
    index=current_idx
)
# 선택한 값에 따라 세션 언어 상태 업데이트
st.session_state.lang = [k for k, v in lang_options.items() if v == selected_lang_name][0]

# 현재 언어 번역 팩 지정
text = T[st.session_state.lang]

# 메인 타이틀 출력
st.title(text["title"])
st.caption(text["caption"])

st.sidebar.markdown("---")
st.sidebar.subheader(text["sidebar_header"])

api_key = st.sidebar.text_input(text["api_key"], type="password", help=text["api_key_help"])

org_id = st.sidebar.text_input(
    text["org_id"],
    value="",
    placeholder=text["org_id_placeholder"],
    help=text["org_id_help"]
)

camera_id = st.sidebar.text_input(
    "Camera ID", 
    value="", 
    placeholder=text["camera_id_placeholder"],
    help=text["camera_id_help"]
)

event_type_uid = st.sidebar.text_input(
    "Event Type UID",
    value="",
    placeholder=text["event_type_uid_placeholder"],
    help=text["event_type_uid_help"]
)

st.sidebar.markdown("---")

num_horns = st.sidebar.number_input(text["num_horns"], min_value=1, max_value=20, value=1)
num_buttons = st.sidebar.number_input(text["num_buttons"], min_value=1, max_value=10, value=3)

# --------------------------------------------------------
# 2. 메인 화면: 각 Horn의 Device Name 입력 칸 생성
# --------------------------------------------------------
st.subheader(text["horn_setup_header"])
st.write(text["horn_setup_subheader"])

horn_names = []
id_cols = st.columns(min(num_horns, 4)) 

for i in range(num_horns):
    col_idx = i % 4
    with id_cols[col_idx]:
        h_name = st.text_input(
            text["horn_name_label"].format(i+1), 
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
        raise Exception(f"Token generation failed (Status: {response.status_code}) - {response.text}")


def send_video_tagging_event(token, org_id, cam_id, event_uid, dev_name, msg_type):
    url = f"https://api.verkada.com/cameras/v1/video_tagging/event?org_id={org_id}"
    
    headers = {
        "content-type": "application/json",
        "x-verkada-auth": token,
        "Authorization": f"Bearer {token}"
    }
    
    current_time_ms = int(time.time() * 1000)
    
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
st.subheader(text["panel_header"])
st.info(text["panel_info"])

for i in range(num_horns):
    current_horn_name = horn_names[i]
    st.write(text["horn_title"].format(i+1, current_horn_name))
    
    btn_cols = st.columns(num_buttons)
    for j in range(num_buttons):
        message_id = j + 1
        
        with btn_cols[j]:
            btn_label = f"Msg {message_id}"
            
            if st.button(btn_label, key=f"btn_{i}_{message_id}", use_container_width=True):
                if not api_key:
                    st.warning(text["warn_api_key"])
                elif not org_id:
                    st.warning(text["warn_org_id"])
                elif not camera_id:
                    st.warning(text["warn_camera_id"])
                elif not event_type_uid:
                    st.warning(text["warn_event_uid"])
                else:
                    with st.spinner(text["spinner"]):
                        try:
                            short_token = get_short_lived_token(api_key)
                            
                            response, sent_payload = send_video_tagging_event(
                                token=short_token,
                                org_id=org_id,
                                cam_id=camera_id,
                                event_uid=event_type_uid,
                                dev_name=current_horn_name,
                                msg_type=message_id
                            )
                            
                            if response.status_code in [200, 201]:
                                st.success(text["success"].format(i+1, message_id))
                                with st.expander(text["payload_expander"]):
                                    st.json(sent_payload)
                            else:
                                st.error(text["api_error"].format(response.status_code))
                                st.json(response.json() if response.text else response.text)
                                
                        except Exception as e:
                            st.error(text["system_error"].format(e))
                            
    st.markdown("---")
