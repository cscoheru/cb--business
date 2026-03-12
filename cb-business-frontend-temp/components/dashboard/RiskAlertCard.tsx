import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react';

interface RiskAlertCardProps {
  id: string;
  title: string;
  market: string;
  type: 'policy' | 'tariff' | 'compliance';
  severity: 'high' | 'medium' | 'low';
  description: string;
  date: string;
}

export function RiskAlertCard({
  id,
  title,
  market,
  type,
  severity,
  description,
  date,
}: RiskAlertCardProps) {
  const typeConfig = {
    policy: { label: '政策变更', icon: AlertTriangle, color: 'bg-orange-500' },
    tariff: { label: '关税调整', icon: AlertCircle, color: 'bg-red-500' },
    compliance: { label: '合规要求', icon: Info, color: 'bg-blue-500' },
  };

  const severityConfig = {
    high: { label: '高风险', color: 'destructive' },
    medium: { label: '中风险', color: 'secondary' },
    low: { label: '低风险', color: 'outline' },
  };

  const typeInfo = typeConfig[type];
  const severityInfo = severityConfig[severity];
  const TypeIcon = typeInfo.icon;

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${typeInfo.color}/10`}>
            <TypeIcon className={`h-5 w-5 ${typeInfo.color.replace('bg-', 'text-')}`} />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="outline">{market}</Badge>
              <Badge variant={severityInfo.color as any}>{severityInfo.label}</Badge>
            </div>
            <h3 className="text-lg font-semibold">{title}</h3>
          </div>
        </div>
        <span className="text-xs text-muted-foreground">{date}</span>
      </div>

      <p className="text-sm text-muted-foreground mb-4">{description}</p>

      <div className="flex gap-2">
        <Button size="sm" variant="outline">查看详情</Button>
        <Button size="sm" variant="ghost">忽略</Button>
      </div>
    </Card>
  );
}

// 默认导出示例数据
export function mockRiskAlertCard(index: number) {
  const alerts = [
    {
      id: '1',
      title: '印尼电子产品认证要求变更',
      market: '印度尼西亚',
      type: 'policy' as const,
      severity: 'high' as const,
      description: '印尼将于下月实施新的电子产品认证标准，所有进口电子产品需要通过SDPPI认证，认证周期预计延长至2-3周。',
      date: '2小时前',
    },
    {
      id: '2',
      title: '欧盟对中国电动车加征关税',
      market: '欧盟',
      type: 'tariff' as const,
      severity: 'high' as const,
      description: '欧盟正式宣布对中国制造的电动车征收临时关税，税率从17.4%至37.6%不等，将直接影响相关产品出口利润。',
      date: '5小时前',
    },
    {
      id: '3',
      title: '泰国FDA进口食品新规',
      market: '泰国',
      type: 'compliance' as const,
      severity: 'medium' as const,
      description: '泰国食品药品监督管理局发布新规，要求所有进口食品提供泰语标签和营养成分表，违规产品将被扣留。',
      date: '1天前',
    },
    {
      id: '4',
      title: '越南增值税税率调整',
      market: '越南',
      type: 'policy' as const,
      severity: 'medium' as const,
      description: '越南计划从下季度起调整增值税税率，从10%降至8%，这可能影响部分商品的定价策略。',
      date: '2天前',
    },
  ];

  return alerts[index % alerts.length];
}
