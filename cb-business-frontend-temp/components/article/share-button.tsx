'use client';

export function ShareButton() {
  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
  };

  return (
    <button
      onClick={handleShare}
      className="inline-flex items-center gap-2 px-5 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium transition-colors"
    >
      <span>📋</span>
      <span>分享</span>
    </button>
  );
}
