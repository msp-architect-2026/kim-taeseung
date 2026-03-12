import { useState } from "react";
import FortuneCard from "./FortuneCard.jsx";

export default function SavedList({
  list,
  loading,
  error,
  isLoggedIn,
  onDelete,
  onEmpty,
  onLoginRequest,
}) {
  const [expandedId, setExpandedId] = useState(null);
  const [confirmId,  setConfirmId]  = useState(null);
  const [deleting,   setDeleting]   = useState(null);

  // 비로그인 상태
  if (!isLoggedIn) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
        <span className="text-6xl opacity-30">🔐</span>
        <p className="text-gray-400 text-sm font-semibold">보관함을 사용하려면 로그인이 필요합니다.</p>
        <p className="text-gray-600 text-xs">닉네임으로 간단하게 입장하면 운세가 DB에 저장됩니다.</p>
        <button
          onClick={onLoginRequest}
          className="mt-2 px-5 py-2 rounded-xl text-sm font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 transition-all"
        >
          🚀 로그인하기
        </button>
      </div>
    );
  }

  // 로딩 중
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <div className="text-4xl animate-spin">🔮</div>
        <p className="text-gray-500 text-sm">보관함을 불러오는 중...</p>
      </div>
    );
  }

  // 에러
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3 text-center">
        <span className="text-5xl opacity-40">⚠️</span>
        <p className="text-red-400 text-sm">{error}</p>
        <p className="text-gray-600 text-xs">DB 연결을 확인해 주세요.</p>
      </div>
    );
  }

  // 빈 보관함
  if (list.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
        <span className="text-6xl opacity-30">📭</span>
        <p className="text-gray-500 text-sm">저장된 운세가 없습니다.</p>
        <button
          onClick={onEmpty}
          className="mt-2 px-5 py-2 rounded-xl text-sm font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 transition-all"
        >
          ✨ 첫 운세 보러 가기
        </button>
      </div>
    );
  }

  const handleDelete = async (id) => {
    setDeleting(id);
    await onDelete(id);
    setDeleting(null);
    setConfirmId(null);
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-lg font-bold text-purple-300 flex items-center gap-2">
          <span>💾</span> 내 사주 보관함
        </h2>
        <span className="text-xs text-gray-500">총 {list.length}개 저장됨</span>
      </div>

      {list.map((item) => {
        const isOpen = expandedId === item.id;

        return (
          <div key={item.id} className="bg-gray-900 border border-gray-700 rounded-2xl overflow-hidden">

            {/* 요약 행 */}
            <div className="flex items-center justify-between px-5 py-4 gap-3 flex-wrap">
              <button
                onClick={() => setExpandedId(isOpen ? null : item.id)}
                className="flex items-center gap-3 text-left flex-1 min-w-0"
              >
                <span className="text-2xl flex-shrink-0">🔮</span>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-purple-200 truncate">
                    {item.name}
                    <span className="text-gray-500 font-normal ml-2 text-xs">
                      {item.role} 개발자
                    </span>
                  </p>
                  <p className="text-xs text-gray-500 truncate">🕓 {item.saved_at}</p>
                </div>
              </button>

              <div className="flex items-center gap-2 flex-shrink-0">
                {/* 펼치기/접기 */}
                <button
                  onClick={() => setExpandedId(isOpen ? null : item.id)}
                  className="text-xs text-gray-500 hover:text-purple-300 border border-gray-700 hover:border-purple-700 px-3 py-1.5 rounded-lg transition"
                >
                  {isOpen ? "▲ 접기" : "▼ 펼치기"}
                </button>

                {/* 삭제 */}
                {confirmId === item.id ? (
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleDelete(item.id)}
                      disabled={deleting === item.id}
                      className="text-xs text-red-300 border border-red-700 bg-red-900/30 hover:bg-red-800/40 px-3 py-1.5 rounded-lg transition disabled:opacity-50"
                    >
                      {deleting === item.id ? "삭제 중..." : "삭제 확인"}
                    </button>
                    <button
                      onClick={() => setConfirmId(null)}
                      className="text-xs text-gray-500 border border-gray-700 px-3 py-1.5 rounded-lg transition hover:text-gray-300"
                    >
                      취소
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setConfirmId(item.id)}
                    className="text-xs text-gray-600 hover:text-red-400 border border-gray-800 hover:border-red-800 px-3 py-1.5 rounded-lg transition"
                  >
                    🗑 삭제
                  </button>
                )}
              </div>
            </div>

            {/* 펼친 카드 */}
            {isOpen && (
              <div className="border-t border-gray-800 px-3 pb-3 pt-1">
                <FortuneCard
                  fortune={{
                    ...item,
                    fortune:  item.fortune,
                    has_time: item.has_time,
                    pod:      item.pod ?? "saved",
                  }}
                  savedAt={item.saved_at}
                  hideActions={true}
                  isLoggedIn={true}
                />
              </div>
            )}

          </div>
        );
      })}
    </div>
  );
}
