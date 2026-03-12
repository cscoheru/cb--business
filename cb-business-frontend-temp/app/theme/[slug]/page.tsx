import Link from 'next/link';
import { notFound } from 'next/navigation';
import { articlesApi, Article } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { ThemeFilterClient } from '@/components/theme/theme-filter-client';

// 强制动态渲染
export const dynamic = 'force-dynamic';

// 主题配置
const THEMES: Record<string, { name: string; description: string; emoji: string; color: string }> = {
  policy: { name: '政策中心', description: '各国电商政策法规解读', emoji: '📜', color: '#eab308' },
  opportunity: { name: '机会发现', description: '市场机会、选品建议', emoji: '💡', color: '#22c55e' },
  risk: { name: '风险预警', description: '市场风险、运营陷阱', emoji: '⚠️', color: '#ef4444' },
  guide: { name: '实操指南', description: '开店流程、运营技巧', emoji: '📊', color: '#3b82f6' },
  platform: { name: '平台指南', description: '各大平台入驻、运营', emoji: '🛒', color: '#a855f7' },
  logistics: { name: '物流参考', description: '国际物流、仓储方案', emoji: '🚚', color: '#f97316' },
};

// 生成静态路径
export async function generateStaticParams() {
  return Object.keys(THEMES).map((slug) => ({ slug }));
}

// 页面Props类型
type PageProps = {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
};

// 主题分类页面
export default async function ThemePage({ params, searchParams }: PageProps) {
  const { slug } = await params;
  const theme = THEMES[slug];

  if (!theme) {
    notFound();
  }

  // 获取该主题的所有文章
  const { articles, total } = await articlesApi.getArticles({
    theme: slug,
    per_page: 100,
  });

  // 获取搜索参数
  const { region, sort } = await searchParams;

  // 客户端筛选文章
  let filteredArticles = [...articles];

  // 按区域筛选
  if (region && typeof region === 'string') {
    filteredArticles = filteredArticles.filter(a => a.region === region);
  }

  // 排序
  if (sort === 'oldest') {
    filteredArticles.sort((a, b) => {
      const dateA = a.published_at ? new Date(a.published_at).getTime() : 0;
      const dateB = b.published_at ? new Date(b.published_at).getTime() : 0;
      return dateA - dateB;
    });
  } else {
    // 默认按最新排序
    filteredArticles.sort((a, b) => {
      const dateA = a.published_at ? new Date(a.published_at).getTime() : 0;
      const dateB = b.published_at ? new Date(b.published_at).getTime() : 0;
      return dateB - dateA;
    });
  }

  return (
    <>
      {/* 面包屑 */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-2">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Link href="/" className="hover:text-gray-900">首页</Link>
            <span>›</span>
            <Link href="/" className="hover:text-gray-900">专业信息门户</Link>
            <span>›</span>
            <span className="text-gray-900 font-medium">{theme.name}</span>
          </div>
        </div>
      </nav>

      {/* 页面头部 - 主题色渐变 */}
      <header
        className="relative overflow-hidden text-white py-12"
        style={{ background: `linear-gradient(135deg, ${theme.color}dd, ${theme.color}99)` }}
      >
        {/* 装饰性圆形 */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full translate-y-1/2 -translate-x-1/2" />

        <div className="relative max-w-7xl mx-auto px-4">
          <div className="flex items-center gap-4 mb-4">
            <span className="text-6xl drop-shadow-lg">{theme.emoji}</span>
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-white drop-shadow-lg mb-2">
                {theme.name}
              </h1>
              <p className="text-white/90 text-lg">{theme.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="bg-white/15 backdrop-blur-sm rounded-lg px-4 py-2 border border-white/20">
              <span className="text-white/80">共</span>
              <span className="font-semibold text-white ml-1">{total}</span>
              <span className="text-white/80 ml-1">篇文章</span>
            </div>
            <Link
              href="/"
              className="bg-white/15 backdrop-blur-sm rounded-lg px-4 py-2 border border-white/20 hover:bg-white/25 transition"
            >
              ← 返回首页
            </Link>
          </div>
        </div>
      </header>

      {/* 筛选栏 */}
      <div className="bg-white border-b sticky top-14 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <ThemeFilterClient
            currentTheme={slug}
            currentRegion={region as string | undefined}
            currentSort={sort as string | undefined}
            articleCount={filteredArticles.length}
          />
        </div>
      </div>

      {/* 文章列表 */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {filteredArticles.length === 0 ? (
          <div className="bg-white rounded-xl p-16 text-center border">
            <div className="text-gray-300 mb-4">
              <span className="text-6xl opacity-50">{theme.emoji}</span>
            </div>
            <p className="text-gray-500 mb-2">暂无相关文章</p>
            <p className="text-sm text-gray-400">尝试调整筛选条件或返回首页探索其他内容</p>
          </div>
        ) : (
          <>
            <div className="text-sm text-gray-500 mb-4">
              显示 <span className="font-medium text-gray-700">{filteredArticles.length}</span> 篇文章
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredArticles.map((article) => (
                <Link key={article.id} href={`/articles/${article.id}`}>
                  <Card className="p-5 hover:shadow-lg transition cursor-pointer border-l-4 h-full" style={{ borderLeftColor: theme.color }}>
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{getRegionEmoji(article.region)}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">
                            {getRegionName(article.region)}
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
                          <span>来源: {article.source}</span>
                        </div>
                      </div>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          </>
        )}
      </main>

      {/* 返回顶部 */}
      <div className="fixed bottom-6 right-6">
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="w-10 h-10 bg-white shadow-lg rounded-full flex items-center justify-center text-gray-600 hover:text-gray-900 hover:shadow-xl transition"
        >
          ↑
        </button>
      </div>
    </>
  );
}

// 获取区域图标
function getRegionEmoji(region: string | null): string {
  const emojis: Record<string, string> = {
    southeast_asia: '🌏',
    north_america: '🇺🇸',
    latin_america: '🇧🇷',
  };
  return region ? emojis[region] || '📰' : '📰';
}

// 获取区域名称
function getRegionName(region: string | null): string {
  const names: Record<string, string> = {
    southeast_asia: '东南亚',
    north_america: '欧美',
    latin_america: '拉美',
  };
  return region ? names[region] || '全球' : '全球';
}

// 格式化时间
function formatTime(dateString: string | null) {
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
}

// 生成元数据
export async function generateMetadata({ params }: PageProps) {
  const { slug } = await params;
  const theme = THEMES[slug];

  if (!theme) {
    return {
      title: '主题不存在',
    };
  }

  return {
    title: `${theme.name} - 跨境电商${theme.name}`,
    description: theme.description,
  };
}
