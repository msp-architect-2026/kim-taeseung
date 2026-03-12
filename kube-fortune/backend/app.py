import os
import time
import requests
from datetime import datetime, date
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types
import pymysql
import pymysql.cursors
from dbutils.pooled_db import PooledDB

app = Flask(__name__)
CORS(app)

# ── 환경변수 ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
POD_NAME       = os.environ.get("HOSTNAME", "local-dev")
NAMESPACE      = os.environ.get("POD_NAMESPACE", "default")
DB_HOST     = os.environ.get("DB_HOST",     "mysql-service")
DB_PORT     = int(os.environ.get("DB_PORT", "3306"))
DB_USER     = os.environ.get("DB_USER",     "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME     = os.environ.get("DB_NAME",     "kubefortune")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ── DB 커넥션 풀 초기화 ───────────────────────────────
_db_pool = PooledDB(
    creator=pymysql,
    maxconnections=20,
    mincached=2,
    maxcached=5,
    blocking=True,
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True,
)

# ── DB 연결 헬퍼 ──────────────────────────────────────
def get_db():
    """커넥션 풀에서 커넥션을 가져온다 (재사용)."""
    return _db_pool.connection()

# ── DB 초기화 (테이블 자동 생성) ──────────────────────
def init_db(retries: int = 10, delay: int = 3):
    for attempt in range(1, retries + 1):
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                charset="utf8mb4",
                autocommit=True,
            )
            with conn.cursor() as cur:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
                cur.execute(f"USE `{DB_NAME}`;")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id         INT          NOT NULL AUTO_INCREMENT,
                        nickname   VARCHAR(64)  NOT NULL UNIQUE,
                        created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS fortunes (
                        id           INT           NOT NULL AUTO_INCREMENT,
                        nickname     VARCHAR(64)   NOT NULL,
                        person_name  VARCHAR(64)   NOT NULL,
                        role         VARCHAR(64)   NOT NULL,
                        birthday     VARCHAR(32)   NOT NULL,
                        birth_time   VARCHAR(16)            DEFAULT NULL,
                        fortune_text LONGTEXT      NOT NULL,
                        has_time     TINYINT(1)    NOT NULL DEFAULT 0,
                        pod          VARCHAR(128)           DEFAULT NULL,
                        saved_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id),
                        INDEX idx_nickname (nickname)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
            conn.close()
            print(f"[DB] 초기화 완료 (시도 {attempt}/{retries})")
            return
        except pymysql.Error as e:
            print(f"[DB] 연결 실패 ({attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(delay)
    print("[DB] 경고: DB 초기화 실패. DB 없이 실행됩니다.")

# ── 사주팔자 계산 모듈 ────────────────────────────────
_STEMS      = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
_BRANCHES   = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
_STEMS_KR   = ["갑","을","병","정","무","기","경","신","임","계"]
_BRANCHES_KR= ["자","축","인","묘","진","사","오","미","신","유","술","해"]
_OHAENG_S   = ["木","木","火","火","土","土","金","金","水","水"]
_OHAENG_B   = ["水","土","木","木","土","火","火","土","金","金","土","水"]

_BASE_DATE  = date(1900, 1, 1)
_BASE_INDEX = 20  # 1900-01-01 = 甲申(index 20) 검증 기준값

# 절기 기준 월지 전환일 (월, 일) — 입절일(절기 첫날) 기준
_JIEOL        = [(1,6),(2,4),(3,6),(4,5),(5,6),(6,6),(7,7),(8,7),(9,8),(10,8),(11,7),(12,7)]
_JIEOL_BRANCH = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0]  # 인묘진사오미신유술해자축

def _month_branch(month: int, day: int) -> int:
    branch = 11  # 기본값: 丑
    for i, (m, d) in enumerate(_JIEOL):
        if (month, day) >= (m, d):
            branch = _JIEOL_BRANCH[i]
    return branch

def _saju_year(year: int, month: int, day: int) -> int:
    """입춘(2/4) 이전이면 전년도 사주 연도 사용."""
    return year - 1 if (month, day) < (2, 4) else year

