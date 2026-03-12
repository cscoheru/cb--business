'use client';

import { useRouter, useSearchParams } from 'next/navigation';

interface ThemeFilterClientProps {
  currentTheme: string;
  currentRegion?: string;
  currentSort?: string;
  articleCount: number;
}

const REGIONS = [
  { key: '', label: '全部区域', emoji: '🌍' },
  { key: 'southeast_asia', label: '东南亚', emoji: '🌏' },
  { key: 'north_america', label: '欧美', emoji: '🇺🇸' },
  { key: 'latin_america', label: '拉美', emoji: '🇧🇷' },
];

const SORT_OPTIONS = [
  { key: '', label: '最新发布' },
  { key: 'oldest', label: '最早发布' },
];

export function ThemeFilterClient({
  currentTheme,
  currentRegion,
  currentSort,
  articleCount,
}: ThemeFilterClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    router.push(`?${params.toString()}`, { scroll: false });
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* 区域筛选 */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-500">区域:</span>
        <div className="flex gap-1">
          {REGIONS.map((region) => (
            <button
              key={region.key}
              onClick={() => updateFilter('region', region.key)}
              className={`
                px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                ${currentRegion === region.key
                  ? 'bg-gray-900 text-white shadow-sm'
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

      {/* 排序选项 */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-500">排序:</span>
        <div className="flex gap-1">
          {SORT_OPTIONS.map((sort) => (
            <button
              key={sort.key}
              onClick={() => updateFilter('sort', sort.key)}
              className={`
                px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                ${currentSort === sort.key
                  ? 'bg-gray-900 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }
              `}
            >
              {sort.label}
            </button>
          ))}
        </div>
      </div>

      <div className="ml-auto text-xs text-gray-500">
        共 <span className="font-semibold text-gray-700">{articleCount}</span> 篇
      </div>
    </div>
  );
}
