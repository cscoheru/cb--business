import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, AlertTriangle, DollarSign } from 'lucide-react';
import Link from 'next/link';

interface OpportunityCardProps {
  id: string;
  title: string;
  market: string;
  category: string;
  reason: string;
  potential: 'high' | 'medium' | 'low';
}

export function OpportunityCard({
  id,
  title,
  market,
  category,
  reason,
  potential
}: OpportunityCardProps) {
  const potentialConfig = {
    high: { color: 'bg-green-500', label: '高潜力', icon: TrendingUp },
    medium: { color: 'bg-yellow-500', label: '中等潜力', icon: TrendingUp },
    low: { color: 'bg-gray-500', label: '待验证', icon: AlertTriangle },
  };

  const config = potentialConfig[potential];
  const Icon = config.icon;

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <Badge variant="outline" className="mb-2">{market}</Badge>
          <h3 className="text-lg font-semibold">{title}</h3>
          <p className="text-sm text-muted-foreground">{category}</p>
        </div>
        <div className={`p-2 rounded-lg ${config.color}/10`}>
          <Icon className={`h-5 w-5 ${config.color.replace('bg-', 'text-')}`} />
        </div>
      </div>

      <p className="text-sm mb-4 line-clamp-2">{reason}</p>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 text-sm">
          <DollarSign className="h-4 w-4 text-green-600" />
          <span className="text-green-600 font-medium">预估利润率 25-35%</span>
        </div>
        <Link href={`/dashboard/opportunities/${id}`}>
          <Button size="sm" variant="outline">查看详情</Button>
        </Link>
      </div>
    </Card>
  );
}

// 默认导出示例数据
export function mockOpportunityCard(index: number) {
  const opportunities = [
    {
      id: '1',
      title: '东南亚宠物用品市场',
      market: '东南亚',
      category: '宠物用品',
      reason: '随着中产阶级崛起，宠物领养率同比增长40%，但本土供应链薄弱，中国产品有明显价格优势。',
      potential: 'high' as const,
    },
    {
      id: '2',
      title: '拉美智能家居小工具',
      market: '拉美',
      category: '智能家居',
      reason: '智能门锁、智能插座等入门级产品需求激增，当地品牌少，主要依赖进口。',
      potential: 'high' as const,
    },
    {
      id: '3',
      title: '欧美露营装备',
      market: '欧美',
      category: '户外用品',
      reason: '疫情后户外露营持续火热，轻量化、多功能产品更受欢迎。',
      potential: 'medium' as const,
    },
    {
      id: '4',
      title: '中东美妆个护',
      market: '中东',
      category: '美妆个护',
      reason: '宗教和文化偏好带来特殊需求，如无酒精、清真认证产品有市场机会。',
      potential: 'medium' as const,
    },
  ];

  return opportunities[index % opportunities.length];
}
