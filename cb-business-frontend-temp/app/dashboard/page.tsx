import { Card } from '@/components/ui/card';
import { JourneyTracker } from '@/components/dashboard/JourneyTracker';
import { QuickActionCard } from '@/components/dashboard/QuickActionCard';
import { OpportunityCard, mockOpportunityCard } from '@/components/dashboard/OpportunityCard';
import Link from 'next/link';

export default function DashboardPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">
          早上好，创业者！
        </h1>
        <p className="text-muted-foreground">
          今天有 <span className="text-primary font-bold">3个</span> 新机会等待您
        </p>
      </div>

      {/* User Journey Tracker */}
      <JourneyTracker />

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-6 my-8">
        <QuickActionCard
          icon="🔍"
          title="发现机会"
          description="查看AI推荐的新机会"
          href="/dashboard/opportunities"
        />
        <QuickActionCard
          icon="⚠️"
          title="风险预警"
          description="查看最新风险提示"
          href="/dashboard/risks"
        />
        <QuickActionCard
          icon="💰"
          title="成本计算"
          description="计算产品成本和利润"
          href="/dashboard/tools/cost-calculator"
        />
      </div>

      {/* Recommended Opportunities */}
      <section className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">为您推荐</h2>
          <Link href="/dashboard/opportunities" className="text-primary text-sm hover:underline">
            查看全部 →
          </Link>
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          <OpportunityCard {...mockOpportunityCard(0)} />
          <OpportunityCard {...mockOpportunityCard(1)} />
        </div>
      </section>

      {/* Recent Alerts */}
      <section className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">最新风险预警</h2>
          <Link href="/dashboard/risks" className="text-primary text-sm hover:underline">
            查看全部 →
          </Link>
        </div>
        <Card className="p-6 text-center text-muted-foreground">
          <p>暂无新风险预警</p>
          <p className="text-sm mt-2">我们会持续监控您关注市场的政策变化</p>
        </Card>
      </section>

      {/* Quick Stats */}
      <section className="mt-8">
        <h2 className="text-2xl font-bold mb-4">数据概览</h2>
        <div className="grid md:grid-cols-4 gap-6">
          <Card className="p-6">
            <div className="text-2xl font-bold mb-1">12</div>
            <div className="text-sm text-muted-foreground">已保存的机会</div>
          </Card>
          <Card className="p-6">
            <div className="text-2xl font-bold mb-1">3</div>
            <div className="text-sm text-muted-foreground">关注的市场</div>
          </Card>
          <Card className="p-6">
            <div className="text-2xl font-bold mb-1">5</div>
            <div className="text-sm text-muted-foreground">成本计算次数</div>
          </Card>
          <Card className="p-6">
            <div className="text-2xl font-bold mb-1">2</div>
            <div className="text-sm text-muted-foreground">活跃预警</div>
          </Card>
        </div>
      </section>
    </div>
  );
}
