import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function DemoPage() {
  return (
    <div className="min-h-screen py-12">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold mb-4">
              产品演示
            </h1>
            <p className="text-xl text-muted-foreground">
              了解CB Business如何帮助您发现跨境电商机会
            </p>
          </div>

          {/* Demo Video/Content Placeholder */}
          <div className="bg-muted rounded-lg p-12 text-center mb-8">
            <div className="text-6xl mb-4">🎬</div>
            <h3 className="text-2xl font-semibold mb-2">
              产品演示视频
            </h3>
            <p className="text-muted-foreground mb-6">
              敬请期待...
            </p>
          </div>

          {/* Feature Highlights */}
          <div className="grid md:grid-cols-2 gap-6 mb-12">
            <div className="border rounded-lg p-6">
              <div className="text-4xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold mb-2">
                市场机会发现
              </h3>
              <p className="text-muted-foreground">
                AI驱动的市场分析，帮您找到蓝海市场
              </p>
            </div>

            <div className="border rounded-lg p-6">
              <div className="text-4xl mb-4">⚠️</div>
              <h3 className="text-xl font-semibold mb-2">
                政策风险预警
              </h3>
              <p className="text-muted-foreground">
                实时监控各国政策变化，及时预警风险
              </p>
            </div>

            <div className="border rounded-lg p-6">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-semibold mb-2">
                数据分析报告
              </h3>
              <p className="text-muted-foreground">
                详细的市场数据和趋势分析报告
              </p>
            </div>

            <div className="border rounded-lg p-6">
              <div className="text-4xl mb-4">💡</div>
              <h3 className="text-xl font-semibold mb-2">
                智能推荐
              </h3>
              <p className="text-muted-foreground">
                基于您的需求，智能推荐最适合的市场
              </p>
            </div>
          </div>

          {/* CTA */}
          <div className="text-center bg-muted rounded-lg p-8">
            <h2 className="text-2xl font-bold mb-4">
              准备开始了吗？
            </h2>
            <p className="text-muted-foreground mb-6">
              立即注册，免费体验所有功能
            </p>
            <div className="flex gap-4 justify-center">
              <Link href="/register">
                <Button size="lg">
                  免费注册
                </Button>
              </Link>
              <Link href="/pricing">
                <Button size="lg" variant="outline">
                  查看定价
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
