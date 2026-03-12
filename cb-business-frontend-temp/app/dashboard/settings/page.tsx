'use client';

import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { User, Bell, Globe, Shield, CreditCard, HelpCircle, Moon, Sun } from 'lucide-react';
import { useState } from 'react';

export default function SettingsPage() {
  const [darkMode, setDarkMode] = useState(false);
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    sms: false,
  });

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">设置</h1>
        <p className="text-muted-foreground">
          管理您的账户、偏好和订阅设置
        </p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full max-w-lg grid-cols-5">
          <TabsTrigger value="profile">个人资料</TabsTrigger>
          <TabsTrigger value="preferences">偏好设置</TabsTrigger>
          <TabsTrigger value="notifications">通知设置</TabsTrigger>
          <TabsTrigger value="subscription">订阅管理</TabsTrigger>
          <TabsTrigger value="billing">账单管理</TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-6">个人信息</h2>

            <div className="flex items-center gap-6 mb-6">
              <Avatar className="h-20 w-20 text-2xl">
                <User className="h-10 w-10" />
              </Avatar>
              <div>
                <Button variant="outline" size="sm">更换头像</Button>
              </div>
            </div>

            <div className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">姓名</Label>
                  <Input id="name" placeholder="您的姓名" />
                </div>
                <div>
                  <Label htmlFor="email">邮箱</Label>
                  <Input id="email" type="email" placeholder="your@email.com" />
                </div>
              </div>

              <div>
                <Label htmlFor="company">公司名称</Label>
                <Input id="company" placeholder="您的公司名称（选填）" />
              </div>

              <div>
                <Label htmlFor="phone">手机号</Label>
                <Input id="phone" type="tel" placeholder="+86 13800000000" />
              </div>

              <Button>保存更改</Button>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">密码</h2>
            <div className="space-y-4 max-w-md">
              <div>
                <Label htmlFor="current-password">当前密码</Label>
                <Input id="current-password" type="password" />
              </div>
              <div>
                <Label htmlFor="new-password">新密码</Label>
                <Input id="new-password" type="password" />
              </div>
              <div>
                <Label htmlFor="confirm-password">确认新密码</Label>
                <Input id="confirm-password" type="password" />
              </div>
              <Button variant="outline">更新密码</Button>
            </div>
          </Card>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-6">外观和语言</h2>

            <div className="space-y-6">
              <div>
                <Label>主题模式</Label>
                <div className="flex items-center gap-4 mt-2">
                  <Button
                    variant={darkMode ? "outline" : "default"}
                    size="sm"
                    onClick={() => setDarkMode(false)}
                  >
                    <Sun className="h-4 w-4 mr-2" />
                    浅色
                  </Button>
                  <Button
                    variant={!darkMode ? "outline" : "default"}
                    size="sm"
                    onClick={() => setDarkMode(true)}
                  >
                    <Moon className="h-4 w-4 mr-2" />
                    深色
                  </Button>
                </div>
              </div>

              <div>
                <Label htmlFor="language">语言</Label>
                <select
                  id="language"
                  className="w-full mt-2 border rounded-lg px-3 py-2"
                >
                  <option value="zh-CN">简体中文</option>
                  <option value="en-US">English</option>
                  <option value="ja-JP">日本語</option>
                </select>
              </div>

              <div>
                <Label htmlFor="timezone">时区</Label>
                <select
                  id="timezone"
                  className="w-full mt-2 border rounded-lg px-3 py-2"
                >
                  <option value="Asia/Shanghai">中国标准时间 (UTC+8)</option>
                  <option value="Asia/Jakarta">印尼西部时间 (UTC+7)</option>
                  <option value="Europe/London">格林威治时间 (UTC+0)</option>
                  <option value="America/New_York">美东时间 (UTC-5)</option>
                </select>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">默认市场偏好</h2>
            <div className="space-y-4">
              <div>
                <Label htmlFor="primary-market">主要关注市场</Label>
                <select
                  id="primary-market"
                  className="w-full mt-2 border rounded-lg px-3 py-2"
                >
                  <option value="">选择市场</option>
                  <option value="sea">东南亚</option>
                  <option value="eu">欧盟</option>
                  <option value="us">美国</option>
                  <option value="latam">拉美</option>
                </select>
              </div>

              <div>
                <Label htmlFor="primary-category">主要关注品类</Label>
                <select
                  id="primary-category"
                  className="w-full mt-2 border rounded-lg px-3 py-2"
                >
                  <option value="">选择品类</option>
                  <option value="electronics">电子产品</option>
                  <option value="fashion">时尚服饰</option>
                  <option value="beauty">美妆个护</option>
                  <option value="home">家居用品</option>
                </select>
              </div>

              <Button>保存偏好</Button>
            </div>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-6">通知方式</h2>

            <div className="space-y-4">
              <div className="flex items-center justify-between py-3 border-b">
                <div>
                  <div className="font-medium">邮件通知</div>
                  <div className="text-sm text-muted-foreground">
                    接收重要政策变化和机会提醒
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.email}
                  onChange={(e) => setNotifications({ ...notifications, email: e.target.checked })}
                  className="w-5 h-5"
                />
              </div>

              <div className="flex items-center justify-between py-3 border-b">
                <div>
                  <div className="font-medium">浏览器推送</div>
                  <div className="text-sm text-muted-foreground">
                    实时接收高风险预警通知
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.push}
                  onChange={(e) => setNotifications({ ...notifications, push: e.target.checked })}
                  className="w-5 h-5"
                />
              </div>

              <div className="flex items-center justify-between py-3">
                <div>
                  <div className="font-medium">短信通知</div>
                  <div className="text-sm text-muted-foreground">
                    接收紧急风险通知（需升级）
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.sms}
                  onChange={(e) => setNotifications({ ...notifications, sms: e.target.checked })}
                  disabled
                  className="w-5 h-5"
                />
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">通知类型</h2>
            <div className="space-y-3">
              {[
                { name: '高风险预警', desc: '重要政策变化和关税调整', tag: '重要' },
                { name: '新机会推荐', desc: 'AI为您发现的市场机会', tag: '推荐' },
                { name: '周报', desc: '每周市场动态汇总', tag: '报告' },
                { name: '产品更新', desc: '新功能和改进通知', tag: '系统' },
              ].map((item) => (
                <div key={item.name} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div>
                    <div className="font-medium flex items-center gap-2">
                      {item.name}
                      <Badge variant="outline" className="text-xs">{item.tag}</Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">{item.desc}</div>
                  </div>
                  <input type="checkbox" defaultChecked className="w-5 h-5" />
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        {/* Subscription Tab */}
        <TabsContent value="subscription" className="space-y-6">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold">当前订阅</h2>
                <p className="text-sm text-muted-foreground">管理您的订阅计划</p>
              </div>
              <Badge variant="outline">免费版</Badge>
            </div>

            <div className="bg-muted p-6 rounded-lg mb-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">免费版</h3>
                  <p className="text-sm text-muted-foreground">¥0/月</p>
                </div>
                <Button size="sm">升级到专业版</Button>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-primary" />
                  <span>基础市场数据</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-primary" />
                  <span>每日5次API调用</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <div className="w-2 h-2 rounded-full bg-muted-foreground" />
                  <span>AI机会分析（专业版功能）</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <div className="w-2 h-2 rounded-full bg-muted-foreground" />
                  <span>风险预警（专业版功能）</span>
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <Button variant="outline">查看专业版功能</Button>
              <Button>立即升级</Button>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">订阅历史</h2>
            <div className="text-center text-muted-foreground py-8">
              <p>暂无订阅历史</p>
            </div>
          </Card>
        </TabsContent>

        {/* Billing Tab */}
        <TabsContent value="billing" className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">账单历史</h2>
            <div className="text-center text-muted-foreground py-8">
              <p>暂无账单记录</p>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">付款方式</h2>
            <div className="text-center text-muted-foreground py-8">
              <p>暂无付款方式</p>
              <Button className="mt-4">添加付款方式</Button>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
