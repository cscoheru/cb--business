'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import type { Article } from '@/lib/api';
import type { CountryConfig } from '@/config/countries/types';
import { Card } from '@/components/ui/card';

interface CountryPortalTabsProps {
  country: CountryConfig;
  articles: Article[];
}

// 6个标签定义
const TABS = [
  { key: 'policy', label: '政策中心', emoji: '📜', theme: 'policy' },
  { key: 'opportunity', label: '机会发现', emoji: '💡', theme: 'opportunity' },
  { key: 'risk', label: '风险预警', emoji: '⚠️', theme: 'risk' },
  { key: 'guide', label: '实操指南', emoji: '📊', theme: 'guide' },
  { key: 'platform', label: '平台指南', emoji: '🛒', theme: 'platform' },
  { key: 'logistics', label: '物流参考', emoji: '🚚', theme: 'logistics' },
] as const;

// 标签颜色映射
const TAB_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  policy: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  opportunity: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
  risk: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  guide: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  platform: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' },
  logistics: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
};

export function CountryPortalTabs({ country, articles }: CountryPortalTabsProps) {
  const [activeTab, setActiveTab] = useState('policy');

  // 按主题筛选文章
  const getArticlesByTheme = (theme: string) => {
    if (theme === 'platform' || theme === 'logistics') {
      // 平台和物流标签显示平台信息而非文章
      return [];
    }
    return articles.filter(a => a.content_theme === theme);
  };

  const formatTime = (dateString: string | null) => {
    if (!dateString) return '未知时间';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'numeric', day: 'numeric' });
  };

  return (
    <div className="bg-white border-b sticky top-14 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} orientation="horizontal">
          <TabsList
            variant="line"
            className="w-full justify-start border-b-0 bg-transparent h-auto p-0"
          >
            {TABS.map((tab) => {
              const count = tab.key === 'platform' || tab.key === 'logistics'
                ? country.platforms.length
                : getArticlesByTheme(tab.key).length;

              return (
                <TabsTrigger
                  key={tab.key}
                  value={tab.key}
                  className={`
                    relative px-4 py-3 text-sm font-medium whitespace-nowrap
                    data-active:border-b-2 data-active:border-current
                    ${activeTab === tab.key ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'}
                  `}
                >
                  <span className="mr-1.5">{tab.emoji}</span>
                  <span>{tab.label}</span>
                  <span className="ml-1.5 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">
                    {count}
                  </span>
                </TabsTrigger>
              );
            })}
          </TabsList>

          {TABS.map((tab) => {
            const tabArticles = getArticlesByTheme(tab.key);
            const colors = TAB_COLORS[tab.key] || TAB_COLORS.policy;

            return (
              <TabsContent key={tab.key} value={tab.key} className="mt-0 p-6">
                {/* 平台标签 */}
                {tab.key === 'platform' && (
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {country.platforms.map((platform: any, idx: number) => (
                      <Card key={platform.name} className="p-5 hover:shadow-lg transition cursor-pointer border-l-4" style={{ borderLeftColor: getPlatformColor(idx) }}>
                        <div className="flex items-start gap-4">
                          <div className="w-14 h-14 bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl flex items-center justify-center text-xl font-bold shadow-inner">
                            {platform.nameEn[0]}
                          </div>
                          <div className="flex-1">
                            <div className="font-semibold text-gray-900 mb-1">
                              {platform.nameEn}
                            </div>
                            <div className="text-sm text-gray-600 mb-2">
                              市场份额: {platform.share}%
                            </div>
                            <div className="flex items-center gap-2 text-xs text-gray-500">
                              <span>卖家数: {platform.sellerCount}</span>
                              {idx === 0 && (
                                <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full">最推荐</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}

                {/* 物流标签 */}
                {tab.key === 'logistics' && (
                  <div className="space-y-4">
                    <div className="grid md:grid-cols-2 gap-4">
                      <Card className="p-5">
                        <div className="flex items-center gap-3 mb-4">
                          <span className="text-2xl">📦</span>
                          <div>
                            <div className="font-semibold text-gray-900">国内物流</div>
                            <div className="text-sm text-gray-500">Domestic Shipping</div>
                          </div>
                        </div>
                        <div className="text-lg font-medium text-gray-700">
                          {country.logistics.domestic}
                        </div>
                      </Card>

                      <Card className="p-5">
                        <div className="flex items-center gap-3 mb-4">
                          <span className="text-2xl">✈️</span>
                          <div>
                            <div className="font-semibold text-gray-900">国际物流</div>
                            <div className="text-sm text-gray-500">International Shipping</div>
                          </div>
                        </div>
                        <div className="text-lg font-medium text-gray-700">
                          {country.logistics.international}
                        </div>
                      </Card>
                    </div>

                    <Card className="p-5">
                      <div className="flex items-center gap-3 mb-4">
                        <span className="text-2xl">💵</span>
                        <div className="font-semibold text-gray-900">成本参考</div>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left py-2 font-medium text-gray-600">平台</th>
                              <th className="text-right py-2 font-medium text-gray-600">开店费用</th>
                              <th className="text-right py-2 font-medium text-gray-600">佣金</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y">
                            {Object.entries(country.costs).map(([platformName, cost]: [string, any]) => (
                              <tr key={platformName}>
                                <td className="py-3 font-medium text-gray-900">
                                  {platformName.charAt(0).toUpperCase() + platformName.slice(1)}
                                </td>
                                <td className="py-3 text-right text-gray-600">{cost.openFee}</td>
                                <td className="py-3 text-right text-gray-600">{cost.commission}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </Card>
                  </div>
                )}

                {/* 文章类标签 */}
                {tabArticles.length > 0 ? (
                  <div className="grid gap-3">
                    {tabArticles.map((article) => (
                      <Link key={article.id} href={`/articles/${article.id}`}>
                        <Card className="p-4 hover:shadow-lg transition cursor-pointer border-l-4" style={{ borderLeftColor: getThemeColor(tab.key) }}>
                          <div className="flex items-start gap-4">
                            <span className="text-2xl">{tab.emoji}</span>
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <span className={`text-xs px-2 py-0.5 rounded ${colors.bg} ${colors.text} ${colors.border} border`}>
                                  {tab.label}
                                </span>
                                <span className="text-xs text-gray-500">
                                  {formatTime(article.published_at)}
                                </span>
                                <span className="text-xs text-gray-400">·</span>
                                <span className="text-xs text-gray-500">{article.source}</span>
                              </div>
                              <h3 className="font-semibold text-gray-900 mb-1 hover:text-blue-600">
                                {article.title}
                              </h3>
                              <p className="text-sm text-gray-600 line-clamp-2">
                                {article.summary}
                              </p>
                            </div>
                          </div>
                        </Card>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-16">
                    <div className="text-gray-400 mb-3">
                      <span className="text-5xl opacity-50">{tab.emoji}</span>
                    </div>
                    <p className="text-gray-500 mb-1">暂无{tab.label}内容</p>
                    <p className="text-sm text-gray-400">我们正在整理相关信息，敬请期待</p>
                  </div>
                )}
              </TabsContent>
            );
          })}
        </Tabs>
      </div>
    </div>
  );
}

// 获取主题颜色
function getThemeColor(theme: string): string {
  const colors: Record<string, string> = {
    policy: '#eab308',    // yellow
    opportunity: '#22c55e', // green
    risk: '#ef4444',       // red
    guide: '#3b82f6',      // blue
  };
  return colors[theme] || '#6b7280';
}

// 获取平台颜色
function getPlatformColor(index: number): string {
  const colors = ['#90EE90', '#FFB347', '#DDA0DD', '#60a5fa', '#f472b6', '#a78bfa'];
  return colors[index % colors.length];
}
