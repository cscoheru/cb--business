'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import type { Article } from '@/lib/api';
import { Card } from '@/components/ui/card';

interface ThemePortalsProps {
  articles: Article[];
}

// 6个主题门户定义
const THEME_PORTALS = [
  { key: 'policy', label: '政策中心', description: '各国电商政策法规解读', emoji: '📜', color: '#eab308' },
  { key: 'opportunity', label: '机会发现', description: '市场机会、选品建议', emoji: '💡', color: '#22c55e' },
  { key: 'risk', label: '风险预警', description: '市场风险、运营陷阱', emoji: '⚠️', color: '#ef4444' },
  { key: 'guide', label: '实操指南', description: '开店流程、运营技巧', emoji: '📊', color: '#3b82f6' },
  { key: 'platform', label: '平台指南', description: '各大平台入驻、运营', emoji: '🛒', color: '#a855f7' },
  { key: 'logistics', label: '物流参考', description: '国际物流、仓储方案', emoji: '🚚', color: '#f97316' },
] as const;

// 区域图标映射
const regionEmojis: Record<string, string> = {
  southeast_asia: '🌏',
  north_america: '🇺🇸',
  latin_america: '🇧🇷',
};

// 主题颜色样式映射
const THEME_STYLES: Record<string, { bg: string; text: string; border: string; badge: string }> = {
  policy: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200', badge: 'badge-policy' },
  opportunity: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200', badge: 'badge-opportunity' },
  risk: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', badge: 'badge-risk' },
  guide: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', badge: 'badge-guide' },
  platform: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', badge: 'badge-platform' },
  logistics: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', badge: 'badge-logistics' },
};

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

export function ThemePortals({ articles }: ThemePortalsProps) {
  const [activeTab, setActiveTab] = useState('policy');

  // 按主题筛选文章
  const getArticlesByTheme = (theme: string) => {
    return articles.filter(a => a.content_theme === theme);
  };

  return (
    <section className="max-w-7xl mx-auto px-4 py-8">
      {/* 标题 */}
      <div className="text-center mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-2">专业信息门户</h2>
        <p className="text-sm text-gray-600">探索跨境电商的全方位知识体系</p>
      </div>

      {/* 水平标签导航 */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} orientation="horizontal">
          {/* 标签栏 */}
          <div className="border-b border-gray-200 bg-gray-50/50">
            <TabsList
              variant="line"
              className="w-full justify-start border-b-0 bg-transparent h-auto p-0"
            >
              {THEME_PORTALS.map((portal) => {
                const count = getArticlesByTheme(portal.key).length;
                return (
                  <TabsTrigger
                    key={portal.key}
                    value={portal.key}
                    className={`
                      relative px-5 py-4 text-sm font-medium whitespace-nowrap
                      data-active:border-b-2 data-active:border-current
                      ${activeTab === portal.key ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'}
                    `}
                  >
                    <span className="mr-2 text-lg">{portal.emoji}</span>
                    <span>{portal.label}</span>
                    <span className="ml-2 text-xs bg-white text-gray-500 px-2 py-0.5 rounded-full shadow-sm border border-gray-200">
                      {count}
                    </span>
                  </TabsTrigger>
                );
              })}
            </TabsList>
          </div>

          {/* 标签内容 */}
          {THEME_PORTALS.map((portal) => {
            const portalArticles = getArticlesByTheme(portal.key);
            const styles = THEME_STYLES[portal.key] || THEME_STYLES.policy;

            return (
              <TabsContent key={portal.key} value={portal.key} className="mt-0 p-6">
                {/* 描述 */}
                <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-100">
                  <span className="text-3xl">{portal.emoji}</span>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{portal.label}</h3>
                    <p className="text-sm text-gray-500">{portal.description}</p>
                  </div>
                </div>

                {/* 文章列表 */}
                {portalArticles.length > 0 ? (
                  <div className="grid md:grid-cols-2 gap-3">
                    {portalArticles.slice(0, 8).map((article) => (
                      <Link key={article.id} href={`/articles/${article.id}`}>
                        <Card className="p-4 hover:shadow-md transition cursor-pointer border-l-4" style={{ borderLeftColor: portal.color }}>
                          <div className="flex items-start gap-3">
                            <span className="text-xl">{regionEmojis[article.region || ''] || '📰'}</span>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className={`text-xs px-2 py-0.5 rounded ${styles.bg} ${styles.text} ${styles.border} border`}>
                                  {article.region === 'southeast_asia' ? '东南亚' :
                                   article.region === 'north_america' ? '欧美' :
                                   article.region === 'latin_america' ? '拉美' : '全球'}
                                </span>
                                <span className="text-xs text-gray-500">
                                  {formatTime(article.published_at)}
                                </span>
                              </div>
                              <h4 className="font-medium text-gray-900 mb-1 hover:text-blue-600 line-clamp-2">
                                {article.title}
                              </h4>
                              <p className="text-xs text-gray-500 line-clamp-2">
                                {article.summary}
                              </p>
                              <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
                                <span>{article.source}</span>
                              </div>
                            </div>
                          </div>
                        </Card>
                      </Link>
                    ))}
                  </div>
                ) : (
                  /* 空状态 */
                  <div className="text-center py-16">
                    <div className="text-gray-300 mb-3">
                      <span className="text-5xl opacity-50">{portal.emoji}</span>
                    </div>
                    <p className="text-gray-500 mb-1">暂无{portal.label}内容</p>
                    <p className="text-sm text-gray-400">我们正在整理相关信息，敬请期待</p>
                  </div>
                )}

                {/* 查看更多链接 */}
                {portalArticles.length > 8 && (
                  <div className="mt-6 text-center">
                    <Link
                      href={`/theme/${portal.key}`}
                      className="inline-flex items-center gap-2 px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
                    >
                      <span>查看全部 {portalArticles.length} 篇</span>
                      <span>→</span>
                    </Link>
                  </div>
                )}
              </TabsContent>
            );
          })}
        </Tabs>
      </div>

      {/* 快速链接 - 当所有主题都有内容时显示 */}
      <div className="mt-6 text-center">
        <div className="text-xs text-gray-500 mb-3">按主题快速筛选</div>
        <div className="flex flex-wrap justify-center gap-2">
          {THEME_PORTALS.map((portal) => {
            const count = getArticlesByTheme(portal.key).length;
            if (count === 0) return null;
            return (
              <Link
                key={portal.key}
                href={`/theme/${portal.key}`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-full text-xs text-gray-600 hover:border-gray-300 hover:text-gray-900 hover:shadow-sm transition-all"
              >
                <span>{portal.emoji}</span>
                <span>{portal.label}</span>
                <span className="bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">{count}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </section>
  );
}
