import Link from 'next/link';

const FUN_MODULES = [
  {
    emoji: '🪞',
    title: '个人能力照妖镜',
    description: '测测你的跨境电商潜力',
    detail: '5分钟快速评估，发现你的优势与短板',
    tag: '免费',
    tagColor: 'green',
    stats: '1.2万人已测',
    href: '/assessment',
  },
  {
    emoji: '📦',
    title: '资源盘点',
    description: '清点你的创业弹药库',
    detail: '资金、时间、技能...你手里有什么牌？',
    tag: '工具',
    tagColor: 'blue',
    stats: '10分钟搞定',
    href: '/inventory',
  },
  {
    emoji: '🧭',
    title: '喜欢到哪里去看看',
    description: '跟着兴趣探索市场',
    detail: '喜欢美妆？宠物？还是户外装备？看看哪个市场适合你',
    tag: '趣味',
    tagColor: 'purple',
    stats: '发现兴趣市场',
    href: '/interests',
  },
  {
    emoji: '📖',
    title: '跨境电商业主养成记',
    description: '从小白到卖家的成长地图',
    detail: '新手入门、进阶成长、突破瓶颈...你的创业路线图',
    tag: '系列',
    tagColor: 'orange',
    stats: '12个阶段',
    href: '/growth-path',
  },
];

const tagColors = {
  green: 'bg-green-50 text-green-600',
  blue: 'bg-blue-50 text-blue-600',
  purple: 'bg-purple-50 text-purple-600',
  orange: 'bg-orange-50 text-orange-600',
};

export function FunModules() {
  return (
    <section className="max-w-7xl mx-auto px-4 py-10">
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {FUN_MODULES.map((module) => (
          <Link
            key={module.href}
            href={module.href}
            className="card-hover bg-white rounded-lg p-5 border border-gray-200 block transition-all duration-200 hover:shadow-lg hover:-translate-y-1"
          >
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl">{module.emoji}</span>
              <div>
                <h3 className="font-semibold text-gray-900">{module.title}</h3>
                <p className="text-xs text-gray-500">{module.description}</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-3">{module.detail}</p>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className={`px-2 py-0.5 rounded ${tagColors[module.tagColor as keyof typeof tagColors]}`}>
                {module.tag}
              </span>
              <span>{module.stats}</span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
