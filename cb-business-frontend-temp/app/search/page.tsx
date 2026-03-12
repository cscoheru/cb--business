'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Card } from '@/components/ui/card';
import { SearchFilterBar } from '@/components/search/search-filter-bar';
import { articlesApi, Article } from '@/lib/api';

function SearchPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams.get('q') || '';

  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [filteredArticles, setFilteredArticles] = useState<Article[]>([]);

  // 筛选状态
  const [regionFilter, setRegionFilter] = useState<string>('');
  const [themeFilter, setThemeFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState<'latest' | 'oldest' | 'relevance'>('relevance');

  useEffect(() => {
    const fetchArticles = async () => {
      setLoading(true);
      try {
        const { articles: allArticles } = await articlesApi.getArticles({ per_page: 200 });
        setArticles(allArticles);
      } catch (error) {
        console.error('Failed to fetch articles:', error);
        setArticles([]);
      } finally {
        setLoading(false);
      }
    };

    fetchArticles();
  }, []);

  // 客户端筛选和排序
  useEffect(() => {
    let results = [...articles];

    // 关键词搜索
    if (query.trim()) {
      const keywords = query.toLowerCase().split(/\s+/);
      results = results.filter(article => {
        const title = article.title.toLowerCase();
        const summary = (article.summary || '').toLowerCase();
        const source = article.source.toLowerCase();

        return keywords.some(keyword =>
          title.includes(keyword) ||
          summary.includes(keyword) ||
          source.includes(keyword)
        );
      });
    }

    // 区域筛选
    if (regionFilter) {
      results = results.filter(a => a.region === regionFilter);
    }

    // 主题筛选
    if (themeFilter) {
      results = results.filter(a => a.content_theme === themeFilter);
    }

    // 排序
    if (sortBy === 'latest') {
      results.sort((a, b) => {
        const dateA = a.published_at ? new Date(a.published_at).getTime() : 0;
        const dateB = b.published_at ? new Date(b.published_at).getTime() : 0;
        return dateB - dateA;
      });
    } else if (sortBy === 'oldest') {
      results.sort((a, b) => {
        const dateA = a.published_at ? new Date(a.published_at).getTime() : 0;
        const dateB = b.published_at ? new Date(b.published_at).getTime() : 0;
        return dateA - dateB;
      });
    } else {
      // 相关度排序 - 标题匹配优先
      if (query.trim()) {
        const keywords = query.toLowerCase().split(/\s+/);
        results.sort((a, b) => {
          const scoreA = getRelevanceScore(a.title, keywords);
          const scoreB = getRelevanceScore(b.title, keywords);
          return scoreB - scoreA;
        });
      }
    }

    setFilteredArticles(results);
  }, [articles, query, regionFilter, themeFilter, sortBy]);

  // 计算相关度分数
  const getRelevanceScore = (text: string, keywords: string[]): number => {
    const lowerText = text.toLowerCase();
    return keywords.reduce((score, keyword) => {
      if (lowerText.includes(keyword)) {
        // 完全匹配加分更多
        if (lowerText === keyword) return score + 10;
        return score + 1;
      }
      return score;
    }, 0);
  };

  const formatTime = (dateString: string | null) => {
    if (!dateString) return '未知时间';
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return '今天';
    if (days === 1) return '昨天';
    if (days < 7) return `${days}天前`;
    if (days < 30) return `${Math.floor(days / 7)}周前`;
    if (days < 365) return `${Math.floor(days / 30)}月前`;
    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'numeric' });
  };

  const getRegionEmoji = (region: string | null) => {
    const emojis: Record<string, string> = {
      southeast_asia: '🌏',
      north_america: '🇺🇸',
      latin_america: '🇧🇷',
    };
    return region ? emojis[region] || '📰' : '📰';
  };

  const getThemeEmoji = (theme: string | null) => {
    const emojis: Record<string, string> = {
      policy: '📜',
      opportunity: '💡',
      risk: '⚠️',
      guide: '📊',
      platform: '🛒',
      logistics: '🚚',
    };
    return theme ? emojis[theme] || '📰' : '📰';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <Link href="/" className="text-sm text-gray-600 hover:text-gray-900">
            ← 返回首页
          </Link>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* 搜索标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {query ? `"${query}"` : '全部文章'}
          </h1>
          <p className="text-sm text-gray-600">
            找到 <span className="font-semibold text-gray-900">{filteredArticles.length}</span> 篇相关文章
          </p>
        </div>

        {/* 筛选栏 */}
        <div className="mb-6">
          <SearchFilterBar
            regionFilter={regionFilter}
            themeFilter={themeFilter}
            sortBy={sortBy}
            onRegionChange={setRegionFilter}
            onThemeChange={setThemeFilter}
            onSortChange={setSortBy}
          />
        </div>

        {/* 搜索结果 */}
        {loading ? (
          <div className="text-center py-16">
            <div className="text-gray-400 text-5xl mb-4 animate-pulse">🔍</div>
            <p className="text-gray-500">正在搜索...</p>
          </div>
        ) : filteredArticles.length === 0 ? (
          <div className="bg-white rounded-xl p-16 text-center border">
            <div className="text-gray-300 text-6xl mb-4">📭</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {query ? `没有找到与"${query}"相关的文章` : '暂无文章'}
            </h2>
            <p className="text-gray-500 mb-6">
              {query
                ? '试试其他关键词，或使用上方的筛选条件'
                : '文章正在更新中，敬请期待'}
            </p>
            <div className="flex gap-3 justify-center">
              <Link
                href="/"
                className="px-5 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
              >
                返回首页
              </Link>
              {query && (
                <button
                  onClick={() => router.push('/search')}
                  className="px-5 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
                >
                  清除筛选
                </button>
              )}
            </div>
          </div>
        ) : (
          <>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredArticles.map((article) => (
                <Link key={article.id} href={`/articles/${article.id}`}>
                  <Card className="p-5 hover:shadow-lg transition cursor-pointer border-l-4 h-full" style={{ borderLeftColor: '#a855f7' }}>
                    <div className="flex items-start gap-3">
                      <div className="text-xl">
                        <span className="block text-lg mb-1">{getRegionEmoji(article.region)}</span>
                        <span>{getThemeEmoji(article.content_theme)}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                          <span className="text-xs px-2 py-0.5 rounded bg-purple-100 text-purple-700">
                            {article.region === 'southeast_asia' ? '东南亚' :
                             article.region === 'north_america' ? '欧美' :
                             article.region === 'latin_america' ? '拉美' : '全球'}
                          </span>
                          <span className="text-xs text-gray-500">
                            {formatTime(article.published_at)}
                          </span>
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-2 hover:text-blue-600 line-clamp-2">
                          {article.title}
                        </h3>
                        <p className="text-sm text-gray-600 line-clamp-3 mb-3">
                          {article.summary}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <span>{article.source}</span>
                        </div>
                      </div>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>

            {/* 加载更多提示 */}
            {filteredArticles.length >= 20 && (
              <div className="mt-8 text-center">
                <p className="text-sm text-gray-500">
                  已显示前 {filteredArticles.length} 篇文章
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// 搜索页面需要Suspense包裹，因为使用了useSearchParams
function SearchPageWrapper() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-400 text-5xl animate-pulse">🔍</div>
      </div>
    }>
      <SearchPageContent />
    </Suspense>
  );
}

export default SearchPageWrapper;
