import Link from 'next/link';
import { notFound } from 'next/navigation';
import { articlesApi, Article } from '@/lib/api';
import { BackToTopButton } from '@/components/article/back-to-top-button';
import { ShareButton } from '@/components/article/share-button';

// 强制动态渲染（每次请求时获取最新文章）
export const dynamic = 'force-dynamic';

// 页面Props类型
type PageProps = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
};

// 获取国家信息
const getCountryInfo = (countryCode: string | null) => {
  const countries: Record<string, { name: string; flag: string; slug: string }> = {
    'th': { name: '泰国', flag: '🇹🇭', slug: 'th' },
    'vn': { name: '越南', flag: '🇻🇳', slug: 'vn' },
    'my': { name: '马来西亚', flag: '🇲🇾', slug: 'my' },
    'us': { name: '美国', flag: '🇺🇸', slug: 'us' },
    'br': { name: '巴西', flag: '🇧🇷', slug: 'br' },
    'mx': { name: '墨西哥', flag: '🇲🇽', slug: 'mx' },
  };
  return countries[countryCode || ''] || null;
};

// 获取地区信息
const getRegionInfo = (region: string | null) => {
  const regions: Record<string, { name: string; emoji: string; color: string }> = {
    'southeast_asia': { name: '东南亚', emoji: '🌏', color: 'purple' },
    'north_america': { name: '欧美', emoji: '🇺🇸', color: 'blue' },
    'latin_america': { name: '拉美', emoji: '🇧🇷', color: 'green' },
  };
  return regions[region || ''] || null;
};

