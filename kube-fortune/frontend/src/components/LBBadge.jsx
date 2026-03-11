import React from "react";

export default function LBBadge({ podName, loading }) {
  if (loading || !podName) {
    return (
      <div className="px-3 py-1 rounded-md bg-gray-800 border border-gray-700 text-xs text-gray-500 animate-pulse">
        파드 확인 중...
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-gray-800 border border-cyan-700 text-xs">
      <span className="text-cyan-400 font-mono">⚙</span>
      <span className="text-gray-400">현재 응답 파드:</span>
      <span className="text-cyan-300 font-mono font-bold">{podName}</span>
    </div>
  );
}
