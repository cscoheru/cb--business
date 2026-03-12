'use client';

import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Search, TrendingUp } from 'lucide-react';

// 快速过滤标签
const QUICK_FILTERS = [
  { label: '美妆', emoji: '💄' },
  { label: '电子', emoji: '📱' },
  { label: '家居', emoji: '🏠' },
  { label: 'Shopee', emoji: '🛒' },
  { label: '亚马逊', emoji: '📦' },
  { label: 'TikTok Shop', emoji: '🎵' },
];

export function HeroSearch() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<string | null>(null);

  const handleSearch = (e: FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleFilterClick = (filter: string) => {
    setActiveFilter(filter);
    router.push(`/search?q=${encodeURIComponent(filter)}`);
  };

  return (
    <section className="relative overflow-hidden">
      {/* 异域浪漫渐变背景 */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          background: 'linear-gradient(135deg, #90EE90 0%, #FFB347 50%, #DDA0DD 100%)',
        }}
      />

      {/* 装饰性圆形元素 */}
      <div className="absolute top-10 left-10 w-32 h-32 rounded-full bg-green-200/30 blur-3xl" />
      <div className="absolute bottom-10 right-10 w-40 h-40 rounded-full bg-purple-200/30 blur-3xl" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full bg-orange-200/20 blur-3xl" />

      {/* 主内容 */}
      <div className="relative max-w-4xl mx-auto px-4 py-16 md:py-24">
        {/* 标题 */}
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-5xl font-bold text-gray-900 mb-4">
            探索跨境电商新世界
          </h1>
          <p className="text-base md:text-lg text-gray-600">
            智能资讯聚合，助你发现东南亚、欧美、拉美市场机遇
          </p>
        </div>

        {/* 搜索框 */}
        <form onSubmit={handleSearch} className="mb-6">
          <div className="relative max-w-2xl mx-auto">
            <div className="flex items-center bg-white rounded-full shadow-lg border-2 border-gray-100 hover:border-purple-200 focus-within:border-purple-300 transition-all duration-300">
              <div className="pl-5">
                <Search className="w-5 h-5 text-gray-400" />
              </div>
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索关键词、国家、平台或主题..."
                className="flex-1 px-4 py-4 text-gray-900 placeholder-gray-400 focus:outline-none bg-transparent"
              />
              <button
                type="submit"
                className="mr-1 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full font-medium hover:from-purple-600 hover:to-pink-600 transition-all duration-300 shadow-md hover:shadow-lg"
              >
                搜索
              </button>
            </div>
          </div>
        </form>

        {/* 快速过滤标签 */}
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">热门搜索</span>
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            {QUICK_FILTERS.map((filter) => (
              <button
                key={filter.label}
                onClick={() => handleFilterClick(filter.label)}
                className={`
                  px-4 py-2 rounded-full text-sm font-medium transition-all duration-200
                  ${activeFilter === filter.label
                    ? 'bg-white shadow-md text-purple-600 scale-105'
                    : 'bg-white/70 text-gray-700 hover:bg-white hover:shadow-sm hover:scale-102'
                  }
                `}
              >
                <span className="mr-1">{filter.emoji}</span>
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        {/* 快速链接 */}
        <div className="mt-10 flex flex-wrap justify-center gap-4 text-sm">
          <Link
            href="/th"
            className="flex items-center gap-2 px-4 py-2 bg-white/70 rounded-full text-gray-700 hover:bg-white hover:shadow-md transition-all"
          >
            <span>🌏</span>
            <span>东南亚</span>
          </Link>
          <Link
            href="/us"
            className="flex items-center gap-2 px-4 py-2 bg-white/70 rounded-full text-gray-700 hover:bg-white hover:shadow-md transition-all"
          >
            <span>🇺🇸</span>
            <span>欧美</span>
          </Link>
          <Link
            href="/br"
            className="flex items-center gap-2 px-4 py-2 bg-white/70 rounded-full text-gray-700 hover:bg-white hover:shadow-md transition-all"
          >
            <span>🇧🇷</span>
            <span>拉美</span>
          </Link>
          <Link
            href="/assessment"
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full text-white hover:shadow-md transition-all"
          >
            <span>🪞</span>
            <span>能力评估</span>
          </Link>
        </div>
      </div>
    </section>
  );
}
