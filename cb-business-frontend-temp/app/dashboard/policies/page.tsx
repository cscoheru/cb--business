'use client';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { AlertTriangle, AlertCircle, Info, Search, Filter, Calendar } from 'lucide-react';
import { useState } from 'react';

interface Policy {
  id: string;
  title: string;
  market: string;
  type: 'policy' | 'tariff' | 'compliance';
  severity: 'high' | 'medium' | 'low';
  date: string;
  effectiveDate: string;
  summary: string;
  impact: string;
}

const mockPolicies: Policy[] = [
  {
    id: '1',
    title: '印尼电子产品认证要求变更',
    market: '印度尼西亚',
    type: 'policy',
    severity: 'high',
    date: '2025-03-08',
    effectiveDate: '2025-04-01',
    summary: '印尼将实施新的电子产品SDPPI认证标准，认证周期延长至2-3周。',
    impact: '影响所有进口电子产品，建议提前申请认证。'
  },
  {
    id: '2',
    title: '欧盟对中国电动车加征关税',
    market: '欧盟',
    type: 'tariff',
    severity: 'high',
    date: '2025-03-05',
    effectiveDate: '2025-03-15',
    summary: '欧盟对中国电动车征收17.4%-37.6%临时关税。',
    impact: '电动车及相关产品出口利润将受影响，需重新评估定价。'
  },
  {
    id: '3',
    title: '泰国FDA进口食品新规',
    market: '泰国',
    type: 'compliance',
    severity: 'medium',
    date: '2025-03-01',
    effectiveDate: '2025-04-01',
    summary: '要求所有进口食品提供泰语标签和营养成分表。',
    impact: '需更新产品包装和标签设计，确保符合新规。'
  },
  {
    id: '4',
    title: '越南增值税税率调整',
    market: '越南',
    type: 'policy',
    severity: 'medium',
    date: '2025-02-28',
    effectiveDate: '2025-07-01',
    summary: '增值税从10%下调至8%。',
    impact: '可能影响产品定价策略，建议重新核算成本。'
  },
];

function PolicyCard({ policy }: { policy: Policy }) {
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

  const typeInfo = typeConfig[policy.type];
  const severityInfo = severityConfig[policy.severity];
  const TypeIcon = typeInfo.icon;

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${typeInfo.color}/10`}>
            <TypeIcon className={`h-5 w-5 ${typeInfo.color.replace('bg-', 'text-')}`} />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="outline">{policy.market}</Badge>
              <Badge variant={severityInfo.color as any}>{severityInfo.label}</Badge>
            </div>
            <h3 className="text-lg font-semibold">{policy.title}</h3>
          </div>
        </div>
        <span className="text-xs text-muted-foreground">{policy.date}</span>
      </div>

      <p className="text-sm mb-3">{policy.summary}</p>

      <div className="bg-muted p-3 rounded-lg mb-4">
        <div className="text-xs text-muted-foreground mb-1">影响评估</div>
        <p className="text-sm">{policy.impact}</p>
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <div className="flex items-center gap-1">
          <Calendar className="h-4 w-4" />
          <span>生效日期：{policy.effectiveDate}</span>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline">详情</Button>
          <Button size="sm" variant="ghost">设置提醒</Button>
        </div>
      </div>
    </Card>
  );
}

export default function PoliciesPage() {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">政策中心</h1>
        <p className="text-muted-foreground">
          实时跟踪全球市场政策、关税和合规要求变化
        </p>
      </div>

      {/* Search and Filter */}
      <Card className="p-6 mb-8">
        <div className="flex items-center gap-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索政策..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" className="gap-2">
            <Filter className="h-4 w-4" />
            筛选
          </Button>
        </div>

        {/* Filter Tags */}
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary" className="cursor-pointer hover:bg-secondary/80">
            全部类型
          </Badge>
          <Badge variant="outline" className="cursor-pointer hover:bg-secondary">
            <AlertTriangle className="h-3 w-3 mr-1" />
            政策变更
          </Badge>
          <Badge variant="outline" className="cursor-pointer hover:bg-secondary">
            <AlertCircle className="h-3 w-3 mr-1" />
            关税调整
          </Badge>
          <Badge variant="outline" className="cursor-pointer hover:bg-secondary">
            <Info className="h-3 w-3 mr-1" />
            合规要求
          </Badge>
        </div>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="all" className="space-y-6">
        <TabsList className="grid w-full max-w-md grid-cols-4">
          <TabsTrigger value="all">全部政策</TabsTrigger>
          <TabsTrigger value="high">高风险</TabsTrigger>
          <TabsTrigger value="following">我的关注</TabsTrigger>
          <TabsTrigger value="archive">历史政策</TabsTrigger>
        </TabsList>

        {/* Policies List */}
        <TabsContent value="all" className="space-y-4">
          {mockPolicies.map((policy) => (
            <PolicyCard key={policy.id} policy={policy} />
          ))}
        </TabsContent>

        {/* High Risk Policies */}
        <TabsContent value="high" className="space-y-4">
          {mockPolicies.filter(p => p.severity === 'high').map((policy) => (
            <PolicyCard key={policy.id} policy={policy} />
          ))}
        </TabsContent>

        {/* Following */}
        <TabsContent value="following" className="space-y-4">
          <Card className="p-12 text-center text-muted-foreground">
            <p>还没有关注任何政策</p>
            <p className="text-sm mt-2">设置关注条件后，相关政策变化会第一时间通知您</p>
          </Card>
        </TabsContent>

        {/* Archive */}
        <TabsContent value="archive" className="space-y-4">
          <Card className="p-12 text-center text-muted-foreground">
            <p>暂无历史政策记录</p>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Setup Alerts */}
      <Card className="mt-8 p-6 bg-muted">
        <div className="text-center">
          <h3 className="text-xl font-semibold mb-2">设置政策预警</h3>
          <p className="text-muted-foreground mb-4">
            选择您关注的市场和政策类型，我们将第一时间通知您重要变化
          </p>
          <Button>配置预警规则</Button>
        </div>
      </Card>
    </div>
  );
}