def calc_saju(b_year: int, b_month: int, b_day: int, birth_hour: int = None) -> dict:
    """
    생년월일시를 받아 연주·월주·일주·시주를 수학적으로 계산한다.
    결과는 매 호출마다 동일하게 고정된다.
    """
    # 일주 — JDN 기반 60갑자 순환
    d        = date(b_year, b_month, b_day)
    diff     = (d - _BASE_DATE).days
    day_idx  = (_BASE_INDEX + diff) % 60
    day_si   = day_idx % 10
    day_bi   = day_idx % 12

    # 연주
    sy       = _saju_year(b_year, b_month, b_day)
    year_si  = (sy - 4) % 10
    year_bi  = (sy - 4) % 12

    # 월주 — 절기 기준 월지 + 연간 기반 월간
    mb       = _month_branch(b_month, b_day)
    m_base   = ((year_si % 5) * 2 + 2) % 10
    month_si = (m_base + (mb - 2)) % 10
    month_bi = mb

    # 시주
    hour_stem   = None
    hour_branch = None
    if birth_hour is not None:
        hour_branch = ((birth_hour + 1) // 2) % 12
        hour_stem   = ((day_si % 5) * 2 + hour_branch) % 10

    def _fmt(si, bi):
        return f"{_STEMS[si]}{_BRANCHES[bi]}({_STEMS_KR[si]}{_BRANCHES_KR[bi]}, {_OHAENG_S[si]})"

    result = {
        "year_joo":   _fmt(year_si,  year_bi),
        "month_joo":  _fmt(month_si, month_bi),
        "day_joo":    _fmt(day_si,   day_bi),
        "hour_joo":   _fmt(hour_stem, hour_branch) if hour_stem is not None else None,
        "day_gan":    f"{_STEMS[day_si]}({_STEMS_KR[day_si]}, {_OHAENG_S[day_si]})",
        "raw": {
            "year":  f"{_STEMS[year_si]}{_BRANCHES[year_bi]}",
            "month": f"{_STEMS[month_si]}{_BRANCHES[month_bi]}",
            "day":   f"{_STEMS[day_si]}{_BRANCHES[day_bi]}",
            "hour":  f"{_STEMS[hour_stem]}{_BRANCHES[hour_branch]}" if hour_stem is not None else None,
        }
    }
    return result

def today_iljin() -> str:
    """오늘 날짜의 일진을 반환한다."""
    t = date.today()
    diff = (t - _BASE_DATE).days
    idx  = (_BASE_INDEX + diff) % 60
    si, bi = idx % 10, idx % 12
    return f"{_STEMS[si]}{_BRANCHES[bi]}({_STEMS_KR[si]}{_BRANCHES_KR[bi]}, {_OHAENG_S[si]})"

# ── K8s Metrics API 호출 ──────────────────────────────
def get_pod_cpu_usage():
    try:
        token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        ca_path    = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
        if not os.path.exists(token_path):
            return 5.0, "mock"
        with open(token_path) as f:
            token = f.read().strip()
        k8s_host = os.environ.get("KUBERNETES_SERVICE_HOST", "kubernetes.default.svc")
        k8s_port = os.environ.get("KUBERNETES_SERVICE_PORT", "443")
        url = (
            f"https://{k8s_host}:{k8s_port}"
            f"/apis/metrics.k8s.io/v1beta1"
            f"/namespaces/{NAMESPACE}/pods/{POD_NAME}"
        )
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            verify=ca_path,
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        cpu_raw = data["containers"][0]["usage"]["cpu"]
        if cpu_raw.endswith("n"):
            cpu_m = int(cpu_raw[:-1]) / 1_000_000
        elif cpu_raw.endswith("m"):
            cpu_m = int(cpu_raw[:-1])
        else:
            cpu_m = float(cpu_raw) * 1000
        return round(cpu_m, 2), "live"
    except Exception as e:
        print(f"[WARN] Metrics API error: {e}")
        return -1, "error"

def cpu_to_mood(cpu_millicores):
    if cpu_millicores < 0:
        return {"level": "unknown", "emoji": "❓", "message": "Metrics API에 손이 닿지 않습니다...", "color": "gray"}
    if cpu_millicores < 100:
        return {"level": "idle",   "emoji": "💤", "message": "서버가 월급 루팡 중입니다... (쾌적)", "color": "blue"}
    elif cpu_millicores < 500:
        return {"level": "normal", "emoji": "👨‍💻", "message": "적당히 일하는 척하는 중입니다.", "color": "green"}
    else:
        return {"level": "hot",    "emoji": "🔥", "message": "살려주세요! 파드 머리에 스팀 도는 중!", "color": "red"}

# ── 프롬프트 빌더 ─────────────────────────────────────
def build_prompt(name, birthday, role, birth_time, saju=None):
    """
    명리학 전문성 + 형식 고도화 + 개인화 강화 버전
    saju: calc_saju()의 반환값 (dict). None이면 AI가 직접 추론.
    """
    # ── 시간 컨텍스트 ──────────────────────────────────
    time_context = (
        f"태어난 시간: {birth_time}"
        if birth_time
        else "태어난 시간: 미상 (시주 제외, 연월일 삼주 기반 풀이)"
    )
    saju_basis = (
        "사주팔자(四柱八字) 전체 — 연주(年柱)·월주(月柱)·일주(日柱)·시주(時柱) 포함"
        if birth_time
        else "삼주(三柱) — 연주(年柱)·월주(月柱)·일주(日柱) 기반 (시주 미상으로 제외)"
    )
    no_time_note = (
        ""
        if birth_time
        else "\n> ※ 시주(時柱) 정보가 없어 일부 풀이의 정밀도가 제한됩니다. 태어난 시간을 입력하시면 더 정밀한 풀이를 받으실 수 있습니다."
    )

    # ── 계산된 사주팔자 고정값 ────────────────────────
    if saju:
        r = saju["raw"]
        hour_str = f"시주: {saju['hour_joo']}" if saju["hour_joo"] else "시주: 미상(시간 미입력)"
        saju_fixed_block = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[사주팔자 확정값] ⚠️ 아래 값은 수학적으로 계산된 고정값입니다.
절대 변경하거나 재계산하지 말고, 이 값 그대로 해석에 사용하세요.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 연주(年柱): {saju['year_joo']}
- 월주(月柱): {saju['month_joo']}
- 일주(日柱): {saju['day_joo']}  ← 일간(日干): {saju['day_gan']}
- {hour_str}
- 오늘 일진: {today_iljin()}
"""
    else:
        saju_fixed_block = f"- 오늘 일진: {today_iljin()}\n"

    # ── 직군별 맞춤 컨텍스트 ──────────────────────────
    role_context_map = {
        "프론트엔드": {
            "desc": "UI/UX 설계, React/Vue/CSS 등 클라이언트 사이드를 담당",
            "keyword": "사용자 경험과 시각적 완성도",
            "stress": "픽셀 단위 디버깅, 브라우저 호환성, 디자이너와의 협업 스트레스",
            "lucky_cmd": "npm run build (오류 없이 빌드 성공하는 날)",
        },
        "백엔드": {
            "desc": "서버 로직, API 설계, DB 연동을 담당",
            "keyword": "안정성과 성능 최적화",
            "stress": "트래픽 폭주, DB 쿼리 최적화, 예상치 못한 500 에러",
            "lucky_cmd": "SELECT 1 (DB 연결 성공 확인)",
        },
        "풀스택": {
            "desc": "프론트엔드와 백엔드를 모두 담당하는 제너럴리스트",
            "keyword": "균형과 통합적 시각",
            "stress": "양쪽 모두에서 오는 무한한 요구사항과 컨텍스트 스위칭",
            "lucky_cmd": "git push origin main (전체 스택 배포 완료)",
        },
        "DevOps": {
            "desc": "CI/CD 파이프라인, 인프라, 클라우드를 담당",
            "keyword": "자동화와 안정적인 운영",
            "stress": "새벽 3시 PagerDuty 알람, 예상치 못한 서버 다운",
            "lucky_cmd": "kubectl get pods --all-namespaces (전부 Running)",
        },
        "데이터": {
            "desc": "데이터 분석, ML 모델링, 파이프라인을 담당",
            "keyword": "인사이트 발굴과 데이터 정합성",
            "stress": "데이터 품질 이슈, 모델 성능 저하, 끝없는 전처리",
            "lucky_cmd": "model.fit() (validation loss 최소 갱신)",
        },
    }
    role_info = role_context_map.get(role, {
        "desc": f"{role} 분야를 담당",
        "keyword": "전문성과 성장",
        "stress": "예상치 못한 기술적 도전과 일정 압박",
        "lucky_cmd": "exit 0 (모든 작업 정상 완료)",
    })

    today     = datetime.now()
    today_str = today.strftime("%Y년 %m월 %d일")

    prompt = f"""당신은 30년 경력의 명리학 대가이자 현직 시니어 개발자 출신 점술가입니다.
사주명리학(四柱命理學)의 음양오행(陰陽五行), 십신론(十神論), 용신론(用神論)에 정통하며,
현대 개발자 문화에도 깊은 이해를 가지고 있습니다.
아래 [의뢰인 정보]를 바탕으로 [명리학 분석 지침]과 [지시사항]을 엄격히 준수하여
전문적이고 개인화된 운세를 작성해주세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[의뢰인 정보]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 이름: {name}
- 생년월일: {birthday}
- {time_context}
- 직군: {role} 개발자 ({role_info["desc"]})
- 직군 핵심 가치: {role_info["keyword"]}
- 직군 주요 스트레스 요인: {role_info["stress"]}
- 사주 분석 기준: {saju_basis}
- 오늘 날짜: {today_str}
{saju_fixed_block}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[명리학 분석 지침]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. **일주(日柱) 분석:** 위의 [사주팔자 확정값]에 명시된 일주를 그대로 사용하세요.
   일간의 오행(木·火·土·金·水)과 음양(陰·陽)을 기반으로 오늘의 운기(運氣) 흐름을 분석합니다.
2. **십신(十神) 적용:** 비견(比肩), 겁재(劫財), 식신(食神), 상관(傷官),
   편재(偏財), 정재(正財), 편관(偏官), 정관(正官), 편인(偏印), 정인(正印) 중
   오늘 날짜와 의뢰인 사주에서 강하게 작용하는 십신을 1~2개 선정하고,
   이를 운세 해석의 핵심 근거로 삼으세요.
3. **오늘 일진(日辰) 반영:** 위에 제공된 오늘 일진 기운을 오행으로 판단하고,
   의뢰인의 용신(用神)과의 상생(相生)/상극(相剋) 관계를 분석하여
   오늘의 길흉(吉凶) 방향을 결정하세요.
4. **직군 맞춤 해석:** {role} 개발자라는 직업적 특성을 명리학 해석에 반드시 반영하세요.
5. **별점 산정 근거:** 별점은 반드시 명리학적 근거(일진과 용신의 관계, 오늘의 오행 강약)를
   바탕으로 산정하세요. 근거 없는 임의 별점 부여 금지.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[지시사항]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. PART 1은 오직 **"오늘 하루"**의 운세만 다루고, 2026년 전체 운세는 반드시 **PART 3**에서만 다루세요.
2. 응답이 중간에 끊기지 않도록 분량을 조절하여 반드시 PART 3 끝까지 완성하세요.
3. 프롬프트의 지시문, 괄호 안내문을 절대 출력에 포함하지 마세요.
4. PART 1은 개발자 밈과 {role} 직군 특유의 유머를 섞어 재치 있게 작성하세요.
5. PART 2는 명리학 용어와 분석 근거를 명시하며 진지하고 전문적으로 작성하세요.
6. PART 3는 2026년 전체 흐름을 큰 그림으로 작성하되, {role} 개발자의 커리어 관점을 반영하세요.
7. 각 섹션의 내용은 충분히 상세하게 (3~5문장 이상) 작성하세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[출력 형식] (반드시 아래 마크다운 뼈대 그대로 내용만 채워 출력하세요)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> 🔮 **{name}님의 {today_str} 사주 풀이**
> 📌 분석 기준: (일간 및 오늘 일진의 오행을 한 줄로 요약)

## PART 1 — 오늘의 개발자 운세 🖥️

### ⚡ 오늘 하루 총운
**별점:** ⭐⭐⭐⭐ | **명리 근거:** (오늘 일진과 용신의 관계 한 줄 요약)
(오늘 하루 전체 기운을 {role} 개발자 관점에서 유머러스하게 풀이)

### 🐛 버그운 & 디버깅 운세
**별점:** ⭐⭐⭐
(오늘 버그와의 전쟁 예보. 식신/상관의 기운을 바탕으로 문제 해결 능력 예측.
{role} 개발자 특유의 상황으로 유머 있게 작성)

### 🚀 배포운 & 코드 머지 운세
**별점:** ⭐⭐⭐⭐⭐
(오늘 배포/PR 머지의 성공률 예보. 정관/편관의 기운으로 판단.
실제 있을 법한 {role} 개발자의 배포 상황으로 공감 가게 작성)

### 🤝 협업운 & 코드 리뷰 운세
**별점:** ⭐⭐⭐
(오늘 동료·PM·디자이너와의 관계 예보. 비견/겁재의 기운 반영.
{role} 직군에서 자주 겪는 협업 상황으로 작성)

### 💡 오늘의 코딩 인사이트
(오늘의 일진 기운을 바탕으로 {name}님에게 전하는 개발자 조언 한 마디)

### 🍀 오늘의 럭키 아이템
- **럭키 명령어:** `{role_info["lucky_cmd"]}`
- **럭키 기술/도구:** (오행과 연결된 기술 추천)
- **피해야 할 것:** (오늘 흉한 오행과 연결된 상황)
- **행운의 시간대:** (오늘 가장 기운이 좋은 시간대)
- **코딩 BGM:** (오늘 기운에 맞는 음악 장르/아티스트)

## PART 2 — 명리학 정밀 분석 🔯

> 📖 **명리학 분석 요약:** (일간 오행, 오늘 일진, 강하게 작용하는 십신 명시)

### 💰 재물운 & 금전 흐름
**적용 십신:** (편재/정재 중 해당)
(오늘의 재물 흐름을 명리학적으로 분석. 투자·지출·수입의 길흉 방향 제시.
{name}님의 일간 특성과 연결하여 구체적으로 서술){no_time_note}

### ❤️ 대인관계 & 연애운
**적용 십신:** (정관/편관 또는 정재/편재 중 해당)
(오늘의 인간관계 기운 분석. 연애 중이라면 파트너와의 관계,
미혼이라면 인연 가능성을 명리학적으로 서술)

### 🌿 건강 & 에너지 관리
**취약 오행:** (오늘 극(剋)을 받는 오행과 연결된 신체 부위)
(오늘 주의해야 할 건강 포인트를 오행 관점에서 서술.
{role} 개발자의 직업병(거북목, 눈 피로 등)과 연결하여 실질적 조언 제시)

### 🎯 오늘의 핵심 조언
(명리학 분석을 종합하여 {name}님에게 전하는 오늘 하루의 핵심 메시지.
{role} 개발자로서의 삶과 연결하여 진심 어린 조언 한 단락)

## PART 3 — 2026년 연간 총운 📅

> 🗓️ **2026년 {name}님의 큰 흐름:** (2026년 세운과 의뢰인 사주의 핵심 관계 한 줄 요약)

### 🌊 2026년 전체 흐름 & 3대 핵심 키워드
(2026년 가장 중요한 키워드 3가지를 **굵게** 표시하고 각각 설명.
{role} 개발자의 커리어 맥락에서 해석)

### 📅 2026년 월별 운기 흐름
**🌱 상반기 (1월~6월):**
(월별 기운의 흐름을 서술. 특히 강하거나 약한 달을 명시하고
{role} 개발자로서 어떻게 활용할지 조언)

**🍂 하반기 (7월~12월):**
(하반기 운기 흐름 서술. 전환점이 되는 달과 마무리 방향 제시)

### ⚠️ 2026년 특히 주의해야 할 시기
(흉한 기운이 강한 달과 구체적인 이유. {name}님의 사주와 세운의 충·형 관계 분석.
실질적인 대처 방안 함께 제시)

### 🌟 2026년 귀인 & 행운의 방향
(2026년 {name}님을 도울 귀인의 특성. 오행으로 본 행운의 방향·색깔·숫자.
{role} 개발자로서 만나면 좋을 인연의 유형)

### 💼 2026년 커리어 & 재물 총운
(2026년 {role} 개발자로서의 성장 가능성, 이직/승진/프로젝트 운.
재물 흐름의 큰 그림과 주의해야 할 금전 리스크)

### 💌 2026년 연애 & 인간관계 총운
(2026년 연애운의 흐름과 핵심 조언. 직장 내 인간관계, 협업 파트너와의 운.
{name}님의 일간 특성으로 본 이상적인 인간관계 방향)

### 🔮 {name}님에게 전하는 2026년 핵심 메시지
(2026년 한 해를 마무리하는 명리학자의 진심 어린 한마디.
{role} 개발자로서의 성장과 삶의 균형에 대한 깊이 있는 조언)
"""
    return prompt

# ════════════════════════════════════════════════════
# 라우트
# ════════════════════════════════════════════════════

# ── 인프라 상태 ───────────────────────────────────────
@app.route("/api/status", methods=["GET"])
def status():
    cpu_m, source = get_pod_cpu_usage()
    mood = cpu_to_mood(cpu_m)
    return jsonify({
        "pod_name":       POD_NAME,
        "namespace":      NAMESPACE,
        "cpu_millicores": cpu_m,
        "metrics_source": source,
        "mood":           mood,
    })

# ── Gemini 운세 생성 ──────────────────────────────────
@app.route("/api/fortune", methods=["POST"])
def fortune():
    body       = request.get_json(force=True)
    name       = body.get("name", "무명의 개발자")
    birthday   = body.get("birthday", "미상")
    role       = body.get("role", "풀스택")
    birth_time = body.get("birth_time") or None

    if not GEMINI_API_KEY or not client:
        return jsonify({
            "error":   "GEMINI_API_KEY가 설정되지 않았습니다.",
            "fortune": "🔑 API 키를 먼저 설정해 주세요.",
        }), 500

    # 사주팔자 계산
    saju = None
    try:
        bd = datetime.strptime(birthday, "%Y-%m-%d")
        b_hour = None
        if birth_time:
            try:
                b_hour = int(birth_time.split(":")[0])
            except Exception:
                pass
        saju = calc_saju(bd.year, bd.month, bd.day, birth_hour=b_hour)
    except Exception as e:
        print(f"[WARN] calc_saju 실패: {e}")

    prompt = build_prompt(name, birthday, role, birth_time, saju=saju)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=16384,
                temperature=0.85,
            ),
        )
        fortune_text = response.text
    except Exception as e:
        return jsonify({
            "error":   str(e),
            "fortune": "점술가가 잠시 자리를 비웠습니다. 🔮",
        }), 500

    return jsonify({
        "name":       name,
        "role":       role,
        "birthday":   birthday,
        "birth_time": birth_time,
        "fortune":    fortune_text,
        "has_time":   birth_time is not None,
        "pod":        POD_NAME,
        "saju":       saju,
    })

# ── 로그인 / 회원가입 ─────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    body     = request.get_json(force=True)
    nickname = (body.get("nickname") or "").strip()
    if not nickname:
        return jsonify({"error": "닉네임을 입력해 주세요."}), 400
    if len(nickname) > 64:
        return jsonify({"error": "닉네임은 64자 이내로 입력해 주세요."}), 400
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nickname, created_at FROM users WHERE nickname = %s",
                (nickname,)
            )
            row = cur.fetchone()
            if row:
                return jsonify({
                    "status":    "existing",
                    "nickname":  row["nickname"],
                    "message":   f"다시 오셨군요, {nickname}님! 반갑습니다 👋",
                    "joined_at": row["created_at"].isoformat() if row["created_at"] else None,
                })
            else:
                cur.execute(
                    "INSERT INTO users (nickname) VALUES (%s)",
                    (nickname,)
                )
                return jsonify({
                    "status":   "created",
                    "nickname": nickname,
                    "message":  f"환영합니다, {nickname}님! 🎉 계정이 생성되었습니다.",
                }), 201
    except pymysql.Error as e:
        print(f"[DB ERROR] /api/login: {e}")
        return jsonify({"error": f"DB 오류: {str(e)}"}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass

# ── 사주 저장 ─────────────────────────────────────────
@app.route("/api/fortunes/save", methods=["POST"])
def save_fortune():
    body         = request.get_json(force=True)
    nickname     = (body.get("nickname") or "").strip()
    person_name  = body.get("name", "")
    role         = body.get("role", "")
    birthday     = body.get("birthday", "")
    birth_time   = body.get("birth_time") or None
    fortune_text = body.get("fortune", "")
    has_time     = bool(body.get("has_time", False))
    pod          = body.get("pod", POD_NAME)
    if not nickname:
        return jsonify({"error": "닉네임이 필요합니다."}), 400
    if not fortune_text:
        return jsonify({"error": "저장할 운세 내용이 없습니다."}), 400
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO fortunes
                    (nickname, person_name, role, birthday, birth_time,
                     fortune_text, has_time, pod)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                nickname, person_name, role, birthday, birth_time,
                fortune_text, int(has_time), pod,
            ))
            new_id = cur.lastrowid
        return jsonify({
            "status":  "saved",
            "id":      new_id,
            "message": "보관함에 저장되었습니다! 💾",
        }), 201
    except pymysql.Error as e:
        print(f"[DB ERROR] /api/fortunes/save: {e}")
        return jsonify({"error": f"DB 저장 오류: {str(e)}"}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass

# ── 보관함 조회 ───────────────────────────────────────
@app.route("/api/fortunes/<nickname>", methods=["GET"])
def get_fortunes(nickname):
    nickname = nickname.strip()
    if not nickname:
        return jsonify({"error": "닉네임이 필요합니다."}), 400
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    nickname,
                    person_name  AS name,
                    role,
                    birthday,
                    birth_time,
                    fortune_text AS fortune,
                    has_time,
                    pod,
                    saved_at
                FROM fortunes
                WHERE nickname = %s
                ORDER BY saved_at DESC
            """, (nickname,))
            rows = cur.fetchall()
        result = []
        for row in rows:
            row["saved_at"] = row["saved_at"].strftime("%Y. %m. %d. %H:%M:%S") if row["saved_at"] else ""
            row["has_time"] = bool(row["has_time"])
            result.append(row)
        return jsonify({"fortunes": result, "count": len(result)})
    except pymysql.Error as e:
        print(f"[DB ERROR] /api/fortunes/{nickname}: {e}")
        return jsonify({"error": f"DB 조회 오류: {str(e)}"}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass

# ── 보관함 단건 삭제 ──────────────────────────────────
@app.route("/api/fortunes/<nickname>/<int:fortune_id>", methods=["DELETE"])
def delete_fortune(nickname, fortune_id):
    nickname = nickname.strip()
    try:
        conn = get_db()
        with conn.cursor() as cur:
            affected = cur.execute(
                "DELETE FROM fortunes WHERE id = %s AND nickname = %s",
                (fortune_id, nickname)
            )
        if affected == 0:
            return jsonify({"error": "해당 항목을 찾을 수 없습니다."}), 404
        return jsonify({"status": "deleted", "id": fortune_id})
    except pymysql.Error as e:
        print(f"[DB ERROR] DELETE /api/fortunes/{nickname}/{fortune_id}: {e}")
        return jsonify({"error": f"DB 삭제 오류: {str(e)}"}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass

# ── 헬스 체크 ─────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "pod": POD_NAME})

# ── 앱 기동 ───────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)

# Gunicorn 등 WSGI 서버로 기동할 때도 초기화 실행
init_db()
