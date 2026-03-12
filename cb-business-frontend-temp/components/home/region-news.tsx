'use client';

import Link from 'next/link';
import { articlesApi, Article } from '@/lib/api';
import { countriesByRegion } from '@/config/countries';
import { KeywordCloud } from './keyword-cloud';

interface RegionNewsProps {
  initialArticles: Article[];
}

const regions = [
  {
    key: 'southeast_asia',
    name: '东南亚',
    emoji: '🌏',
    color: 'purple',
    countries: countriesByRegion.southeast_asia,
  },
  {
    key: 'north_america',
    name: '欧美',
    emoji: '🇺🇸',
    color: 'blue',
    countries: countriesByRegion.north_america,
  },
  {
    key: 'latin_america',
    name: '拉美',
    emoji: '🇧🇷',
    color: 'green',
    countries: countriesByRegion.latin_america,
  },
];

function formatTime(dateString: string | null) {
  if (!dateString) return '未知时间';
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);

  if (hours < 1) return '刚刚';
  if (hours < 24) return `${hours}小时前`;
  if (days === 1) return '昨天';
  if (days < 7) return `${days}天前`;
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
}

export function RegionNews({ initialArticles }: RegionNewsProps) {
  return (
    <section className="max-w-7xl mx-auto px-4 py-6">
      <div className="grid lg:grid-cols-3 gap-4">
        {regions.map((region) => {
          // 筛选当前区域的文章（后端暂不支持按国家筛选）
          const regionArticles = initialArticles.filter(article => {
            return article.region === region.key;
          });

          return (
            <div key={region.key} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              {/* 头部 */}
              <div className="px-4 py-3 border-b border-gray-200">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{region.emoji}</span>
                    <span className="font-semibold text-gray-900">{region.name}</span>
                  </div>
                  <span className="text-xs text-gray-500">
                    {regionArticles.length} 篇资讯
                  </span>
                </div>
              </div>

              {/* 关键词云 */}
              <div className="px-4 py-3 bg-gradient-to-b from-gray-50 to-white border-b border-gray-100">
                <KeywordCloud region={region.key as 'southeast_asia' | 'north_america' | 'latin_america'} />
              </div>

              {/* 最新资讯列表（仅显示前3条） */}
              <div className="p-3">
                <div className="text-xs text-gray-500 mb-2">最新资讯</div>
                <div className="space-y-1">
                  {regionArticles.length === 0 ? (
                    <div className="text-center py-4 text-gray-400 text-sm">
                      <p>📝 整理中...</p>
                    </div>
                  ) : (
                    regionArticles.slice(0, 3).map((article) => (
                      <Link
                        key={article.id}
                        href={`/articles/${article.id}`}
                        className="flex items-start gap-2 py-1.5 px-2 rounded cursor-pointer block transition-colors hover:bg-gray-50"
                      >
                        <span className="text-xs text-gray-400 mt-0.5 whitespace-nowrap">
                          {formatTime(article.published_at)}
                        </span>
                        <span className="text-sm text-gray-700 hover:text-blue-600 flex-1 line-clamp-1">
                          {article.title}
                        </span>
                      </Link>
                    ))
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
