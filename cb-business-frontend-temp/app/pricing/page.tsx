import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Check } from 'lucide-react';
import Link from 'next/link';

const plans = [
  {
    name: "免费版",
    price: "¥0",
    period: "/月",
    features: [
      { name: "基础市场数据", included: true },
      { name: "每日5次API调用", included: true },
      { name: "社区支持", included: true },
      { name: "AI机会分析", included: false },
      { name: "风险预警", included: false },
      { name: "成本计算器", included: false },
      { name: "数据导出", included: false },
    ],
    cta: "免费注册",
    highlighted: false,
  },
  {
    name: "专业版",
    price: "¥99",
    period: "/月",
    features: [
      { name: "全部市场数据", included: true },
      { name: "无限API调用", included: true },
      { name: "AI机会分析", included: true },
      { name: "风险预警", included: true },
      { name: "成本计算器", included: true },
      { name: "Excel导出", included: true },
      { name: "邮件支持", included: true },
    ],
    cta: "开始试用",
    highlighted: true,
    badge: "最受欢迎",
  },
];

function PricingCard({ plan }: { plan: typeof plans[0] }) {
  return (
    <Card className={`p-8 ${plan.highlighted ? 'border-primary border-2 shadow-lg' : ''}`}>
      {plan.badge && (
        <div className="text-center mb-4">
          <span className="bg-primary text-primary-foreground px-3 py-1 rounded-full text-sm font-medium">
            {plan.badge}
          </span>
        </div>
      )}
      <h3 className="text-2xl font-bold text-center mb-2">{plan.name}</h3>
      <div className="text-center mb-6">
        <span className="text-4xl font-bold">{plan.price}</span>
        <span className="text-muted-foreground">{plan.period}</span>
      </div>
      <ul className="space-y-3 mb-8">
        {plan.features.map((feature) => (
          <li key={feature.name} className="flex items-center gap-2">
            {feature.included ? (
              <Check className="text-primary h-5 w-5 flex-shrink-0" />
            ) : (
              <span className="h-5 w-4 flex-shrink-0" />
            )}
            <span className={feature.included ? '' : 'text-muted-foreground'}>
              {feature.name}
            </span>
          </li>
        ))}
      </ul>
      <Link href={plan.price === "¥0" ? "/register" : "/dashboard"} className="block">
        <Button
          className="w-full"
          variant={plan.highlighted ? 'default' : 'outline'}
        >
          {plan.cta}
        </Button>
      </Link>
    </Card>
  );
}

export default function PricingPage() {
  return (
    <div className="container mx-auto px-4 py-16">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">选择适合您的计划</h1>
        <p className="text-xl text-muted-foreground mb-2">
          随时升级，随时取消，无隐藏费用
        </p>
        <p className="text-sm text-muted-foreground">
          开始您的跨境电商之旅
        </p>
      </div>

      {/* Pricing Cards */}
      <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto mb-16">
        {plans.map((plan) => (
          <PricingCard key={plan.name} plan={plan} />
        ))}
      </div>

      {/* Feature Comparison */}
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-center mb-8">功能对比</h2>
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-4 font-semibold">功能</th>
                  <th className="text-center p-4 font-semibold">免费版</th>
                  <th className="text-center p-4 font-semibold">专业版</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                <tr>
                  <td className="p-4">市场数据</td>
                  <td className="p-4 text-center text-muted-foreground">基础数据</td>
                  <td className="p-4 text-center text-primary font-medium">全部市场</td>
                </tr>
                <tr>
                  <td className="p-4">API调用</td>
                  <td className="p-4 text-center text-muted-foreground">5次/天</td>
                  <td className="p-4 text-center text-primary font-medium">无限次</td>
                </tr>
                <tr>
                  <td className="p-4">AI分析</td>
                  <td className="p-4 text-center text-muted-foreground">—</td>
                  <td className="p-4 text-center text-primary font-medium">✓</td>
                </tr>
                <tr>
                  <td className="p-4">成本计算器</td>
                  <td className="p-4 text-center text-muted-foreground">—</td>
                  <td className="p-4 text-center text-primary font-medium">✓</td>
                </tr>
                <tr>
                  <td className="p-4">风险预警</td>
                  <td className="p-4 text-center text-muted-foreground">—</td>
                  <td className="p-4 text-center text-primary font-medium">✓</td>
                </tr>
                <tr>
                  <td className="p-4">数据导出</td>
                  <td className="p-4 text-center text-muted-foreground">—</td>
                  <td className="p-4 text-center text-primary font-medium">✓ Excel</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* FAQ */}
      <div className="max-w-2xl mx-auto mt-16">
        <h2 className="text-2xl font-bold text-center mb-8">常见问题</h2>
        <div className="space-y-4">
          <Card className="p-6">
            <h3 className="font-semibold mb-2">我可以随时取消吗？</h3>
            <p className="text-sm text-muted-foreground">是的，您可以随时取消订阅，无需任何理由。</p>
          </Card>
          <Card className="p-6">
            <h3 className="font-semibold mb-2">专业版支持多少个市场？</h3>
            <p className="text-sm text-muted-foreground">支持所有市场数据，包括东南亚、欧美、拉美、中东等主要市场。</p>
          </Card>
          <Card className="p-6">
            <h3 className="font-semibold mb-2">如何开始试用？</h3>
            <p className="text-sm text-muted-foreground">点击"开始试用"按钮，注册后即可享受7天免费试用。</p>
          </Card>
        </div>
      </div>
    </div>
  );
}
