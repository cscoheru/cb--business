import Link from 'next/link';
import { notFound } from 'next/navigation';
import { articlesApi, Article } from '@/lib/api';
import { Card } from '@/components/ui/card';
import { getCountryBySlug, getCountriesByRegion } from '@/config/countries';
import type { CountryConfig } from '@/config/countries/types';
import { CountryPortalTabs } from '@/components/country/country-portal-tabs';

// 强制动态渲染（每次请求时获取最新文章）
export const dynamic = 'force-dynamic';

// 生成静态路径（用于构建时预渲染）
export async function generateStaticParams() {
  const countries = await Promise.all([
    getCountryBySlug('th'),
    getCountryBySlug('vn'),
    getCountryBySlug('my'),
    getCountryBySlug('us'),
    getCountryBySlug('br'),
    getCountryBySlug('mx'),
  ]);

  return countries
    .filter((c): c is CountryConfig => c !== undefined)
    .map((country) => ({ country: country.slug }));
}

// 页面Props类型
type PageProps = {
  params: Promise<{ country: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
};

// 国家门户页面
export default async function CountryPage({ params, searchParams }: PageProps) {
  const { country: countrySlug } = await params;
  const country = getCountryBySlug(countrySlug);

  if (!country) {
    notFound();
  }

  // 获取该国家的文章（优先按国家筛选，如果没有则按地区筛选）
  const { articles, total } = await articlesApi.getArticles({
    country: country.slug,  // 使用国家代码筛选
    per_page: 50,  // 增加每页文章数量
  });

  // 获取同一区域的其他国家
  const regionCountries = getCountriesByRegion(country.region);

  return (
    <>
      {/* 面包屑 */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-2">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Link href="/" className="hover:text-gray-900">首页</Link>
            <span>›</span>
            <Link href={`/?region=${country.region}`} className="hover:text-gray-900 capitalize">
              {country.region.replace('_', ' ')}
            </Link>
            <span>›</span>
            <span className="text-gray-900 font-medium">{country.name}</span>
          </div>
        </div>
      </nav>

      {/* 国家门户头部 - 带地区特色渐变 */}
      <header className={`relative overflow-hidden ${
        country.region === 'southeast_asia' ? 'bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400' :
        country.region === 'north_america' ? 'bg-gradient-to-br from-blue-600 via-indigo-500 to-purple-500' :
        'bg-gradient-to-br from-green-600 via-teal-500 to-emerald-400'
      } text-white`}>
        {/* 装饰性图案 */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-64 h-64 border-8 border-white rounded-full -translate-x-1/2 -translate-y-1/2"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 border-8 border-white rounded-full translate-x-1/2 translate-y-1/2"></div>
          <div className="absolute top-1/2 left-1/4 w-32 h-32 border-4 border-white rounded-full -translate-y-1/2"></div>
        </div>

        <div className="relative max-w-7xl mx-auto px-4 py-10">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-4 mb-4">
                <span className="text-7xl drop-shadow-lg">{country.flag}</span>
                <div>
                  <h1 className="text-4xl font-bold text-white drop-shadow-lg">{country.name}</h1>
                  <p className="text-white/90 text-lg">{country.nameEn} · {country.culture.greeting}</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="bg-white/15 backdrop-blur-sm rounded-lg px-4 py-3 border border-white/20">
                  <div className="flex items-center gap-2 text-white/80">
                    <span>👥</span>
                    <span>人口</span>
                  </div>
                  <div className="font-semibold text-white text-lg">{country.population}</div>
                </div>
                <div className="bg-white/15 backdrop-blur-sm rounded-lg px-4 py-3 border border-white/20">
                  <div className="flex items-center gap-2 text-white/80">
                    <span>💰</span>
                    <span>GDP</span>
                  </div>
                  <div className="font-semibold text-white text-lg">{country.gdp}</div>
                </div>
                <div className="bg-white/15 backdrop-blur-sm rounded-lg px-4 py-3 border border-white/20">
                  <div className="flex items-center gap-2 text-white/80">
                    <span>🛒</span>
                    <span>电商规模</span>
                  </div>
                  <div className="font-semibold text-white text-lg">{country.ecommerce}</div>
                </div>
                <div className="bg-white/15 backdrop-blur-sm rounded-lg px-4 py-3 border border-white/20">
                  <div className="flex items-center gap-2 text-white/80">
                    <span>📈</span>
                    <span>增长率</span>
                  </div>
                  <div className="font-semibold text-green-300 text-lg">{country.growth} 🚀</div>
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="bg-white/15 backdrop-blur-sm rounded-lg px-5 py-3 border border-white/20 mb-3">
                <div className="text-white/80 text-sm">📰 文章</div>
                <div className="font-semibold text-white text-2xl">{total}</div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 6标签导航 */}
      <CountryPortalTabs country={country} articles={articles} />

      {/* 主要内容区 */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* 市场概览卡片 */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <Card className="p-5">
            <div className="flex items-center gap-2 text-gray-600 text-sm mb-2">
              <span>📱</span>
              <span>移动电商占比</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{country.mobileCommerceRate}</div>
          </Card>

          <Card className="p-5">
            <div className="flex items-center gap-2 text-gray-600 text-sm mb-2">
              <span>💳</span>
              <span>主流支付</span>
            </div>
            <div className="text-sm text-gray-700">
              {country.paymentMethods.slice(0, 2).join(' · ')}
            </div>
          </Card>

          <Card className="p-5">
            <div className="flex items-center gap-2 text-gray-600 text-sm mb-2">
              <span>🏪</span>
              <span>热门平台</span>
            </div>
            <div className="text-sm text-gray-700">
              {country.platforms.slice(0, 2).map((p: any) => p.nameEn).join(' · ')}
            </div>
          </Card>

          <Card className="p-5">
            <div className="flex items-center gap-2 text-gray-600 text-sm mb-2">
              <span>🚚</span>
              <span>物流时效</span>
            </div>
            <div className="text-sm text-gray-700">{country.logistics.domestic}</div>
          </Card>
        </div>

        {/* 同区域其他国家 */}
        {regionCountries.length > 1 && (
          <section>
            <h2 className="text-sm font-bold mb-4 text-gray-600">
              其他{country.region.replace('_', ' ')}国家
            </h2>
            <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-3">
              {regionCountries
                .filter(c => c.code !== country.code)
                .map((c) => (
                  <Link key={c.code} href={`/${c.slug}`}>
                    <Card className="p-4 hover:shadow-md transition cursor-pointer text-center">
                      <span className="text-3xl">{c.flag}</span>
                      <div className="font-medium mt-2">{c.name}</div>
                      <div className="text-xs text-gray-500">{c.ecommerce}</div>
                    </Card>
                  </Link>
                ))}
            </div>
          </section>
        )}
      </main>
    </>
  );
}

// 生成元数据
export async function generateMetadata({ params }: PageProps) {
  const { country: countrySlug } = await params;
  const country = getCountryBySlug(countrySlug);

  if (!country) {
    return {
      title: '国家不存在',
    };
  }

  return {
    title: `${country.name}跨境电商门户 - ${country.nameEn} e-commerce Guide`,
    description: country.description,
  };
}
