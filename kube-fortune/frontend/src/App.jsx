import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import MoodLamp from "./components/MoodLamp.jsx";
import LBBadge from "./components/LBBadge.jsx";
import FortuneCard from "./components/FortuneCard.jsx";
import SavedList from "./components/SavedList.jsx";

const ROLES = [
  "프론트엔드", "백엔드", "풀스택", "인프라/DevOps",
  "데이터 엔지니어", "AI/ML", "QA", "기획자(개발자 마음 아픔)",
];

const HOURS = Array.from({ length: 24 }, (_, i) =>
  String(i).padStart(2, "0") + "시"
);

// ════════════════════════════════════════════════════
// 로그인 모달
// ════════════════════════════════════════════════════
function LoginModal({ onLogin, onGuest }) {
  const [nick,    setNick]    = useState("");
  const [err,     setErr]     = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = nick.trim();
    if (!trimmed)           { setErr("닉네임을 입력해 주세요.");         return; }
    if (trimmed.length > 16){ setErr("닉네임은 16자 이내로 입력해 주세요."); return; }

    setLoading(true);
    setErr("");
    try {
      const { data } = await axios.post("/api/login", { nickname: trimmed });
      onLogin({ nick: trimmed, message: data.message, status: data.status });
    } catch (error) {
      const msg = error.response?.data?.error ?? "로그인 중 오류가 발생했습니다.";
      setErr(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-950/95 backdrop-blur px-4">
      <div className="w-full max-w-sm bg-gray-900 border border-purple-700 rounded-2xl p-8 shadow-2xl shadow-purple-900/40">

        <div className="flex flex-col items-center gap-2 mb-8">
          <span className="text-5xl">🔮</span>
          <h1 className="text-2xl font-extrabold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
            Kube-Fortune
          </h1>
          <p className="text-xs text-gray-500 text-center">
            개발자 맞춤형 AI 사주풀이 & 인프라 대시보드
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <label className="text-sm text-gray-400">닉네임</label>
          <input
            type="text"
            value={nick}
            onChange={(e) => { setNick(e.target.value); setErr(""); }}
            placeholder="예) 버그킬러김씨"
            maxLength={16}
            disabled={loading}
            className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2.5 text-gray-100 placeholder-gray-600 focus:outline-none focus:border-purple-500 transition disabled:opacity-50"
          />
          {err && <p className="text-xs text-red-400">⚠ {err}</p>}
          <button
            type="submit"
            disabled={loading}
            className="mt-1 py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-900/30"
          >
            {loading ? "⏳ 접속 중..." : "🚀 입장하기"}
          </button>
        </form>

        <button
          onClick={onGuest}
          disabled={loading}
          className="mt-3 w-full py-2 rounded-xl text-xs text-gray-500 hover:text-gray-300 border border-gray-800 hover:border-gray-600 transition disabled:opacity-40"
        >
          👀 로그인 없이 둘러보기
        </button>

      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════
// 메인 앱
// ════════════════════════════════════════════════════
export default function App() {

  // ── 유저 상태 ─────────────────────────────────────
  // user: null | { nick: string }
  const [user,      setUser]      = useState(null);
  const [showLogin, setShowLogin] = useState(true);
  const [loginMsg,  setLoginMsg]  = useState("");  // 환영 메시지 (잠깐 표시)

  const handleLogin = ({ nick, message }) => {
    setUser({ nick });
    setShowLogin(false);
    setLoginMsg(message);
    setTimeout(() => setLoginMsg(""), 3500);
  };
  const handleGuest  = () => setShowLogin(false);
  const handleLogout = () => {
    setUser(null);
    setShowLogin(true);
    setSavedList([]);
    setFortune(null);
  };

  // ── 보관함 상태 ───────────────────────────────────
  const [savedList,     setSavedList]     = useState([]);
  const [savedLoading,  setSavedLoading]  = useState(false);
  const [savedError,    setSavedError]    = useState("");

  const fetchSaved = useCallback(async (nickname) => {
    if (!nickname) return;
    setSavedLoading(true);
    setSavedError("");
    try {
      const { data } = await axios.get(`/api/fortunes/${encodeURIComponent(nickname)}`);
      setSavedList(data.fortunes || []);
    } catch (e) {
      setSavedError(e.response?.data?.error ?? "보관함을 불러오지 못했습니다.");
    } finally {
      setSavedLoading(false);
    }
  }, []);

  const handleSaveToDb = useCallback(async (fortune) => {
    if (!user) return { ok: false, msg: "로그인이 필요합니다." };
    try {
      await axios.post("/api/fortunes/save", {
        nickname:   user.nick,
        name:       fortune.name,
        role:       fortune.role,
        birthday:   fortune.birthday,
        birth_time: fortune.birth_time ?? null,
        fortune:    fortune.fortune,
        has_time:   fortune.has_time,
        pod:        fortune.pod,
      });
      // 보관함 탭이 열려있을 수도 있으니 목록 갱신
      await fetchSaved(user.nick);
      return { ok: true, msg: "보관함에 저장되었습니다! 💾" };
    } catch (e) {
      const msg = e.response?.data?.error ?? "저장 중 오류가 발생했습니다.";
      return { ok: false, msg };
    }
  }, [user, fetchSaved]);

  const handleDelete = useCallback(async (fortuneId) => {
    if (!user) return;
    try {
      await axios.delete(
        `/api/fortunes/${encodeURIComponent(user.nick)}/${fortuneId}`
      );
      setSavedList((prev) => prev.filter((i) => i.id !== fortuneId));
    } catch (e) {
      alert(e.response?.data?.error ?? "삭제 중 오류가 발생했습니다.");
    }
  }, [user]);

  // ── 탭 ────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState("new");

  const handleTabChange = (key) => {
    setActiveTab(key);
    // 보관함 탭 클릭 시 최신 데이터 로드
    if (key === "saved" && user) {
      fetchSaved(user.nick);
    }
  };

  // ── 인프라 상태 ───────────────────────────────────
  const [status,        setStatus]        = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const { data } = await axios.get("/api/status");
      setStatus(data);
    } catch (e) {
      console.error("Status fetch failed:", e);
    } finally {
      setStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 30_000);
    return () => clearInterval(timer);
  }, [fetchStatus]);

  // ── 운세 폼 ───────────────────────────────────────
  const [form, setForm] = useState({
    name: "", birthday: "", role: ROLES[0], birth_time: "",
  });
  const [timeUnknown,    setTimeUnknown]    = useState(false);
  const [fortune,        setFortune]        = useState(null);
  const [fortuneLoading, setFortuneLoading] = useState(false);
  const [error,          setError]          = useState("");

  const handleChange = (e) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleTimeUnknown = (e) => {
    setTimeUnknown(e.target.checked);
    if (e.target.checked) setForm((prev) => ({ ...prev, birth_time: "" }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { setError("이름을 입력해 주세요."); return; }
    if (!form.birthday)    { setError("생년월일을 입력해 주세요."); return; }
    setError("");
    setFortuneLoading(true);
    setFortune(null);

    const payload = {
      ...form,
      birth_time: timeUnknown ? null : form.birth_time || null,
    };
    try {
      const { data } = await axios.post("/api/fortune", payload);
      setFortune(data);
      fetchStatus();
    } catch (err) {
      setError(err.response?.data?.error ?? "운세 서버가 먹통입니다. 🔮💥");
    } finally {
      setFortuneLoading(false);
    }
  };

  // ── 렌더링 ────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">

      {/* 로그인 모달 */}
      {showLogin && <LoginModal onLogin={handleLogin} onGuest={handleGuest} />}

      {/* 환영 토스트 */}
      {loginMsg && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-40 bg-purple-900 border border-purple-500 text-purple-100 text-sm px-5 py-3 rounded-xl shadow-lg shadow-purple-900/50 transition-all">
          {loginMsg}
        </div>
      )}

      {/* ── 헤더 ── */}
      <header className="sticky top-0 z-10 bg-gray-950/90 backdrop-blur border-b border-gray-800 px-6 py-3">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🔮</span>
            <div>
              <h1 className="text-xl font-extrabold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                Kube-Fortune
              </h1>
              {user ? (
                <div className="flex items-center gap-2">
                  <p className="text-xs text-purple-400">👤 {user.nick}님 환영합니다</p>
                  <button
                    onClick={handleLogout}
                    className="text-xs text-gray-600 hover:text-gray-400 underline transition"
                  >
                    로그아웃
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowLogin(true)}
                  className="text-xs text-gray-500 hover:text-purple-400 underline transition"
                >
                  로그인하기
                </button>
              )}
            </div>
          </div>
          <MoodLamp status={status} loading={statusLoading} />
        </div>
      </header>

      {/* ── 탭 ── */}
      <div className="max-w-4xl mx-auto w-full px-4 pt-6">
        <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1">
          {[
            { key: "new",   label: "✨ 새 운세 보기" },
            { key: "saved", label: savedList.length > 0
                ? `💾 내 사주 보관함 (${savedList.length})`
                : "💾 내 사주 보관함" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => handleTabChange(tab.key)}
              className={[
                "flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200",
                activeTab === tab.key
                  ? "bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-900/30"
                  : "text-gray-500 hover:text-gray-300",
              ].join(" ")}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── 메인 ── */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-6">

        {/* 탭 1: 새 운세 */}
        {activeTab === "new" && (
          <>
            <section className="bg-gray-900 border border-gray-700 rounded-2xl p-6 shadow-xl">
              <h2 className="text-lg font-bold text-purple-300 mb-5 flex items-center gap-2">
                <span>✨</span> 오늘의 코딩 운세 확인
              </h2>

              <form onSubmit={handleSubmit} className="flex flex-col gap-4">

                {/* 이름 */}
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-gray-400">이름</label>
                  <input
                    type="text" name="name" value={form.name}
                    onChange={handleChange} placeholder="예) 홍길동"
                    className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-gray-100 placeholder-gray-600 focus:outline-none focus:border-purple-500 transition"
                  />
                </div>

                {/* 생년월일 */}
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-gray-400">생년월일</label>
                  <input
                    type="date" name="birthday" value={form.birthday}
                    onChange={handleChange}
                    className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-gray-100 focus:outline-none focus:border-purple-500 transition"
                  />
                </div>

                {/* 태어난 시간 */}
                <div className="flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm text-gray-400 flex items-center gap-1">
                      태어난 시간
                      <span className="text-xs text-amber-400 bg-amber-400/10 border border-amber-400/30 rounded px-1.5 py-0.5 ml-1">
                        ✦ 정밀도 향상
                      </span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox" checked={timeUnknown}
                        onChange={handleTimeUnknown}
                        className="w-3.5 h-3.5 accent-purple-500"
                      />
                      <span className="text-xs text-gray-500">시간을 모름</span>
                    </label>
                  </div>
                  <select
                    name="birth_time" value={form.birth_time}
                    onChange={handleChange} disabled={timeUnknown}
                    className={[
                      "bg-gray-800 border rounded-lg px-4 py-2 text-gray-100 focus:outline-none focus:border-purple-500 transition",
                      timeUnknown ? "border-gray-700 opacity-40 cursor-not-allowed" : "border-gray-600",
                    ].join(" ")}
                  >
                    <option value="">-- 태어난 시간 선택 --</option>
                    {HOURS.map((h) => <option key={h} value={h}>{h}</option>)}
                  </select>
                  <p className="text-xs text-gray-500 leading-relaxed">
                    {timeUnknown
                      ? "⚠ 시간 미입력 시 연월일 삼주(三柱) 기반으로 풀이됩니다."
                      : "🕐 태어난 시(時)는 재물·건강 풀이의 핵심 데이터입니다."}
                  </p>
                </div>

                {/* 직군 */}
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-gray-400">직군</label>
                  <select
                    name="role" value={form.role} onChange={handleChange}
                    className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-gray-100 focus:outline-none focus:border-purple-500 transition"
                  >
                    {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>

                {error && (
                  <p className="text-red-400 text-sm bg-red-950/40 border border-red-800 rounded-lg px-4 py-2">
                    ⚠ {error}
                  </p>
                )}

                <button
                  type="submit" disabled={fortuneLoading}
                  className="mt-1 py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-900/30"
                >
                  {fortuneLoading ? "🔮 점술가 채널 접속 중..." : "🔮 오늘의 운세 보기"}
                </button>

              </form>
            </section>

            {/* 운세 결과 카드 */}
            <FortuneCard
              fortune={fortune}
              loading={fortuneLoading}
              onSave={user ? handleSaveToDb : null}
              isLoggedIn={!!user}
            />

            {/* LB 새로고침 */}
            <div className="mt-8 flex justify-center">
              <button
                onClick={fetchStatus}
                className="text-xs text-gray-500 hover:text-cyan-400 border border-gray-700 hover:border-cyan-700 px-4 py-2 rounded-full transition"
              >
                🔄 파드 상태 새로고침 (LB 확인용)
              </button>
            </div>
          </>
        )}

        {/* 탭 2: 보관함 */}
        {activeTab === "saved" && (
          <SavedList
            list={savedList}
            loading={savedLoading}
            error={savedError}
            isLoggedIn={!!user}
            onDelete={handleDelete}
            onEmpty={() => setActiveTab("new")}
            onLoginRequest={() => setShowLogin(true)}
          />
        )}

      </main>

      {/* ── 푸터 ── */}
      <footer className="border-t border-gray-800 px-6 py-3">
        <div className="max-w-4xl mx-auto flex justify-between items-center flex-wrap gap-2">
          <span className="text-xs text-gray-600">
            Kube-Fortune © 2025 · Powered by Kubernetes & Gemini & MySQL
          </span>
          <LBBadge podName={status?.pod_name} loading={statusLoading} />
        </div>
      </footer>

    </div>
  );
}
