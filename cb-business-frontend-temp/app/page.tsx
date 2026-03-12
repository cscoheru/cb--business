import Link from 'next/link';
import { HeroSearch } from '@/components/home/hero-search';
import { FunModules } from '@/components/home/fun-modules';
import { RegionNews } from '@/components/home/region-news';
import { ThemePortals } from '@/components/home/theme-portals';

export default function HomePage() {
  // Articles will be fetched client-side by components
  const latestArticles: any[] = [];

  return (
    <div className="bg-gray-100 min-h-screen">
      {/* 全局导航栏 */}
      <nav className="bg-white border-b sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-8">
              <Link href="/" className="font-bold text-xl text-gray-900 flex items-center gap-2">
                <span className="text-2xl">🌐</span>
                ZenConsult
              </Link>
              <div className="hidden md:flex items-center gap-6 text-sm text-gray-600">
                <Link href="#" className="hover:text-gray-900">首页</Link>
                <Link href="/th" className="hover:text-gray-900">🌏 东南亚</Link>
                <Link href="/us" className="hover:text-gray-900">🇺🇸 欧美</Link>
                <Link href="/br" className="hover:text-gray-900">🇧🇷 拉美</Link>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <input
                type="search"
                placeholder="搜索..."
                className="px-3 py-1.5 border border-gray-200 rounded text-sm w-40 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">登录</Link>
              <Link href="/register" className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700">
                注册
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero搜索区域 */}
      <HeroSearch />

      {/* 三大区域资讯流 */}
      <RegionNews initialArticles={latestArticles} />

      {/* 有趣的功能模块 */}
      <FunModules />

      {/* 专业信息门户 */}
      <ThemePortals articles={latestArticles} />

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg p-8 text-center border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            想要更深入的数据分析？
          </h2>
          <p className="text-gray-600 mb-4">
            升级到专业版，获取AI选品分析、成本计算器等高级功能
          </p>
          <div className="flex gap-3 justify-center">
            <Link href="/pricing" className="px-5 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              查看定价
            </Link>
            <Link href="/register" className="px-5 py-2 border border-gray-300 text-gray-700 rounded text-sm hover:bg-gray-50">
              免费注册
            </Link>
          </div>
        </div>
      </section>

      {/* 页脚 */}
      <footer className="bg-white border-t border-gray-200 py-8">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-gray-500">
            <p>© 2024 ZenConsult. 跨境电商智能信息平台</p>
            <div className="flex gap-4">
              <Link href="#" className="hover:text-gray-900">关于</Link>
              <Link href="#" className="hover:text-gray-900">隐私</Link>
              <Link href="#" className="hover:text-gray-900">条款</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
