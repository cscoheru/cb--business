import { Card } from '@/components/ui/card';
import { Check } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface JourneyStep {
  id: string;
  title: string;
  description: string;
  status: 'completed' | 'current' | 'locked';
}

const journeySteps: JourneyStep[] = [
  {
    id: '1',
    title: '选择目标市场',
    description: '选择您想了解的市场区域',
    status: 'completed',
  },
  {
    id: '2',
    title: '探索市场机会',
    description: '查看AI为您推荐的市场机会',
    status: 'completed',
  },
  {
    id: '3',
    title: '分析成本利润',
    description: '使用成本计算器评估可行性',
    status: 'current',
  },
  {
    id: '4',
    title: '寻找供应商',
    description: '从供应商数据库找到合适伙伴',
    status: 'locked',
  },
  {
    id: '5',
    title: '制定进入策略',
    description: '获取详细的市场进入方案',
    status: 'locked',
  },
];

export function JourneyTracker() {
  return (
    <Card className="p-6">
      <div className="mb-4">
        <h2 className="text-xl font-semibold mb-1">您的探索之旅</h2>
        <p className="text-sm text-muted-foreground">
          已完成 <span className="text-primary font-bold">2/5</span> 步骤
        </p>
      </div>

      <div className="space-y-4">
        {journeySteps.map((step, index) => (
          <div key={step.id} className="flex items-start gap-4">
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center
                  ${step.status === 'completed' ? 'bg-primary text-primary-foreground' : ''}
                  ${step.status === 'current' ? 'bg-primary/20 border-2 border-primary text-primary' : ''}
                  ${step.status === 'locked' ? 'bg-muted text-muted-foreground' : ''}
                `}
              >
                {step.status === 'completed' ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <span className="text-sm font-medium">{index + 1}</span>
                )}
              </div>
              {index < journeySteps.length - 1 && (
                <div className="w-0.5 h-full bg-border mt-2" />
              )}
            </div>

            <div className="flex-1 pb-8">
              <div className="flex items-center gap-2 mb-1">
                <h3 className={`font-semibold ${step.status === 'locked' ? 'text-muted-foreground' : ''}`}>
                  {step.title}
                </h3>
                {step.status === 'current' && (
                  <Badge variant="default" className="text-xs">进行中</Badge>
                )}
                {step.status === 'locked' && (
                  <Badge variant="outline" className="text-xs">专业版</Badge>
                )}
              </div>
              <p className={`text-sm ${step.status === 'locked' ? 'text-muted-foreground' : 'text-muted-foreground'}`}>
                {step.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
