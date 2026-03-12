import Link from 'next/link';
import { Button } from '@/components/ui/button';

export function Header() {
  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold">
          CB Business
        </Link>
        <nav className="flex items-center gap-6">
          <Link href="/pricing" className="hover:text-primary">定价</Link>
          <Link href="/dashboard" className="hover:text-primary">Dashboard</Link>
          <Link href="/login">
            <Button variant="outline" size="sm">
              登录
            </Button>
          </Link>
          <Link href="/register">
            <Button size="sm">
              免费注册
            </Button>
          </Link>
        </nav>
      </div>
    </header>
  );
}
