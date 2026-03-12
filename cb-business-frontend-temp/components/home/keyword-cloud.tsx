'use client';

import Link from 'next/link';
import { countriesByRegion } from '@/config/countries';
import type { CountryConfig } from '@/config/countries';

interface KeywordCloudProps {
  region: 'southeast_asia' | 'north_america' | 'latin_america';
}

// 平台关键词配置
const PLATFORMS_BY_REGION: Record<string, string[]> = {
  southeast_asia: ['Shopee', 'Lazada', 'TikTok Shop', 'Amazon'],
  north_america: ['Amazon', 'Shopify', 'eBay', 'Walmart'],
  latin_america: ['Mercado Libre', 'Amazon', 'Shopee', 'AliExpress'],
};

// 分类关键词
const CATEGORIES = [
  { label: '美妆', emoji: '💄' },
  { label: '电子', emoji: '📱' },
  { label: '家居', emoji: '🏠' },
  { label: '服饰', emoji: '👗' },
  { label: '食品', emoji: '🍜' },
  { label: '母婴', emoji: '👶' },
  { label: '运动', emoji: '⚽' },
  { label: '宠物', emoji: '🐕' },
];

// 区域颜色映射
const REGION_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  southeast_asia: {
    bg: 'bg-green-50',
    text: 'text-green-700',
    border: 'border-green-200 hover:border-green-300',
  },
  north_america: {
    bg: 'bg-purple-50',
    text: 'text-purple-700',
    border: 'border-purple-200 hover:border-purple-300',
  },
  latin_america: {
    bg: 'bg-orange-50',
    text: 'text-orange-700',
    border: 'border-orange-200 hover:border-orange-300',
  },
};

export function KeywordCloud({ region }: KeywordCloudProps) {
  const countries = countriesByRegion[region] || [];
  const platforms = PLATFORMS_BY_REGION[region] || [];
  const colors = REGION_COLORS[region] || REGION_COLORS.southeast_asia;

  return (
    <div className="space-y-4">
      {/* 国家标签 */}
      <div>
        <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
          <span>🌍</span>
          <span>国家/地区</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {countries.map((country: CountryConfig) => (
            <Link
              key={country.slug}
              href={`/${country.slug}`}
              className={`
                px-3 py-1.5 rounded-lg text-sm font-medium border
                ${colors.bg} ${colors.text} ${colors.border}
                transition-all duration-200 hover:shadow-sm hover:-translate-y-0.5
              `}
            >
              <span className="mr-1">{country.flag}</span>
              {country.name}
            </Link>
          ))}
        </div>
      </div>

      {/* 平台标签 */}
      <div>
        <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
          <span>🛒</span>
          <span>热门平台</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {platforms.map((platform) => (
            <button
              key={platform}
              className={`
                px-3 py-1.5 rounded-lg text-sm font-medium border
                bg-gray-50 text-gray-700 border-gray-200 hover:border-gray-300
                transition-all duration-200 hover:shadow-sm hover:-translate-y-0.5
              `}
              onClick={() => {
                window.location.href = `/search?q=${encodeURIComponent(platform)}`;
              }}
            >
              {platform}
            </button>
          ))}
        </div>
      </div>

      {/* 分类标签 */}
      <div>
        <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
          <span>📂</span>
          <span>品类</span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.label}
              className={`
                px-3 py-1.5 rounded-lg text-sm font-medium border
                bg-white text-gray-700 border-gray-200 hover:border-purple-200
                transition-all duration-200 hover:shadow-sm hover:-translate-y-0.5
              `}
              onClick={() => {
                window.location.href = `/search?q=${encodeURIComponent(cat.label)}`;
              }}
            >
              <span className="mr-1">{cat.emoji}</span>
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* 更多探索链接 */}
      <div className="pt-2 border-t border-gray-100">
        <Link
          href={`/${countries[0]?.slug || 'th'}`}
          className={`
            text-sm font-medium flex items-center gap-1
            ${colors.text} hover:underline
          `}
        >
          <span>探索更多</span>
          <span>→</span>
        </Link>
      </div>
    </div>
  );
}
