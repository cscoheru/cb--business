'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { RiskAlertCard, mockRiskAlertCard } from '@/components/dashboard/RiskAlertCard';
import { Search, SlidersHorizontal, AlertTriangle, AlertCircle, Info, Globe } from 'lucide-react';
import { useState } from 'react';

export default function RisksPage() {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">风险预警</h1>
        <p className="text-muted-foreground">
          实时监控全球市场政策、关税和合规变化
        </p>
      </div>

      {/* Filters */}
      <Card className="p-6 mb-8">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索风险预警..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <Button variant="outline" className="gap-2">
            <SlidersHorizontal className="h-4 w-4" />
            筛选
          </Button>
        </div>

        {/* Filter Tags */}
        <div className="flex flex-wrap gap-2 mt-4">
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

        {/* Severity Filter */}
        <div className="flex flex-wrap gap-2 mt-3">
          <Badge variant="destructive" className="cursor-pointer">
            高风险
          </Badge>
          <Badge variant="secondary" className="cursor-pointer">
            中风险
          </Badge>
          <Badge variant="outline" className="cursor-pointer">
            低风险
          </Badge>
        </div>
      </Card>

      {/* Stats */}
      <div className="grid md:grid-cols-4 gap-6 mb-8">
        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-red-500/10 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-red-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">8</div>
              <div className="text-sm text-muted-foreground">高风险预警</div>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-yellow-500/10 rounded-lg">
              <AlertCircle className="h-6 w-6 text-yellow-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">23</div>
              <div className="text-sm text-muted-foreground">中风险预警</div>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-500/10 rounded-lg">
              <Info className="h-6 w-6 text-blue-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">45</div>
              <div className="text-sm text-muted-foreground">低风险预警</div>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-500/10 rounded-lg">
              <Globe className="h-6 w-6 text-purple-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">12</div>
              <div className="text-sm text-muted-foreground">覆盖市场</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Alerts List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">最新预警</h2>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">排序：</span>
            <select className="border rounded-lg px-3 py-1.5 text-sm">
              <option>严重程度</option>
              <option>发布时间</option>
            </select>
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          <RiskAlertCard {...mockRiskAlertCard(0)} />
          <RiskAlertCard {...mockRiskAlertCard(1)} />
          <RiskAlertCard {...mockRiskAlertCard(2)} />
          <RiskAlertCard {...mockRiskAlertCard(3)} />
        </div>

        {/* Load More */}
        <div className="text-center mt-8">
          <Button variant="outline">加载更多</Button>
        </div>
      </div>

      {/* Setup Alerts Section */}
      <Card className="mt-8 p-6 bg-muted">
        <div className="text-center">
          <h3 className="text-xl font-semibold mb-2">设置预警规则</h3>
          <p className="text-muted-foreground mb-4">
            自定义您关注的市场和产品类型，我们会在有风险时第一时间通知您
          </p>
          <Button>配置预警规则</Button>
        </div>
      </Card>
    </div>
  );
}