// 格式化文章内容 - 简化版本，直接渲染HTML
function formatContent(content: string | null) {
  if (!content) return null;

  // 简单处理：将 markdown 格式转换为 HTML，然后直接渲染
  let html = content
    // 处理标题
    .replace(/^### (.*$)/gm, '<h3 class="font-bold text-gray-900 mt-6 mb-3 text-lg">$1</h3>')
    .replace(/^## (.*$)/gm, '<h2 class="font-bold text-gray-900 mt-6 mb-3 text-xl">$1</h2>')
    .replace(/^# (.*$)/gm, '<h1 class="font-bold text-gray-900 mt-6 mb-3 text-2xl">$1</h1>')
    // 处理加粗
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // 处理换行
    .replace(/\n\n/g, '</p><p class="text-gray-700 leading-8 mb-4">')
    .replace(/\n/g, '<br />')
    // 包装段落
    .replace(/^(?!<h)/, '<p class="text-gray-700 leading-8 mb-4">')
    .replace(/$/, '</p>');

  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

// 文章详情页
export default async function ArticlePage({ params }: PageProps) {
  const { id } = await params;

  try {
    const article = await articlesApi.getArticle(id);
    const countryInfo = getCountryInfo(article.country);
    const regionInfo = getRegionInfo(article.region);

    // 判断是否有完整内容
    const hasFullContent = article.full_content && article.full_content.length > 50;
    const hasSummary = article.summary && article.summary.length > 10;

    return (
      <div className="min-h-screen bg-gray-50">
        {/* 返回顶部浮动按钮 */}
        <BackToTopButton />

        {/* 顶部导航条 */}
        <nav className="bg-white border-b sticky top-0 z-50 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex items-center gap-2 text-sm">
              <Link href="/" className="text-gray-600 hover:text-gray-900 flex items-center gap-1">
                <span>🏠</span>
                <span>首页</span>
              </Link>
              <span className="text-gray-400">›</span>
              {regionInfo && (
                <>
                  <Link href={`/?region=${article.region}`} className="text-gray-600 hover:text-gray-900 flex items-center gap-1">
                    <span>{regionInfo.emoji}</span>
                    <span>{regionInfo.name}</span>
                  </Link>
                  <span className="text-gray-400">›</span>
                </>
              )}
              {countryInfo && (
                <>
                  <Link href={`/${countryInfo.slug}`} className="text-gray-600 hover:text-gray-900 flex items-center gap-1">
                    <span>{countryInfo.flag}</span>
                    <span>{countryInfo.name}</span>
                  </Link>
                  <span className="text-gray-400">›</span>
                </>
              )}
              <span className="text-gray-900 font-medium truncate max-w-xs" title={article.title}>
                {article.title}
              </span>
            </div>
          </div>
        </nav>

        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* 文章头部卡片 */}
          <header className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
            {/* 标签区域 */}
            <div className="flex flex-wrap items-center gap-2 mb-4">
              {regionInfo && (
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  regionInfo.color === 'purple' ? 'bg-purple-100 text-purple-700' :
                  regionInfo.color === 'blue' ? 'bg-blue-100 text-blue-700' :
                  'bg-green-100 text-green-700'
                }`}>
                  {regionInfo.emoji} {regionInfo.name}
                </span>
              )}
              {countryInfo && (
                <Link href={`/${countryInfo.slug}`}>
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 cursor-pointer">
                    {countryInfo.flag} {countryInfo.name}
                  </span>
                </Link>
              )}
              {article.content_theme && (
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  article.content_theme === 'policy' ? 'bg-yellow-100 text-yellow-700' :
                  article.content_theme === 'opportunity' ? 'bg-green-100 text-green-700' :
                  article.content_theme === 'risk' ? 'bg-red-100 text-red-700' :
                  article.content_theme === 'guide' ? 'bg-blue-100 text-blue-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {article.content_theme === 'policy' ? '📜 政策' :
                   article.content_theme === 'opportunity' ? '💡 机会' :
                   article.content_theme === 'risk' ? '⚠️ 风险' :
                   article.content_theme === 'guide' ? '📊 指南' : '📰 资讯'}
                </span>
              )}
              {article.platform && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                  🛒 {article.platform}
                </span>
              )}
              {article.risk_level && (
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  article.risk_level === 'critical' ? 'bg-red-600 text-white' :
                  article.risk_level === 'high' ? 'bg-red-100 text-red-700' :
                  article.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-green-100 text-green-700'
                }`}>
                  {article.risk_level === 'critical' ? '🔴 严重风险' :
                   article.risk_level === 'high' ? '🟠 高风险' :
                   article.risk_level === 'medium' ? '🟡 中等风险' : '🟢 低风险'}
                </span>
              )}
              {article.opportunity_score !== null && article.opportunity_score !== undefined && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                  📈 商机评分: {Math.round(article.opportunity_score * 100)}%
                </span>
              )}
            </div>

            {/* 标题 */}
            <h1 className="text-3xl font-bold text-gray-900 mb-4 leading-tight">
              {article.title}
            </h1>

            {/* 元信息 */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 pb-4 border-b">
              <div className="flex items-center gap-1">
                <span>📰</span>
                {article.link ? (
                  <a href={article.link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    {article.source}
                  </a>
                ) : (
                  <span>{article.source}</span>
                )}
              </div>
              <span>·</span>
              <div className="flex items-center gap-1">
                <span>📅</span>
                <span>{article.published_at ? new Date(article.published_at).toLocaleDateString('zh-CN') : '未知日期'}</span>
              </div>
              <span>·</span>
              <div className="flex items-center gap-1">
                <span>✍️</span>
                <span>{article.author || 'ZenConsult编辑团队'}</span>
              </div>
            </div>

            {/* 标签 */}
            {article.tags && article.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-4">
                {article.tags.map((tag, index) => (
                  <span key={index} className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                    #{tag}
                  </span>
                ))}
              </div>
            )}
          </header>

          {/* 摘要卡片 */}
          {hasSummary && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-6 mb-6">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">📋</span>
                <h3 className="font-semibold text-blue-900 text-lg">内容摘要</h3>
              </div>
              <p className="text-gray-700 leading-relaxed text-base">{article.summary}</p>
            </div>
          )}

          {/* 完整内容 */}
          <article className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-6">
            <div className="prose prose-gray prose-p:text-lg prose-headings:font-bold prose-headings:text-gray-900 prose-a:text-blue-600 prose-strong:text-gray-900 prose-code:bg-gray-100 prose-code:text-gray-800 max-w-none">
              {/* 优先显示 full_content，如果没有则显示摘要 */}
              {article.full_content && article.full_content.length > 50
                ? formatContent(article.full_content)
                : (
                  <div className="space-y-4">
                    <p className="text-gray-700 leading-relaxed text-base">
                      {article.summary || article.full_content || "文章内容正在加载中..."}
                    </p>
                    {article.link && (
                      <p className="text-sm text-gray-500 mt-4">
                        来源: <a href={article.link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{article.source}</a>
                      </p>
                    )}
                  </div>
                )
              }
            </div>

            {/* 文章底部操作栏 */}
            <div className="flex items-center justify-between pt-6 mt-8 border-t border-gray-200">
              <div className="flex gap-3">
                <ShareButton />
              </div>
              <div className="text-sm text-gray-500">
                {article.published_at ? `发布于 ${new Date(article.published_at).toLocaleString('zh-CN')}` : '发布日期未知'}
              </div>
            </div>
          </article>

          {/* 相关推荐 */}
          <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xl">📚</span>
              <h3 className="text-lg font-bold">相关阅读</h3>
            </div>
            <div className="text-center py-8 text-gray-500 text-sm">
              <p className="mb-2">相关文章推荐功能即将上线</p>
              <p>我们会根据文章内容为您推荐更多相关资讯</p>
            </div>
          </section>

          {/* 底部CTA */}
          <section className="mt-6 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-xl p-8 text-center text-white shadow-lg">
            <h3 className="text-xl font-bold mb-2">🚀 想要更深入的市场分析？</h3>
            <p className="text-blue-100 mb-6 max-w-2xl mx-auto">
              升级到专业版，获取AI选品分析、成本计算器、竞品分析等高级功能，助您在跨境电商市场取得成功
            </p>
            <div className="flex gap-3 justify-center">
              <Link href="/pricing" className="px-8 py-3 bg-white text-blue-600 rounded-lg hover:bg-gray-100 font-medium transition-colors shadow-sm">
                查看定价
              </Link>
              <Link href="/register" className="px-8 py-3 bg-blue-700 text-white rounded-lg hover:bg-blue-800 font-medium transition-colors shadow-sm">
                免费注册
              </Link>
            </div>
          </section>
        </div>
      </div>
    );
  } catch (error) {
    console.error('Failed to fetch article:', error);
    notFound();
  }
}

// 生成元数据
export async function generateMetadata({ params }: PageProps) {
  const { id } = await params;

  try {
    const article = await articlesApi.getArticle(id);

    return {
      title: `${article.title} - ZenConsult跨境电商`,
      description: article.summary || article.title,
      keywords: article.tags?.join(', ') || '',
    };
  } catch {
    return {
      title: '文章不存在',
    };
  }
}
