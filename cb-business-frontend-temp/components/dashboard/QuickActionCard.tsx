import { Card } from '@/components/ui/card';
import { ArrowRight } from 'lucide-react';
import Link from 'next/link';

interface QuickActionCardProps {
  icon: string;
  title: string;
  description: string;
  href: string;
}

export function QuickActionCard({ icon, title, description, href }: QuickActionCardProps) {
  return (
    <Link href={href}>
      <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer h-full">
        <div className="text-4xl mb-4">{icon}</div>
        <h3 className="text-xl font-semibold mb-2">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
        <div className="flex items-center text-primary mt-4">
          <span className="text-sm">立即查看</span>
          <ArrowRight className="w-4 h-4 ml-1" />
        </div>
      </Card>
    </Link>
  );
}
