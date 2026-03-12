import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MarketData {
  market: string;
  flag: string;
  gdp: string;
  growth: number;
  trend: 'up' | 'down' | 'flat';
  population: string;
  internet: string;
}

const marketsData: MarketData[] = [
  {
    market: '东南亚',
    flag: '🇸🇬',
    gdp: '$3.6万亿',
    growth: 4.5,
    trend: 'up',
    population: '6.7亿',
    internet: '75%',
  },
  {
    market: '欧盟',
    flag: '🇪🇺',
    gdp: '$17万亿',
    growth: 1.2,
    trend: 'up',
    population: '4.5亿',
    internet: '92%',
  },
  {
    market: '美国',
    flag: '🇺🇸',
    gdp: '$25万亿',
    growth: 2.1,
    trend: 'up',
    population: '3.3亿',
    internet: '90%',
  },
  {
    market: '拉美',
    flag: '🇧🇷',
    gdp: '$5.5万亿',
    growth: 3.2,
    trend: 'up',
    population: '6.5亿',
    internet: '80%',
  },
];

interface CategoryTrend {
  category: string;
  growth: number;
  volume: string;
  trend: 'up' | 'down' | 'flat';
}

const categoryTrends: CategoryTrend[] = [
  { category: '宠物用品', growth: 45, volume: '$120亿', trend: 'up' },
  { category: '智能家居', growth: 38, volume: '$85亿', trend: 'up' },
  { category: '美妆个护', growth: 22, volume: '$200亿', trend: 'up' },
  { category: '户外用品', growth: 15, volume: '$95亿', trend: 'up' },
  { category: '健康食品', growth: 32, volume: '$150亿', trend: 'up' },
];

export default function MarketOverviewPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">市场概览</h1>
        <p className="text-muted-foreground">
          了解目标市场的基本情况、消费趋势和增长机会
        </p>
      </div>

      {/* Market Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full max-w-md grid-cols-3">
          <TabsTrigger value="overview">市场概览</TabsTrigger>
          <TabsTrigger value="trends">消费趋势</TabsTrigger>
          <TabsTrigger value="insights">深度洞察</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Market Cards */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {marketsData.map((market) => (
              <Card key={market.market} className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-3xl">{market.flag}</span>
                  {market.trend === 'up' && (
                    <TrendingUp className="h-5 w-5 text-green-500" />
                  )}
                  {market.trend === 'down' && (
                    <TrendingDown className="h-5 w-5 text-red-500" />
                  )}
                  {market.trend === 'flat' && (
                    <Minus className="h-5 w-5 text-gray-500" />
                  )}
                </div>
                <h3 className="text-lg font-semibold mb-3">{market.market}</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">GDP</span>
                    <span className="font-medium">{market.gdp}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">增长率</span>
                    <span className={`font-medium ${market.trend === 'up' ? 'text-green-600' : market.trend === 'down' ? 'text-red-600' : ''}`}>
                      {market.growth}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">人口</span>
                    <span className="font-medium">{market.population}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">互联网</span>
                    <span className="font-medium">{market.internet}</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Key Metrics */}
          <div className="grid md:grid-cols-4 gap-6">
            <Card className="p-6">
              <div className="text-sm text-muted-foreground mb-2">覆盖市场</div>
              <div className="text-3xl font-bold">12</div>
              <div className="text-xs text-muted-foreground mt-1">持续增长中</div>
            </Card>
            <Card className="p-6">
              <div className="text-sm text-muted-foreground mb-2">总人口</div>
              <div className="text-3xl font-bold">21亿</div>
              <div className="text-xs text-muted-foreground mt-1">潜在消费者</div>
            </Card>
            <Card className="p-6">
              <div className="text-sm text-muted-foreground mb-2">GDP总和</div>
              <div className="text-3xl font-bold">$54.7万亿</div>
              <div className="text-xs text-muted-foreground mt-1">市场规模</div>
            </Card>
            <Card className="p-6">
              <div className="text-sm text-muted-foreground mb-2">平均增长</div>
              <div className="text-3xl font-bold text-green-600">+2.8%</div>
              <div className="text-xs text-muted-foreground mt-1">年增长率</div>
            </Card>
          </div>
        </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">热门品类增长趋势</h2>
            <div className="space-y-4">
              {categoryTrends.map((item) => (
                <div key={item.category} className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{item.category}</span>
                      <span className="text-sm text-muted-foreground">{item.volume}</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all"
                        style={{ width: `${item.growth}%` }}
                      />
                    </div>
                  </div>
                  <div className={`flex items-center gap-1 ${item.trend === 'up' ? 'text-green-600' : item.trend === 'down' ? 'text-red-600' : 'text-gray-600'}`}>
                    <span className="text-lg font-bold">{item.growth > 0 ? '+' : ''}{item.growth}%</span>
                    {item.trend === 'up' && <TrendingUp className="h-4 w-4" />}
                    {item.trend === 'down' && <TrendingDown className="h-4 w-4" />}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Shopping Behavior */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">消费者购物行为</h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-4xl font-bold text-primary mb-2">68%</div>
                <div className="text-sm text-muted-foreground">在线购物比例</div>
                <div className="text-xs text-muted-foreground mt-1">较去年+12%</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-primary mb-2">2.3</div>
                <div className="text-sm text-muted-foreground">平均年消费次数</div>
                <div className="text-xs text-muted-foreground mt-1">跨境+8%</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-primary mb-2">$127</div>
                <div className="text-sm text-muted-foreground">平均客单价</div>
                <div className="text-xs text-muted-foreground mt-1">较去年+5%</div>
              </div>
            </div>
          </Card>
        </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">市场进入建议</h2>
            <div className="space-y-4">
              <div className="border-l-4 border-primary pl-4">
                <h3 className="font-semibold mb-1">东南亚：快速增长期</h3>
                <p className="text-sm text-muted-foreground">
                  中产阶级迅速扩大，电商渗透率仍有提升空间。建议从新加坡、马来西亚等成熟市场切入。
                </p>
              </div>
              <div className="border-l-4 border-blue-500 pl-4">
                <h3 className="font-semibold mb-1">拉美：差异化竞争</h3>
                <p className="text-sm text-muted-foreground">
                  本土供应链不完善，中国制造有明显优势。建议关注巴西、墨西哥重点国家。
                </p>
              </div>
              <div className="border-l-4 border-purple-500 pl-4">
                <h3 className="font-semibold mb-1">欧美：品牌化运营</h3>
                <p className="text-sm text-muted-foreground">
                  市场成熟但竞争激烈，需要建立品牌差异化。建议聚焦细分市场和小众品类。
                </p>
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
