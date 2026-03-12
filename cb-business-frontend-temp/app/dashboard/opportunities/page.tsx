'use client';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { OpportunityCard, mockOpportunityCard } from '@/components/dashboard/OpportunityCard';
import { Search, SlidersHorizontal, TrendingUp, DollarSign, Package, Globe } from 'lucide-react';
import { useState } from 'react';

export default function OpportunitiesPage() {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">机会发现</h1>
        <p className="text-muted-foreground">
          AI 为您分析全球市场，发现跨境电商新机会
        </p>
      </div>

      {/* Filters */}
      <Card className="p-6 mb-8">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索机会..."
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
            全部市场
          </Badge>
          <Badge variant="outline" className="cursor-pointer hover:bg-secondary">
            东南亚
          </Badge>
          <Badge variant="outline" className="cursor-pointer hover:bg-secondary">
            欧美
          </Badge>
          <Badge variant="outline" className="cursor-pointer hover:bg-secondary">
            拉美
          </Badge>
          <Badge variant="outline" className="cursor-pointer hover:bg-secondary">
            中东
          </Badge>
          <Badge variant="outline" className="cursor-pointer hover:bg-secondary">
            非洲
          </Badge>
        </div>
      </Card>

      {/* Stats */}
      <div className="grid md:grid-cols-4 gap-6 mb-8">
        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-500/10 rounded-lg">
              <TrendingUp className="h-6 w-6 text-blue-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">156</div>
              <div className="text-sm text-muted-foreground">总机会数</div>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-500/10 rounded-lg">
              <DollarSign className="h-6 w-6 text-green-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">23</div>
              <div className="text-sm text-muted-foreground">高潜力</div>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-500/10 rounded-lg">
              <Package className="h-6 w-6 text-purple-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">89</div>
              <div className="text-sm text-muted-foreground">产品类别</div>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-orange-500/10 rounded-lg">
              <Globe className="h-6 w-6 text-orange-500" />
            </div>
            <div>
              <div className="text-2xl font-bold">12</div>
              <div className="text-sm text-muted-foreground">覆盖市场</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Opportunities List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">推荐机会</h2>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">排序：</span>
            <select className="border rounded-lg px-3 py-1.5 text-sm">
              <option>相关度排序</option>
              <option>潜力高低</option>
              <option>最新发布</option>
            </select>
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          <OpportunityCard {...mockOpportunityCard(0)} />
          <OpportunityCard {...mockOpportunityCard(1)} />
          <OpportunityCard {...mockOpportunityCard(2)} />
          <OpportunityCard {...mockOpportunityCard(3)} />
        </div>

        {/* Load More */}
        <div className="text-center mt-8">
          <Button variant="outline">加载更多</Button>
        </div>
      </div>
    </div>
  );
}
