'use client';

import { useRouter, useSearchParams } from 'next/navigation';

interface SearchFilterBarProps {
  regionFilter: string;
  themeFilter: string;
  sortBy: 'latest' | 'oldest' | 'relevance';
  onRegionChange: (value: string) => void;
  onThemeChange: (value: string) => void;
  onSortChange: (value: 'latest' | 'oldest' | 'relevance') => void;
}

const REGIONS = [
  { key: '', label: '全部区域', emoji: '🌍' },
  { key: 'southeast_asia', label: '东南亚', emoji: '🌏' },
  { key: 'north_america', label: '欧美', emoji: '🇺🇸' },
  { key: 'latin_america', label: '拉美', emoji: '🇧🇷' },
];

const THEMES = [
  { key: '', label: '全部主题', emoji: '📂' },
  { key: 'policy', label: '政策', emoji: '📜' },
  { key: 'opportunity', label: '机会', emoji: '💡' },
  { key: 'risk', label: '风险', emoji: '⚠️' },
  { key: 'guide', label: '实操', emoji: '📊' },
  { key: 'platform', label: '平台', emoji: '🛒' },
  { key: 'logistics', label: '物流', emoji: '🚚' },
];

const SORT_OPTIONS = [
  { key: 'relevance', label: '相关度' },
  { key: 'latest', label: '最新' },
  { key: 'oldest', label: '最早' },
];

export function SearchFilterBar({
  regionFilter,
  themeFilter,
  sortBy,
  onRegionChange,
  onThemeChange,
  onSortChange,
}: SearchFilterBarProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
      <div className="flex flex-wrap items-center gap-4">
        {/* 区域筛选 */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-medium">区域:</span>
          <div className="flex gap-1">
            {REGIONS.map((region) => (
              <button
                key={region.key}
                onClick={() => onRegionChange(region.key)}
                className={`
                  px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                  ${regionFilter === region.key
                    ? 'bg-purple-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }
                `}
              >
                <span className="mr-1">{region.emoji}</span>
                {region.label}
              </button>
            ))}
          </div>
        </div>

        <div className="w-px h-6 bg-gray-200" />

        {/* 主题筛选 */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-medium">主题:</span>
          <div className="flex gap-1">
            {THEMES.map((theme) => (
              <button
                key={theme.key}
                onClick={() => onThemeChange(theme.key)}
                className={`
                  px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                  ${themeFilter === theme.key
                    ? 'bg-purple-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }
                `}
              >
                <span className="mr-1">{theme.emoji}</span>
                {theme.label}
              </button>
            ))}
          </div>
        </div>

        <div className="w-px h-6 bg-gray-200" />

        {/* 排序选项 */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-medium">排序:</span>
          <div className="flex gap-1">
            {SORT_OPTIONS.map((sort) => (
              <button
                key={sort.key}
                onClick={() => onSortChange(sort.key as any)}
                className={`
                  px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                  ${sortBy === sort.key
                    ? 'bg-purple-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }
                `}
              >
                {sort.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
