import { useState } from "react";

// ── 공통 배경 클래스 (전체 섹션 통일) ─────────────────
const SECTION_BG = "bg-gradient-to-br from-purple-950/60 to-indigo-950/60";

// ── PART 1 / 2 / 3 분리 파서 ──────────────────────────
function splitFortuneParts(text) {
  const p1Idx = text.search(/^##\s*PART\s*1/im);
  const p2Idx = text.search(/^##\s*PART\s*2/im);
  const p3Idx = text.search(/^##\s*PART\s*3/im);

  if (p1Idx === -1 && p2Idx === -1) {
    return { part1: text, part2: null, part3: null };
  }

  const s1 = p1Idx !== -1 ? p1Idx : 0;
  const s2 = p2Idx !== -1 ? p2Idx : null;
  const s3 = p3Idx !== -1 ? p3Idx : null;

  const part1 = s2 !== null ? text.slice(s1, s2).trim() : text.slice(s1).trim();
  const part2 = s2 !== null
    ? (s3 !== null ? text.slice(s2, s3).trim() : text.slice(s2).trim())
    : null;
  const part3 = s3 !== null ? text.slice(s3).trim() : null;

  return { part1, part2, part3 };
}

function stripPartHeader(text) {
  return text.replace(/^##\s*PART\s*\d+[^\n]*\n*/im, "").trim();
}

// ── 마크다운 → HTML 변환 ──────────────────────────────
function renderMarkdown(text) {
  return text
    .replace(/^###\s(.+)$/gm,
      "<h4 class='text-sm font-bold text-purple-200 mt-5 mb-2'>$1</h4>")
    .replace(/\*\*(.*?)\*\*/g,
      "<strong class='text-purple-100 font-semibold'>$1</strong>")
    .replace(/`([^`]+)`/g,
      "<code class='bg-gray-800 text-cyan-300 px-1.5 py-0.5 rounded text-xs font-mono'>$1</code>")
    .replace(/^>\s(.+)$/gm,
      "<blockquote class='border-l-2 border-purple-500 pl-3 text-gray-400 italic text-xs my-1'>$1</blockquote>")
    .replace(/^-\s(.+)$/gm,
      "<li class='ml-4 text-gray-300 list-disc list-outside text-sm'>$1</li>")
    .replace(/\n/g, "<br/>");
}

// ── 로딩 스켈레톤 ─────────────────────────────────────
function LoadingSkeleton() {
  return (
    <div className="w-full max-w-2xl mx-auto mt-6 p-6 rounded-2xl bg-purple-950/50 border border-purple-700 animate-pulse">
      <div className="flex flex-col gap-3 items-center">
        <div className="text-5xl animate-spin">🔮</div>
        <p className="text-purple-300 text-sm font-semibold">점술가가 천기를 살피는 중입니다...</p>
        <p className="text-gray-500 text-xs">상세한 풀이를 준비 중이라 시간이 조금 걸려요</p>
        <div className="w-full space-y-2 mt-3">
          {[0.75, 1, 0.67, 1, 0.8, 1, 0.6].map((w, i) => (
            <div key={i} className="h-3 bg-purple-800/60 rounded"
              style={{ width: `${w * 100}%` }} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── 구분 Divider ──────────────────────────────────────
// flexbox 양쪽 라인 방식 → 배경색과 무관하게 항상 깔끔하게 표시됨
function PremiumDivider({ label, color = "amber" }) {
  const styles = {
    amber:  { line: "border-amber-500/40",  badge: "from-amber-500/20 to-yellow-500/20 border-amber-500/40 text-amber-300" },
    yellow: { line: "border-yellow-500/40", badge: "from-yellow-500/20 to-orange-500/20 border-yellow-500/40 text-yellow-300" },
  };
  const s = styles[color] || styles.amber;

  return (
    <div className={`${SECTION_BG} flex items-center gap-3 px-6 py-3`}>
      <div className={`flex-1 border-t ${s.line}`} />
      <span className={`flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-gradient-to-r ${s.badge} border`}>
        {label}
      </span>
      <div className={`flex-1 border-t ${s.line}`} />
    </div>
  );
}

// ── PART 1 섹션 ───────────────────────────────────────
function Part1Section({ content }) {
  return (
    <div className={`${SECTION_BG} px-6 py-5`}>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">🖥️</span>
        <span className="text-sm font-bold text-purple-300 tracking-wide">오늘의 개발자 운세</span>
      </div>
      <div className="text-gray-200 text-sm leading-7"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }} />
    </div>
  );
}

// ── PART 2 섹션 ───────────────────────────────────────
function Part2Section({ content, hasTime }) {
  return (
    <div className={`${SECTION_BG} px-6 py-5`}>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">🔮</span>
        <span className="text-sm font-bold text-amber-300 tracking-wide">오늘의 프리미엄 사주 풀이</span>
        <span className="ml-auto text-xs text-amber-400 bg-amber-400/10 border border-amber-400/30 rounded-full px-2 py-0.5">
          ✨ Premium
        </span>
      </div>
      {!hasTime && (
        <div className="mb-4 flex items-start gap-2 text-xs text-amber-400/80 bg-amber-400/5 border border-amber-400/20 rounded-lg px-3 py-2">
          <span className="mt-0.5 flex-shrink-0">⚠</span>
          <span>태어난 시간 미입력 — 연월일 삼주(三柱) 기반 풀이입니다. 시간 입력 시 더 정밀한 풀이를 받을 수 있습니다.</span>
        </div>
      )}
      <div className="text-gray-200 text-sm leading-7"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }} />
    </div>
  );
}

// ── PART 3 섹션 ───────────────────────────────────────
function Part3Section({ content }) {
  return (
    <div className={`${SECTION_BG} px-6 py-5`}>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">🌟</span>
        <span className="text-sm font-bold text-yellow-300 tracking-wide">2026년 프리미엄 올해 총운</span>
        <span className="ml-auto text-xs text-yellow-400 bg-yellow-400/10 border border-yellow-400/30 rounded-full px-2 py-0.5">
          ✨ Premium+
        </span>
      </div>
      <div className="text-gray-200 text-sm leading-7"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }} />
    </div>
  );
}

// ── 범용 해금 버튼 ────────────────────────────────────
function UnlockButton({ onClick, variant = "yearly" }) {
  const config = {
    premium: {
      hint:     "✦ 명리학 기반 오늘의 심층 풀이가 준비되어 있습니다 ✦",
      sub:      "재물운 · 대인관계 · 건강 & 스트레스",
      icon:     "✨",
      label:    "오늘의 프리미엄 사주 풀이 보기",
      gradient: "from-purple-600 via-amber-500 to-purple-600 hover:from-purple-500 hover:via-amber-400 hover:to-purple-500",
      shadow:   "shadow-purple-500/30 hover:shadow-purple-400/50",
    },
    yearly: {
      hint:     "✦ 아직 확인하지 않은 운세가 있습니다 ✦",
      sub:      "올해 흐름 · 주의할 달 · 귀인 · 커리어 총운",
      icon:     "🌟",
      label:    "2026년 프리미엄 올해 총운 보기",
      gradient: "from-amber-500 via-yellow-400 to-amber-500 hover:from-amber-400 hover:via-yellow-300 hover:to-amber-400",
      shadow:   "shadow-amber-500/30 hover:shadow-amber-400/50",
    },
  };
  const c = config[variant];

  return (
    <div className={`${SECTION_BG} px-6 py-6 flex flex-col items-center gap-3`}>
      <p className="text-xs text-purple-400/70 text-center">{c.hint}</p>
      <button
        onClick={onClick}
        className={`relative group w-full max-w-xs py-3.5 px-6 rounded-2xl font-bold text-sm text-white bg-gradient-to-r ${c.gradient} shadow-lg ${c.shadow} transition-all duration-300 overflow-hidden`}
      >
        <span className="absolute inset-0 rounded-2xl bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
        <span className="relative flex items-center justify-center gap-2">
          <span className="text-base">{c.icon}</span>
          <span>{c.label}</span>
          <span className="text-base">{c.icon}</span>
        </span>
      </button>
      <p className="text-xs text-purple-500/60">{c.sub}</p>
    </div>
  );
}

// ── 저장 버튼 ─────────────────────────────────────────
function SaveButton({ saveState, saveMsg, onSave, isLoggedIn }) {
  if (!isLoggedIn) {
    return (
      <span className="text-xs text-purple-700 italic">
        💡 로그인하면 보관함에 저장할 수 있어요
      </span>
    );
  }

  const base = "flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-200";

  if (saveState === "saving") {
    return (
      <button disabled className={`${base} bg-purple-900/20 border-purple-700 text-purple-400 cursor-not-allowed`}>
        ⏳ 저장 중...
      </button>
    );
  }
  if (saveState === "saved") {
    return (
      <button disabled className={`${base} bg-green-900/30 border-green-700 text-green-400 cursor-default`}>
        ✅ 보관함에 저장됨
      </button>
    );
  }
  if (saveState === "error") {
    return (
      <div className="flex flex-col gap-1">
        <button onClick={onSave} className={`${base} bg-red-900/30 border-red-700 text-red-300 hover:bg-red-800/40`}>
          ❌ 저장 실패 — 다시 시도
        </button>
        {saveMsg && <span className="text-xs text-red-400">{saveMsg}</span>}
      </div>
    );
  }
  return (
    <button onClick={onSave} className={`${base} bg-purple-900/30 border-purple-600 text-purple-300 hover:bg-purple-800/40 hover:text-white`}>
      💾 보관함에 저장
    </button>
  );
}

// ── 운세 카드 본체 ────────────────────────────────────
function FortuneContent({ fortune, onSave, savedAt, hideActions, isLoggedIn }) {
  const [saveState, setSaveState] = useState("idle");
  const [saveMsg,   setSaveMsg]   = useState("");
  const [showPart2, setShowPart2] = useState(false);
  const [showPart3, setShowPart3] = useState(false);

  const { part1, part2, part3 } = splitFortuneParts(fortune.fortune);

  const handleSave = async () => {
    if (saveState === "saving" || saveState === "saved" || !onSave) return;
    setSaveState("saving");
    setSaveMsg("");
    const result = await onSave(fortune);
    if (result.ok) {
      setSaveState("saved");
    } else {
      setSaveState("error");
      setSaveMsg(result.msg);
    }
  };

  return (
    <div className="rounded-2xl border border-purple-600 shadow-xl shadow-purple-900/30 overflow-hidden">

      {/* 카드 헤더 */}
      <div className="bg-gradient-to-r from-purple-950/90 to-indigo-950/90 px-6 pt-6 pb-4 border-b border-purple-800/50">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <span className="text-4xl">🔮</span>
            <div>
              <h3 className="text-purple-100 font-bold text-xl">{fortune.name}님의 운세</h3>
              <p className="text-purple-400 text-xs mt-0.5">{fortune.role} 개발자</p>
            </div>
          </div>
          {savedAt && (
            <span className="text-xs text-purple-700 font-mono self-center">🕓 {savedAt}</span>
          )}
        </div>
      </div>

      {/* PART 1 */}
      {part1 && <Part1Section content={stripPartHeader(part1)} />}

      {/* PART 2 흐름 */}
      {part2 && (
        showPart2 ? (
          <>
            <PremiumDivider label="✨ Premium Fortune — 오늘의 사주 풀이" color="amber" />
            <div style={{ animation: "fadeSlideIn 0.45s ease-out" }}>
              <Part2Section content={stripPartHeader(part2)} hasTime={fortune.has_time} />
            </div>

            {/* PART 3 흐름 */}
            {part3 && (
              showPart3 ? (
                <>
                  <PremiumDivider label="🌟 Premium+ — 2026년 올해 총운" color="yellow" />
                  <div style={{ animation: "fadeSlideIn 0.45s ease-out" }}>
                    <Part3Section content={stripPartHeader(part3)} />
                  </div>
                </>
              ) : (
                <UnlockButton variant="yearly" onClick={() => setShowPart3(true)} />
              )
            )}
          </>
        ) : (
          <UnlockButton variant="premium" onClick={() => setShowPart2(true)} />
        )
      )}

      {/* 카드 푸터 */}
      <div className={`${SECTION_BG} px-6 py-3 border-t border-purple-800/40 flex items-center justify-between gap-3 flex-wrap`}>
        {!hideActions && (
          <SaveButton
            saveState={saveState}
            saveMsg={saveMsg}
            onSave={handleSave}
            isLoggedIn={isLoggedIn}
          />
        )}
        <span className="text-xs text-purple-800 font-mono ml-auto">
          ✦ served by {fortune.pod}
        </span>
      </div>

    </div>
  );
}

// ── 외부 래퍼 ────────────────────────────────────────
export default function FortuneCard({
  fortune,
  loading,
  onSave,
  savedAt,
  hideActions = false,
  isLoggedIn  = false,
}) {
  if (loading)  return <LoadingSkeleton />;
  if (!fortune) return null;

  return (
    <div className="w-full max-w-2xl mx-auto mt-6">
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(-10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
      <FortuneContent
        fortune={fortune}
        onSave={onSave}
        savedAt={savedAt}
        hideActions={hideActions}
        isLoggedIn={isLoggedIn}
      />
    </div>
  );
}
