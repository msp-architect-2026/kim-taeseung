import React from "react";

const COLOR_MAP = {
  blue:  { bg: "bg-blue-900/40",  border: "border-blue-400",  text: "text-blue-300",  glow: "text-blue-400"  },
  green: { bg: "bg-green-900/40", border: "border-green-400", text: "text-green-300", glow: "text-green-400" },
  red:   { bg: "bg-red-900/40",   border: "border-red-400",   text: "text-red-300",   glow: "text-red-400"   },
  gray:  { bg: "bg-gray-800/40",  border: "border-gray-500",  text: "text-gray-300",  glow: "text-gray-400"  },
};

export default function MoodLamp({ status, loading }) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-gray-800 border border-gray-600 animate-pulse">
        <div className="w-3 h-3 rounded-full bg-gray-500" />
        <span className="text-sm text-gray-400">서버 상태 확인 중...</span>
      </div>
    );
  }

  if (!status) return null;

  const mood   = status.mood;
  const colors = COLOR_MAP[mood.color] ?? COLOR_MAP.gray;

  return (
    <div className={`flex items-center gap-3 px-5 py-2 rounded-full border ${colors.border} ${colors.bg} transition-all duration-700`}>
      <span className={`text-lg glow-animate ${colors.glow}`}>
        {mood.emoji}
      </span>
      <span className={`text-sm font-medium ${colors.text}`}>
        {mood.message}
      </span>
      {status.metrics_source !== "mock" && (
        <span className="text-xs text-gray-500 ml-1">
          ({status.cpu_millicores}m CPU)
        </span>
      )}
    </div>
  );
}
