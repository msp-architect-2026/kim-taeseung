import os
import time
import requests
from datetime import datetime
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
    maxconnections=20,       # 최대 커넥션 수 (파드당)
    mincached=2,             # 시작 시 미리 생성할 커넥션 수
    maxcached=5,             # 유휴 상태로 유지할 최대 커넥션 수
    blocking=True,           # 풀이 꽉 찼을 때 대기 (에러 대신)
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
    """
    MySQL이 아직 기동 중일 수 있으므로 재시도 로직을 포함한다.
    앱 시작 시 한 번만 호출된다.
    """
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
                # DB 생성
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
                cur.execute(f"USE `{DB_NAME}`;")

                # users 테이블
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id         INT          NOT NULL AUTO_INCREMENT,
                        nickname   VARCHAR(64)  NOT NULL UNIQUE,
                        created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # fortunes 테이블
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
def build_prompt(name, birthday, role, birth_time):
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

    no_time_footer = (
        ""
        if birth_time
        else "\n> ※ 시주(時柱) 정보가 없어 일부 풀이의 정밀도가 제한됩니다. 태어난 시간을 입력하시면 더 정밀한 풀이를 받으실 수 있습니다."
    )

    prompt = f"""당신은 20년 차 베테랑 개발자 점술가이자 명리학 전문가입니다.
아래 [의뢰인 정보]를 바탕으로 [지시사항]을 엄격히 준수하여 운세를 작성해주세요.

[의뢰인 정보]
- 이름: {name}
- 생년월일: {birthday}
- {time_context}
- 직군: {role} 개발자
- 사주 분석 기준: {saju_basis}

[지시사항]
1. 시간적 배경을 절대 혼동하지 마세요. PART 1는 오직 **"오늘 하루"**의 운세만 다루고, 2026년 전체 운세는 반드시 **PART 3**에서만 다루어야 합니다.
2. 응답이 너무 길어져서 중간에 끊기는 일이 없도록, 전체 분량을 스스로 조절하여 반드시 PART 3 끝까지 텍스트 생성을 완료하세요.
3. 절대로 프롬프트의 지시문 괄호 안내문(예: "이곳에 내용을 작성...")을 출력 결과에 포함하지 마세요.
4. PART 1은 개발자 밈을 섞어 유머러스하게 작성하세요.
5. PART 2는 명리학 용어를 사용하여 진지하게 오늘 하루를 분석하세요.
6. PART 3는 2026년 한 해의 총운을 작성하세요.

[출력 형식] (반드시 아래 마크다운 뼈대 그대로 내용만 채워 출력하세요)

## PART 1
### ⚡ 오늘 하루 개발자 총운
**별점:** ⭐⭐⭐⭐
(이곳에 오늘 하루의 총운 내용을 작성...)

### 🐛 오늘 하루 버그운
**별점:** ⭐⭐⭐
(이곳에 오늘 하루의 버그운 내용을 작성...)

### 🚀 오늘 하루 배포운
**별점:** ⭐⭐⭐⭐⭐
(이곳에 오늘 하루의 배포운 내용을 작성...)

### 🤝 오늘 하루 협업운
**별점:** ⭐⭐⭐
(이곳에 오늘 하루의 협업운 내용을 작성...)

### 🍀 오늘의 럭키 아이템
- **럭키 명령어:** `(명령어)`
- **럭키 기술:** (기술)
- **피해야 할 것:** (피할 것)
- **코딩 BGM:** (BGM 추천)

## PART 2
### 💰 오늘의 재물운 & 금전 흐름
(이곳에 오늘 하루의 재물운 내용을 작성...)

### ❤️ 오늘의 대인관계 & 연애운
(이곳에 오늘 하루의 연애운 내용을 작성...)

### 🌿 오늘의 건강 & 스트레스 관리
(이곳에 오늘 하루의 건강운 내용을 작성...){no_time_footer}

## PART 3
### 🗓️ 2026년 전체 흐름 & 핵심 키워드
(올해 가장 중요한 키워드 3가지를 **굵게** 표시하고 설명...)

### 📅 2026년 월별 주요 흐름
**상반기 (1월~6월):**
(상반기 흐름을 설명...)

**하반기 (7월~12월):**
(하반기 흐름을 설명...)

### ⚠️ 2026년 특히 주의해야 할 달
(주의해야 할 달과 이유를 설명...)

### 🌟 2026년 귀인 & 행운의 방향
(귀인과 행운의 요소를 설명...)

### 💼 2026년 커리어 & 재물 총운
(커리어와 재물 흐름을 설명...)

### 💌 2026년 연애 & 인간관계 총운
(연애와 인간관계 흐름을 설명...)
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

    prompt = build_prompt(name, birthday, role, birth_time)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=8192,
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
            # 이미 존재하는지 확인
            cur.execute(
                "SELECT id, nickname, created_at FROM users WHERE nickname = %s",
                (nickname,)
            )
            row = cur.fetchone()

            if row:
                # 기존 사용자
                return jsonify({
                    "status":    "existing",
                    "nickname":  row["nickname"],
                    "message":   f"다시 오셨군요, {nickname}님! 반갑습니다 👋",
                    "joined_at": row["created_at"].isoformat() if row["created_at"] else None,
                })
            else:
                # 신규 사용자 생성
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

        # datetime → 문자열 직렬화
        result = []
        for row in rows:
            row["saved_at"]  = row["saved_at"].strftime("%Y. %m. %d. %H:%M:%S") if row["saved_at"] else ""
            row["has_time"]  = bool(row["has_time"])
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
            # 본인 것만 삭제 가능하도록 nickname 조건 포함
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
