# ZenConsult Website Redesign - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform ZenConsult from a basic article aggregator into an immersive, AI-powered cross-border e-commerce platform with exotic romantic aesthetics and interactive user features.

**Architecture:**
- Frontend: Next.js 15 with App Router, Server Components for data fetching, Client Components for interactivity
- Backend: FastAPI with Zhipu AI integration for personalized assessments
- State: React hooks for form state, localStorage for anonymous progress tracking
- Styling: Tailwind CSS with custom color variables for exotic romantic theme

**Tech Stack:**
- Next.js 15, TypeScript, Tailwind CSS, shadcn/ui
- Zhipu AI API for assessments
- PostgreSQL full-text search
- Redis for caching

---

## Phase 1: Visual Foundation (Color System & Layout)

### Task 1.1: Create Custom Color System

**Files:**
- Create: `frontend/app/globals.css`
- Modify: `frontend/tailwind.config.ts`

**Step 1: Add CSS custom properties to globals.css**

```css
:root {
  /* Primary Accent Colors - Exotic Romantic Theme */
  --light-green-primary: #90EE90;
  --light-green-secondary: #98FB98;
  --light-orange-primary: #FFB347;
  --light-orange-secondary: #FFDAB9;
  --light-purple-primary: #DDA0DD;
  --light-purple-secondary: #E6E6FA;

  /* Supporting Colors */
  --bg-warm: #FFFEF9;
  --bg-cream: #FFFDF5;
  --text-dark: #2D2D2D;
  --text-medium: #555555;
  --text-light: #888888;

  /* Gradients */
  --gradient-hero: linear-gradient(135deg, #90EE90 0%, #FFB347 50%, #DDA0DD 100%);
  --gradient-card: linear-gradient(to bottom, rgba(144,238,144,0.1), transparent);
}

[data-theme="southeast_asia"] {
  --accent-primary: #90EE90;
  --accent-secondary: #98FB98;
}

[data-theme="north_america"] {
  --accent-primary: #DDA0DD;
  --accent-secondary: #E6E6FA;
}

[data-theme="latin_america"] {
  --accent-primary: #FFB347;
  --accent-secondary: #FFDAB9;
}
```

**Step 2: Update Tailwind config to use custom colors**

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "accent-green": "var(--light-green-primary)",
        "accent-orange": "var(--light-orange-primary)",
        "accent-purple": "var(--light-purple-primary)",
        "bg-warm": "var(--bg-warm)",
        "bg-cream": "var(--bg-cream)",
      },
      backgroundImage: {
        "gradient-hero": "var(--gradient-hero)",
        "gradient-card": "var(--gradient-card)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
```

**Step 3: Commit**

```bash
git add frontend/app/globals.css frontend/tailwind.config.ts
git commit -m "feat: add exotic romantic color system"
```

---

### Task 1.2: Reorder Homepage Sections

**Files:**
- Modify: `frontend/app/page.tsx`

**Step 1: Write component test for page structure**

```typescript
// frontend/__tests__/page-order.test.tsx
import { render, screen } from '@testing-library/react';
import HomePage from '@/app/page';

describe('HomePage section order', () => {
  it('renders sections in correct order', () => {
    render(<HomePage />);

    const sections = screen.getAllByRole('region');
    const sectionOrder = sections.map(el => el.getAttribute('data-section'));

    expect(sectionOrder).toEqual([
      'hero',
      'region-cards',
      'function-cards',
      'theme-portals',
      'cta'
    ]);
  });
});
```

**Step 2: Run test to verify it fails (current order is wrong)**

```bash
cd frontend && npm test -- page-order.test.tsx
```
Expected: FAIL - sections in wrong order

**Step 3: Reorder sections in page.tsx**

```typescript
// frontend/app/page.tsx
import Link from 'next/link';
import { Suspense } from 'react';
import { articlesApi } from '@/lib/api';
import { Header } from '@/components/layout/header';
import { Footer } from '@/components/layout/footer';
import { HeroSearch } from '@/components/home/hero-search';
import { RegionCards } from '@/components/home/region-cards';
import { FunctionCards } from '@/components/home/function-cards';
import { ThemePortals } from '@/components/home/theme-portals';
import { CTASection } from '@/components/home/cta-section';

export default async function HomePage() {
  // Fetch initial articles for region cards
  const articles = await articlesApi.getArticles({ per_page: 50 });

  return (
    <div className="min-h-screen bg-bg-warm">
      <Header />
      <main>
        {/* Hero with search */}
        <section data-section="hero" className="bg-gradient-hero">
          <HeroSearch />
        </section>

        {/* Region Cards - MOVED UP */}
        <section data-section="region-cards" className="py-10">
          <RegionCards articles={articles.articles} />
        </section>

        {/* Function Cards - MOVED DOWN */}
        <section data-section="function-cards" className="py-10 bg-bg-cream">
          <FunctionCards />
        </section>

        {/* Theme Portals - unchanged position */}
        <section data-section="theme-portals" className="py-10">
          <ThemePortals articles={articles.articles} />
        </section>

        {/* CTA Section */}
        <section data-section="cta" className="py-16 bg-gradient-card">
          <CTASection />
        </section>
      </main>
      <Footer />
    </div>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- page-order.test.tsx
```
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/app/page.tsx frontend/__tests__/page-order.test.tsx
git commit -m "refactor: reorder homepage sections (region up, functions down)"
```

---

## Phase 2: Region Cards with Keyword Clouds

### Task 2.1: Create Keyword Configuration

**Files:**
- Create: `frontend/config/keywords/index.ts`

**Step 1: Write test for keyword config**

```typescript
// frontend/__tests__/keywords-config.test.ts
import { getKeywordsByRegion } from '@/config/keywords';

describe('Keyword configuration', () => {
  it('returns correct keywords for Southeast Asia', () => {
    const keywords = getKeywordsByRegion('southeast_asia');

    expect(keywords.countries).toContain('泰国');
    expect(keywords.platforms).toContain('Shopee');
    expect(keywords.categories).toContain('美妆');
  });

  it('returns correct keywords for Latin America', () => {
    const keywords = getKeywordsByRegion('latin_america');

    expect(keywords.countries).toContain('巴西');
    expect(keywords.platforms).toContain('Mercado Libre');
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- keywords-config.test.ts
```
Expected: FAIL - config doesn't exist

**Step 3: Create keyword configuration**

```typescript
// frontend/config/keywords/index.ts

export interface RegionKeywords {
  countries: string[];
  platforms: string[];
  categories: string[];
}

const KEYWORDS: Record<string, RegionKeywords> = {
  southeast_asia: {
    countries: ['泰国', '越南', '马来西亚', '印尼', '菲律宾', '新加坡'],
    platforms: ['Shopee', 'Lazada', 'TikTok Shop'],
    categories: ['美妆', '电子', '家居', '服饰', '食品']
  },
  north_america: {
    countries: ['美国', '加拿大'],
    platforms: ['Amazon', 'eBay', 'Walmart', 'Shopify'],
    categories: ['电子', '家居', '户外', '健康']
  },
  latin_america: {
    countries: ['巴西', '墨西哥', '阿根廷', '智利'],
    platforms: ['Mercado Libre', 'Amazon', 'Shopee'],
    categories: ['电子', '家居', '美妆', '服饰']
  }
};

export function getKeywordsByRegion(region: string): RegionKeywords {
  return KEYWORDS[region] || {
    countries: [],
    platforms: [],
    categories: []
  };
}

export function getAllRegions(): string[] {
  return Object.keys(KEYWORDS);
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- keywords-config.test.ts
```
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/config/keywords/ frontend/__tests__/keywords-config.test.ts
git commit -m "feat: add region keyword configuration"
```

---

### Task 2.2: Redesign Region Cards Component

**Files:**
- Modify: `frontend/components/home/region-cards.tsx`
- Create: `frontend/components/home/region-card.tsx`

**Step 1: Write test for region card with keywords**

```typescript
// frontend/__tests__/region-card.test.tsx
import { render, screen } from '@testing-library/react';
import { RegionCard } from '@/components/home/region-card';
import { getKeywordsByRegion } from '@/config/keywords';

describe('RegionCard', () => {
  it('displays keywords instead of articles', () => {
    const keywords = getKeywordsByRegion('southeast_asia');
    render(
      <RegionCard
        region="southeast_asia"
        keywords={keywords}
        articleCount={128}
      />
    );

    // Should show keywords
    expect(screen.getByText('泰国')).toBeInTheDocument();
    expect(screen.getByText('Shopee')).toBeInTheDocument();
    expect(screen.getByText('美妆')).toBeInTheDocument();

    // Should NOT show descriptive text
    expect(screen.queryByText('按地区探索资讯')).not.toBeInTheDocument();
    expect(screen.queryByText('实时更新')).not.toBeInTheDocument();
  });

  it('links keywords to country portals', () => {
    const keywords = getKeywordsByRegion('southeast_asia');
    render(
      <RegionCard
        region="southeast_asia"
        keywords={keywords}
        articleCount={128}
      />
    );

    const thailandLink = screen.getByText('泰国').closest('a');
    expect(thailandLink).toHaveAttribute('href', '/country/thailand');
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- region-card.test.tsx
```
Expected: FAIL - component doesn't exist or doesn't match

**Step 3: Create RegionCard component**

```typescript
// frontend/components/home/region-card.tsx
'use client';

import Link from 'next/link';
import { RegionKeywords } from '@/config/keywords';

interface RegionCardProps {
  region: string;
  keywords: RegionKeywords;
  articleCount: number;
}

const REGION_INFO: Record<string, { emoji: string; name: string; color: string }> = {
  southeast_asia: { emoji: '🌏', name: '东南亚', color: 'accent-green' },
  north_america: { emoji: '🇺🇸', name: '北美', color: 'accent-purple' },
  latin_america: { emoji: '🇧🇷', name: '拉美', color: 'accent-orange' }
};

const COUNTRY_SLUGS: Record<string, string> = {
  '泰国': 'thailand',
  '越南': 'vietnam',
  '马来西亚': 'malaysia',
  '印尼': 'indonesia',
  '菲律宾': 'philippines',
  '新加坡': 'singapore',
  '美国': 'usa',
  '加拿大': 'canada',
  '巴西': 'brazil',
  '墨西哥': 'mexico',
  '阿根廷': 'argentina',
  '智利': 'chile'
};

export function RegionCard({ region, keywords, articleCount }: RegionCardProps) {
  const info = REGION_INFO[region] || { emoji: '🌍', name: 'Region', color: 'gray' };

  return (
    <div className="card-hover bg-white rounded-lg p-6 border-2 border-${info.color} transition-all duration-200 hover:shadow-lg hover:-translate-y-1">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <span className="text-4xl">{info.emoji}</span>
        <div className="flex-1">
          <h3 className="font-semibold text-xl text-gray-900">{info.name}</h3>
          <p className="text-sm text-gray-500">{articleCount} 篇文章</p>
        </div>
      </div>

      {/* Keyword Cloud */}
      <div className="space-y-3 mb-4">
        {/* Countries */}
        <div className="flex flex-wrap gap-2">
          {keywords.countries.map(country => (
            <Link
              key={country}
              href={`/country/${COUNTRY_SLUGS[country] || country.toLowerCase()}`}
              className="text-xs px-3 py-1 rounded-full bg-${info.color}/10 text-${info.color} hover:bg-${info.color}/20 transition-colors"
            >
              {country}
            </Link>
          ))}
        </div>

        {/* Platforms */}
        <div className="flex flex-wrap gap-2">
          {keywords.platforms.map(platform => (
            <span
              key={platform}
              className="text-xs px-3 py-1 rounded-full bg-gray-100 text-gray-600"
            >
              {platform}
            </span>
          ))}
        </div>

        {/* Categories */}
        <div className="flex flex-wrap gap-2">
          {keywords.categories.map(category => (
            <span
              key={category}
              className="text-xs px-3 py-1 rounded-full bg-gray-50 text-gray-500"
            >
              {category}
            </span>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="pt-3 border-t border-gray-100 text-xs text-gray-400">
        点击国家名称进入详情 →
      </div>
    </div>
  );
}
```

**Step 4: Update RegionCards to use new component**

```typescript
// frontend/components/home/region-cards.tsx
import { RegionCard } from './region-card';
import { getKeywordsByRegion, getAllRegions } from '@/config/keywords';
import { Article } from '@/lib/api';

interface RegionCardsProps {
  articles: Article[];
}

export function RegionCards({ articles }: RegionCardsProps) {
  const regions = getAllRegions();

  // Count articles per region
  const articleCounts = regions.reduce((acc, region) => {
    acc[region] = articles.filter(a => a.region === region).length;
    return acc;
  }, {} as Record<string, number>);

  return (
    <section className="max-w-7xl mx-auto px-4">
      <div className="grid md:grid-cols-3 gap-6">
        {regions.map(region => (
          <RegionCard
            key={region}
            region={region}
            keywords={getKeywordsByRegion(region)}
            articleCount={articleCounts[region] || 0}
          />
        ))}
      </div>
    </section>
  );
}
```

**Step 5: Run test to verify it passes**

```bash
cd frontend && npm test -- region-card.test.tsx
```
Expected: PASS

**Step 6: Commit**

```bash
git add frontend/components/home/region-card.tsx frontend/components/home/region-cards.tsx frontend/__tests__/region-card.test.tsx
git commit -m "feat: redesign region cards with keyword clouds"
```

---

## Phase 3: Function Cards (Real Features)

### Task 3.1: Create Generic Assessment Form Component

**Files:**
- Create: `frontend/components/assessments/assessment-form.tsx`
- Create: `frontend/components/assessments/assessment-results.tsx`

**Step 1: Write test for assessment form**

```typescript
// frontend/__tests__/assessment-form.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AssessmentForm } from '@/components/assessments/assessment-form';

describe('AssessmentForm', () => {
  const mockQuestions = [
    {
      id: 'q1',
      text: 'Test question?',
      options: [
        { label: 'A', value: 'a', points: 1 },
        { label: 'B', value: 'b', points: 2 }
      ]
    }
  ];

  it('renders questions and options', () => {
    render(
      <AssessmentForm
        type="test"
        questions={mockQuestions}
        onSubmit={jest.fn()}
      />
    );

    expect(screen.getByText('Test question?')).toBeInTheDocument();
    expect(screen.getByText('A')).toBeInTheDocument();
    expect(screen.getByText('B')).toBeInTheDocument();
  });

  it('submits selected answers', async () => {
    const handleSubmit = jest.fn();
    render(
      <AssessmentForm
        type="test"
        questions={mockQuestions}
        onSubmit={handleSubmit}
      />
    );

    fireEvent.click(screen.getByText('A'));
    fireEvent.click(screen.getByText('提交评估'));

    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledWith({ q1: 'a' });
    });
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- assessment-form.test.tsx
```
Expected: FAIL - component doesn't exist

**Step 3: Create AssessmentForm component**

```typescript
// frontend/components/assessments/assessment-form.tsx
'use client';

import { useState } from 'react';

export interface Question {
  id: string;
  text: string;
  options: Array<{
    label: string;
    value: string;
    points: number;
  }>;
}

interface AssessmentFormProps {
  type: string;
  questions: Question[];
  onSubmit: (answers: Record<string, string>) => Promise<void>;
}

export function AssessmentForm({ type, questions, onSubmit }: AssessmentFormProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSelect = (questionId: string, value: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate all questions answered
    const unanswered = questions.filter(q => !answers[q.id]);
    if (unanswered.length > 0) {
      alert('请回答所有问题');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(answers);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {questions.map(question => (
        <div key={question.id} className="bg-white rounded-lg p-5 border border-gray-200">
          <h3 className="font-medium text-gray-900 mb-3">{question.text}</h3>
          <div className="grid grid-cols-2 gap-2">
            {question.options.map(option => (
              <label
                key={option.value}
                className={`
                  flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-colors
                  ${answers[question.id] === option.value
                    ? 'border-accent-green bg-accent-green/10'
                    : 'border-gray-200 hover:border-gray-300'
                  }
                `}
              >
                <input
                  type="radio"
                  name={question.id}
                  value={option.value}
                  checked={answers[question.id] === option.value}
                  onChange={() => handleSelect(question.id, option.value)}
                  className="w-4 h-4 text-accent-green"
                />
                <span className="text-sm text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
        </div>
      ))}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full py-3 px-6 bg-gradient-hero text-white font-medium rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
      >
        {isSubmitting ? '评估中...' : '提交评估'}
      </button>
    </form>
  );
}
```

**Step 4: Create AssessmentResults component**

```typescript
// frontend/components/assessments/assessment-results.tsx
'use client';

interface Result {
  score: number;
  level: string;
  recommendations: Array<{
    title: string;
    description: string;
    link: string;
  }>;
  nextSteps: string[];
}

interface AssessmentResultsProps {
  type: string;
  result: Result;
}

export function AssessmentResults({ type, result }: AssessmentResultsProps) {
  return (
    <div className="bg-white rounded-lg p-6 border-2 border-accent-green">
      {/* Score Display */}
      <div className="text-center mb-6">
        <div className="text-6xl mb-2">{result.score}</div>
        <div className="text-xl font-medium text-gray-900">{result.level}</div>
      </div>

      {/* Recommendations */}
      <div className="space-y-3 mb-6">
        <h3 className="font-semibold text-gray-900">为您推荐</h3>
        {result.recommendations.map((rec, index) => (
          <a
            key={index}
            href={rec.link}
            className="block p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <h4 className="font-medium text-gray-900">{rec.title}</h4>
            <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
          </a>
        ))}
      </div>

      {/* Next Steps */}
      <div className="border-t pt-4">
        <h3 className="font-semibold text-gray-900 mb-2">下一步行动</h3>
        <ul className="space-y-2">
          {result.nextSteps.map((step, index) => (
            <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
              <span className="text-accent-green">{index + 1}.</span>
              <span>{step}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

**Step 5: Run test to verify it passes**

```bash
cd frontend && npm test -- assessment-form.test.tsx
```
Expected: PASS

**Step 6: Commit**

```bash
git add frontend/components/assessments/ frontend/__tests__/assessment-form.test.tsx
git commit -m "feat: add generic assessment form and results components"
```

---

### Task 3.2: Implement Capability Assessment

**Files:**
- Create: `frontend/config/assessments/capability.ts`
- Create: `frontend/components/function-cards/capability-card.tsx`

**Step 1: Write test for capability assessment questions**

```typescript
// frontend/__tests__/capability-assessment.test.ts
import { getCapabilityQuestions, calculateCapabilityScore } from '@/config/assessments/capability';

describe('Capability Assessment', () => {
  it('has 4 questions with 4 options each', () => {
    const questions = getCapabilityQuestions();
    expect(questions).toHaveLength(4);
    questions.forEach(q => {
      expect(q.options).toHaveLength(4);
    });
  });

  it('calculates correct score ranges', () => {
    // All lowest options: 4 points
    expect(calculateCapabilityScore({ q1: 'a', q2: 'a', q3: 'a', q4: 'a' })).toBe(4);

    // All highest options: 16 points
    expect(calculateCapabilityScore({ q1: 'd', q2: 'd', q3: 'd', q4: 'd' })).toBe(16);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- capability-assessment.test.ts
```
Expected: FAIL - config doesn't exist

**Step 3: Create capability assessment configuration**

```typescript
// frontend/config/assessments/capability.ts
import { Question } from '@/components/assessments/assessment-form';

export function getCapabilityQuestions(): Question[] {
  return [
    {
      id: 'q1',
      text: '您的跨境电商经验？',
      options: [
        { label: '完全新手', value: 'a', points: 1 },
        { label: '了解一些，没做过', value: 'b', points: 2 },
        { label: '有1-2年经验', value: 'c', points: 3 },
        { label: '3年以上经验', value: 'd', points: 4 }
      ]
    },
    {
      id: 'q2',
      text: '每周可用时间？',
      options: [
        { label: '少于10小时（兼职）', value: 'a', points: 1 },
        { label: '10-20小时', value: 'b', points: 2 },
        { label: '20-30小时', value: 'c', points: 3 },
        { label: '30小时以上（全职）', value: 'd', points: 4 }
      ]
    },
    {
      id: 'q3',
      text: '启动资金准备？',
      options: [
        { label: '1万以下', value: 'a', points: 1 },
        { label: '1-5万', value: 'b', points: 2 },
        { label: '5-20万', value: 'c', points: 3 },
        { label: '20万以上', value: 'd', points: 4 }
      ]
    },
    {
      id: 'q4',
      text: '语言能力？',
      options: [
        { label: '仅中文', value: 'a', points: 1 },
        { label: '中文 + 基础英语', value: 'b', points: 2 },
        { label: '中文 + 流利英语', value: 'c', points: 3 },
        { label: '多语言能力', value: 'd', points: 4 }
      ]
    }
  ];
}

export function calculateCapabilityScore(answers: Record<string, string>): number {
  const questions = getCapabilityQuestions();
  return questions.reduce((total, question) => {
    const selected = question.options.find(opt => opt.value === answers[question.id]);
    return total + (selected?.points || 0);
  }, 0);
}

export function getCapabilityRecommendations(score: number) {
  if (score <= 5) {
    return {
      level: '新手路径',
      recommendations: [
        { title: '泰国 Shopee 开店', description: '门槛低，竞争小，适合新手', link: '/country/thailand' },
        { title: '越南 Lazada 入驻', description: '快速增长的东南亚市场', link: '/country/vietnam' }
      ],
      nextSteps: [
        '阅读新手入门指南',
        '完成Shopee账号注册',
        '学习基础选品方法',
        '完成首单上架'
      ]
    };
  } else if (score <= 10) {
    return {
      level: '进阶路径',
      recommendations: [
        { title: '东南亚多平台布局', description: 'Shopee + Lazada + TikTok Shop', link: '/region/southeast_asia' },
        { title: '拉美市场探索', description: '巴西Mercado Libre机会', link: '/country/brazil' }
      ],
      nextSteps: [
        '学习多平台运营策略',
        '建立基础供应链',
        '优化店铺评分',
        '拓展第二个平台'
      ]
    };
  } else if (score <= 15) {
    return {
      level: '专业路径',
      recommendations: [
        { title: '北美 Amazon FBA', description: '专业卖家首选平台', link: '/country/usa' },
        { title: '独立站 Shopify', description: '打造自有品牌', link: '/platform/shopify' }
      ],
      nextSteps: [
        '注册美国商标',
        '选择FBA产品线',
        '建立品牌官网',
        '投放精准广告'
      ]
    };
  } else {
    return {
      level: '专家路径',
      recommendations: [
        { title: '全球品牌布局', description: '多国家、多平台综合运营', link: '/dashboard' }
      ],
      nextSteps: [
        '组建运营团队',
        '建立海外仓',
        '本地化运营',
        '品牌建设与推广'
      ]
    };
  }
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- capability-assessment.test.ts
```
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/config/assessments/capability.ts frontend/__tests__/capability-assessment.test.ts
git commit -m "feat: add capability assessment questions and scoring"
```

---

### Task 3.3: Create Capability Card Component

**Files:**
- Create: `frontend/components/function-cards/capability-card.tsx`

**Step 1: Write test for capability card**

```typescript
// frontend/__tests__/capability-card.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CapabilityCard } from '@/components/function-cards/capability-card';

// Mock the API
jest.mock('@/lib/api', () => ({
  assessmentsApi: {
    submitCapability: jest.fn().mockResolvedValue({
      score: 8,
      level: '进阶路径',
      recommendations: [],
      nextSteps: []
    })
  }
}));

describe('CapabilityCard', () => {
  it('shows assessment form initially', () => {
    render(<CapabilityCard />);
    expect(screen.getByText('个人能力照妖镜')).toBeInTheDocument();
    expect(screen.getByText('开始评估')).toBeInTheDocument();
  });

  it('submits assessment and shows results', async () => {
    render(<CapabilityCard />);

    fireEvent.click(screen.getByText('开始评估'));
    // Answer questions and submit...

    await waitFor(() => {
      expect(screen.getByText('进阶路径')).toBeInTheDocument();
    });
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- capability-card.test.tsx
```
Expected: FAIL - component doesn't exist

**Step 3: Create CapabilityCard component**

```typescript
// frontend/components/function-cards/capability-card.tsx
'use client';

import { useState } from 'react';
import { AssessmentForm } from '@/components/assessments/assessment-form';
import { AssessmentResults } from '@/components/assessments/assessment-results';
import { getCapabilityQuestions, calculateCapabilityScore, getCapabilityRecommendations } from '@/config/assessments/capability';
import { assessmentsApi } from '@/lib/api';

export function CapabilityCard() {
  const [isStarted, setIsStarted] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (answers: Record<string, string>) => {
    // Calculate base score
    const score = calculateCapabilityScore(answers);

    // Get AI recommendations (will integrate Zhipu AI in Phase 4)
    const recommendations = getCapabilityRecommendations(score);

    setResult({ score, ...recommendations });
  };

  if (result) {
    return (
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">个人能力照妖镜</h3>
          <button
            onClick={() => { setResult(null); setIsStarted(false); }}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            重新评估
          </button>
        </div>
        <AssessmentResults type="capability" result={result} />
      </div>
    );
  }

  if (isStarted) {
    return (
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">个人能力照妖镜</h3>
          <button
            onClick={() => setIsStarted(false)}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            返回
          </button>
        </div>
        <AssessmentForm
          type="capability"
          questions={getCapabilityQuestions()}
          onSubmit={handleSubmit}
        />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer group">
      <div className="text-center">
        <div className="text-4xl mb-3">🔮</div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">个人能力照妖镜</h3>
        <p className="text-sm text-gray-600 mb-4">
          评估您的创业准备度，推荐最合适的起步路径
        </p>
        <button
          onClick={() => setIsStarted(true)}
          className="px-6 py-2 bg-gradient-hero text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
        >
          开始评估
        </button>
      </div>
    </div>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- capability-card.test.tsx
```
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/components/function-cards/capability-card.tsx frontend/__tests__/capability-card.test.tsx
git commit -m "feat: add capability assessment card component"
```

---

### Task 3.4-3.6: Resource Inventory, Interest Recommendations, Growth Timeline

*Due to length constraints, these follow the same pattern as Task 3.1-3.3. Create similar test files, configs, and components for:*

- **Resource Inventory** (`frontend/config/assessments/resource.ts`, `resource-card.tsx`)
- **Interest Recommendations** (`frontend/config/interests.ts`, `interest-card.tsx`)
- **Growth Timeline** (`frontend/components/function-cards/growth-timeline.tsx` with progress tracking)

---

### Task 3.7: Update FunctionCards Container

**Files:**
- Modify: `frontend/components/home/function-cards.tsx`

**Step 1: Write test for function cards layout**

```typescript
// frontend/__tests__/function-cards.test.tsx
import { render, screen } from '@testing-library/react';
import { FunctionCards } from '@/components/home/function-cards';

describe('FunctionCards', () => {
  it('renders all 4 function cards', () => {
    render(<FunctionCards />);

    expect(screen.getByText('个人能力照妖镜')).toBeInTheDocument();
    expect(screen.getByText('资源盘点')).toBeInTheDocument();
    expect(screen.getByText('兴趣推荐')).toBeInTheDocument();
    expect(screen.getByText('业主养成记')).toBeInTheDocument();
  });

  it('lays out cards in 2x2 grid', () => {
    const { container } = render(<FunctionCards />);
    const grid = container.querySelector('.grid-cols-2');
    expect(grid).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- function-cards.test.tsx
```
Expected: FAIL - needs updating

**Step 3: Update FunctionCards component**

```typescript
// frontend/components/home/function-cards.tsx
import { CapabilityCard } from './function-cards/capability-card';
import { ResourceCard } from './function-cards/resource-card';
import { InterestCard } from './function-cards/interest-card';
import { GrowthTimeline } from './function-cards/growth-timeline';

export function FunctionCards() {
  return (
    <section className="max-w-7xl mx-auto px-4">
      <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
        发现您的跨境电商之路
      </h2>
      <div className="grid md:grid-cols-2 gap-6">
        <CapabilityCard />
        <ResourceCard />
        <InterestCard />
        <GrowthTimeline />
      </div>
    </section>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- function-cards.test.tsx
```
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/components/home/function-cards.tsx frontend/__tests__/function-cards.test.tsx
git commit -m "feat: update function cards container with real features"
```

---

## Phase 4: Theme Portals (Horizontal Layout)

### Task 4.1: Redesign Theme Portals for Horizontal Layout

**Files:**
- Modify: `frontend/components/home/theme-portals.tsx`

**Step 1: Write test for horizontal tab layout**

```typescript
// frontend/__tests__/theme-portals.test.tsx
import { render, screen } from '@testing-library/react';
import { ThemePortals } from '@/components/home/theme-portals';
import { Article } from '@/lib/api';

const mockArticles: Article[] = [
  { id: '1', title: 'Test', content_theme: 'policy', region: 'southeast_asia' } as Article
];

describe('ThemePortals', () => {
  it('renders 6 tabs in horizontal row', () => {
    render(<ThemePortals articles={mockArticles} />);

    const tabs = screen.getAllByRole('tab');
    expect(tabs).toHaveLength(6);
  });

  it('displays tabs in correct order', () => {
    render(<ThemePortals articles={mockArticles} />);

    const tabLabels = screen.getAllByRole('tab').map(el => el.textContent);
    expect(tabLabels).toEqual([
      '政策法规', '机会发现', '风险预警',
      '实操指南', '平台指南', '物流参考'
    ]);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- theme-portals.test.tsx
```
Expected: FAIL - current layout is 2x3 grid

**Step 3: Rewrite ThemePortals component**

```typescript
// frontend/components/home/theme-portals.tsx
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Article } from '@/lib/api';

interface ThemePortalsProps {
  articles: Article[];
}

const THEMES = [
  { key: 'policy', name: '政策法规', emoji: '📜', color: 'yellow' },
  { key: 'opportunity', name: '机会发现', emoji: '💡', color: 'green' },
  { key: 'risk', name: '风险预警', emoji: '⚠️', color: 'red' },
  { key: 'guide', name: '实操指南', emoji: '📊', color: 'blue' },
  { key: 'platform', name: '平台指南', emoji: '🛒', color: 'purple' },
  { key: 'logistics', name: '物流参考', emoji: '🚚', color: 'orange' }
];

export function ThemePortals({ articles }: ThemePortalsProps) {
  const [activeTab, setActiveTab] = useState('policy');

  const activeTheme = THEMES.find(t => t.key === activeTab);
  const tabArticles = articles
    .filter(a => a.content_theme === activeTab)
    .slice(0, 6);

  return (
    <section className="max-w-7xl mx-auto px-4 py-10">
      <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
        按主题探索资讯
      </h2>

      {/* Horizontal Tabs - 1 row x 6 columns */}
      <div className="flex overflow-x-auto gap-2 mb-6 pb-2 scrollbar-hide">
        {THEMES.map(theme => (
          <button
            key={theme.key}
            onClick={() => setActiveTab(theme.key)}
            role="tab"
            aria-selected={activeTab === theme.key}
            className={`
              flex-shrink-0 px-4 py-2 rounded-lg font-medium transition-all whitespace-nowrap
              ${activeTab === theme.key
                ? 'bg-accent-green text-white shadow-md'
                : 'bg-white text-gray-600 hover:bg-gray-50'
              }
            `}
          >
            <span className="mr-1">{theme.emoji}</span>
            {theme.name}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tabArticles.length > 0 ? (
          tabArticles.map(article => (
            <Link
              key={article.id}
              href={`/articles/${article.id}`}
              className="bg-white rounded-lg p-4 border border-gray-200 hover:shadow-md hover:border-accent-green transition-all"
            >
              <h3 className="font-medium text-gray-900 line-clamp-2 mb-2">
                {article.title}
              </h3>
              <p className="text-sm text-gray-500 line-clamp-2">
                {article.summary}
              </p>
              <div className="flex items-center gap-2 mt-3 text-xs text-gray-400">
                <span>{article.region}</span>
                <span>•</span>
                <span>{new Date(article.published_at || '').toLocaleDateString()}</span>
              </div>
            </Link>
          ))
        ) : (
          <div className="col-span-full text-center py-10 text-gray-500">
            <p>📝 该分类整理中...</p>
          </div>
        )}
      </div>
    </section>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- theme-portals.test.tsx
```
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/components/home/theme-portals.tsx frontend/__tests__/theme-portals.test.tsx
git commit -m "feat: redesign theme portals with horizontal tab layout"
```

---

## Phase 5: Country Portal with Horizontal Tabs

### Task 5.1: Create Country Portal Page Structure

**Files:**
- Create: `frontend/app/country/[slug]/page.tsx`

**Step 1: Write test for country portal page**

```typescript
// frontend/__tests__/country-portal.test.tsx
import { render, screen } from '@testing-library/react';
import CountryPortal from '@/app/country/[slug]/page';

// Mock data
jest.mock('@/config/countries', () => ({
  getCountryBySlug: () => ({
    name: 'Thailand',
    localName: 'ประเทศไทย',
    flag: '🇹🇭',
    region: 'southeast_asia',
    population: '71,000,000',
    gdp: '$549,000,000,000',
    ecommerce: '$19,000,000,000',
    growth: '+18%'
  })
}));

describe('CountryPortal', () => {
  it('renders country header with stats', () => {
    render(<CountryPortal params={{ slug: 'thailand' }} />);

    expect(screen.getByText('🇹🇭')).toBeInTheDocument();
    expect(screen.getByText('Thailand')).toBeInTheDocument();
    expect(screen.getByText('71,000,000')).toBeInTheDocument();
  });

  it('renders 6 horizontal tabs', () => {
    render(<CountryPortal params={{ slug: 'thailand' }} />);

    const tabs = screen.getAllByRole('tab');
    expect(tabs).toHaveLength(6);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- country-portal.test.tsx
```
Expected: FAIL - page doesn't exist

**Step 3: Create country portal page**

```typescript
// frontend/app/country/[slug]/page.tsx
import { notFound } from 'next/navigation';
import { getCountryBySlug } from '@/config/countries';
import { articlesApi } from '@/lib/api';
import { CountryHeader } from '@/components/country/country-header';
import { CountryTabs } from '@/components/country/country-tabs';

interface PageProps {
  params: { slug: string };
}

export default async function CountryPortal({ params }: PageProps) {
  const country = getCountryBySlug(params.slug);

  if (!country) {
    notFound();
  }

  // Fetch articles for this country
  const articles = await articlesApi.getArticles({
    country: country.code,
    per_page: 100
  });

  return (
    <div className="min-h-screen bg-bg-warm">
      {/* Country Header with Stats */}
      <CountryHeader country={country} />

      {/* Horizontal Tabs (1x6) */}
      <CountryTabs articles={articles.articles} />
    </div>
  );
}

export async function generateStaticParams() {
  // Pre-render all country pages
  const { getAllCountries } = await import('@/config/countries');
  const countries = getAllCountries();

  return countries.map(country => ({
    slug: country.slug
  }));
}
```

**Step 4: Create CountryHeader component**

```typescript
// frontend/components/country/country-header.tsx
import { Country } from '@/config/countries';

interface CountryHeaderProps {
  country: Country;
}

export function CountryHeader({ country }: CountryHeaderProps) {
  return (
    <section className="bg-gradient-hero text-white py-12">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center gap-4 mb-6">
          <span className="text-6xl">{country.flag}</span>
          <div>
            <h1 className="text-4xl font-bold">{country.name}</h1>
            <p className="text-xl opacity-90">{country.localName}</p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white/10 backdrop-blur rounded-lg p-4">
            <div className="text-2xl font-bold">{country.population}</div>
            <div className="text-sm opacity-80">人口</div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-lg p-4">
            <div className="text-2xl font-bold">{country.gdp}</div>
            <div className="text-sm opacity-80">GDP</div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-lg p-4">
            <div className="text-2xl font-bold">{country.ecommerce}</div>
            <div className="text-sm opacity-80">电商规模</div>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-lg p-4">
            <div className="text-2xl font-bold text-accent-green">{country.growth}</div>
            <div className="text-sm opacity-80">年增长</div>
          </div>
        </div>
      </div>
    </section>
  );
}
```

**Step 5: Create CountryTabs component**

```typescript
// frontend/components/country/country-tabs.tsx
'use client';

import { useState } from 'react';
import { Article } from '@/lib/api';

interface CountryTabsProps {
  articles: Article[];
}

const TABS = [
  { key: 'overview', name: '综合概况', emoji: '📊' },
  { key: 'policy', name: '政策法规', emoji: '📜' },
  { key: 'opportunity', name: '机会发现', emoji: '💡' },
  { key: 'risk', name: '风险预警', emoji: '⚠️' },
  { key: 'industry', name: '产业分析', emoji: '🏭' },
  { key: 'platform', name: '平台指南', emoji: '🛒' }
];

export function CountryTabs({ articles }: CountryTabsProps) {
  const [activeTab, setActiveTab] = useState('overview');

  const tabArticles = articles.filter(a => {
    if (activeTab === 'overview') return true;
    if (activeTab === 'industry') return a.tags?.includes('产业');
    return a.content_theme === activeTab;
  });

  return (
    <section className="max-w-7xl mx-auto px-4 py-8">
      {/* Horizontal Tabs - 1 row x 6 columns */}
      <div className="flex overflow-x-auto gap-2 mb-8 pb-2">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            role="tab"
            aria-selected={activeTab === tab.key}
            className={`
              flex-shrink-0 px-5 py-3 rounded-lg font-medium transition-all whitespace-nowrap
              ${activeTab === tab.key
                ? 'bg-accent-green text-white shadow-md'
                : 'bg-white text-gray-600 hover:bg-gray-50'
              }
            `}
          >
            <span className="mr-2 text-lg">{tab.emoji}</span>
            {tab.name}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg p-6 shadow-sm">
        {activeTab === 'overview' ? (
          <OverviewContent />
        ) : (
          <ArticleList articles={tabArticles} />
        )}
      </div>
    </section>
  );
}

function OverviewContent() {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-gray-900">市场概览</h3>
      <p className="text-gray-600">
        详细的市场分析内容将在这里显示...
      </p>
    </div>
  );
}

function ArticleList({ articles }: { articles: Article[] }) {
  if (articles.length === 0) {
    return (
      <div className="text-center py-10 text-gray-500">
        <p>📝 该分类内容整理中...</p>
      </div>
    );
  }

  return (
    <div className="grid md:grid-cols-2 gap-4">
      {articles.map(article => (
        <a
          key={article.id}
          href={`/articles/${article.id}`}
          className="block p-4 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <h4 className="font-medium text-gray-900 line-clamp-2">{article.title}</h4>
          <p className="text-sm text-gray-600 mt-2 line-clamp-2">{article.summary}</p>
        </a>
      ))}
    </div>
  );
}
```

**Step 6: Run test to verify it passes**

```bash
cd frontend && npm test -- country-portal.test.tsx
```
Expected: PASS

**Step 7: Commit**

```bash
git add frontend/app/country/ frontend/components/country/ frontend/__tests__/country-portal.test.tsx
git commit -m "feat: add country portal with horizontal tabs (1x6 layout)"
```

---

## Phase 6: AI Integration

### Task 6.1: Set Up Zhipu AI API Client

**Files:**
- Create: `backend/services/zhipu_ai.py`
- Modify: `backend/config/settings.py`

**Step 1: Write test for Zhipu AI client**

```python
# backend/tests/test_zhipu_ai.py
import pytest
from services.zhipu_ai import ZhipuAIService

def test_zhipu_ai_client_init():
    service = ZhipuAIService()
    assert service.api_key is not None
    assert service.base_url == "https://open.bigmodel.cn/api/paas/v4"

@pytest.mark.asyncio
async def test_assessment_analysis():
    service = ZhipuAIService()
    result = await service.analyze_assessment(
        assessment_type="capability",
        answers={"q1": "a", "q2": "b", "q3": "a", "q4": "a"}
    )
    assert "score" in result
    assert "recommendations" in result
    assert "insights" in result
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/test_zhipu_ai.py -v
```
Expected: FAIL - service doesn't exist

**Step 3: Create Zhipu AI service**

```python
# backend/services/zhipu_ai.py
import httpx
from config.settings import settings

class ZhipuAIService:
    """Zhipu AI service for assessment analysis"""

    def __init__(self):
        self.api_key = settings.ZHIPU_AI_API_KEY
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.model = "glm-4-flash"

    async def analyze_assessment(
        self,
        assessment_type: str,
        answers: dict
    ) -> dict:
        """Analyze assessment answers and provide recommendations"""

        prompt = self._build_prompt(assessment_type, answers)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

            # Parse AI response
            content = data["choices"][0]["message"]["content"]
            return self._parse_response(content, assessment_type, answers)

    def _build_prompt(self, assessment_type: str, answers: dict) -> str:
        """Build prompt for AI based on assessment type"""

        if assessment_type == "capability":
            return f"""作为跨境电商专家，请分析以下用户评估结果并提供建议：

评估答案：
{answers}

请提供：
1. 评分（0-20分）
2. 用户级别（新手/进阶/专业/专家）
3. 3个具体推荐（国家/平台/产品）
4. 5个下一步行动建议

请以JSON格式返回：
{{
  "score": 10,
  "level": "进阶路径",
  "recommendations": [
    {{"title": "推荐", "description": "描述", "link": "路径"}}
  ],
  "next_steps": ["步骤1", "步骤2", ...]
}}"""

        # Similar prompts for other assessment types...
        return f"Analyze assessment: {assessment_type}, answers: {answers}"

    def _parse_response(self, content: str, assessment_type: str, answers: dict) -> dict:
        """Parse AI response and merge with rule-based scoring"""
        import json
        import re

        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback to rule-based scoring
        from config.assessments.capability import calculateCapabilityScore, getCapabilityRecommendations
        score = calculateCapabilityScore(answers)
        return {"score": score, **getCapabilityRecommendations(score)}
```

**Step 4: Add ZHIPU_AI_API_KEY to settings**

```python
# backend/config/settings.py
class Settings(BaseSettings):
    # ... existing settings ...

    # Zhipu AI
    ZHIPU_AI_API_KEY: str = Field(default="", env="ZHIPU_AI_API_KEY")

    class Config:
        env_file = ".env"
```

**Step 5: Run test to verify it passes**

```bash
cd backend && pytest tests/test_zhipu_ai.py -v
```
Expected: PASS (or skip if no API key configured)

**Step 6: Commit**

```bash
git add backend/services/zhipu_ai.py backend/config/settings.py backend/tests/test_zhipu_ai.py
git commit -m "feat: add Zhipu AI service for assessment analysis"
```

---

### Task 6.2: Create Assessment API Endpoints

**Files:**
- Create: `backend/api/assessments.py`

**Step 1: Write test for assessment API**

```python
# backend/tests/test_assessments_api.py
import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_submit_capability_assessment():
    response = client.post(
        "/api/v1/assessments/capability",
        json={
            "answers": {
                "q1": "a",
                "q2": "b",
                "q3": "a",
                "q4": "a"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "recommendations" in data
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/test_assessments_api.py -v
```
Expected: FAIL - endpoint doesn't exist

**Step 3: Create assessments router**

```python
# backend/api/assessments.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.zhipu_ai import ZhipuAIService

router = APIRouter(prefix="/api/v1/assessments", tags=["assessments"])
ai_service = ZhipuAIService()

class AssessmentRequest(BaseModel):
    answers: dict

class AssessmentResponse(BaseModel):
    score: int
    level: str
    recommendations: list
    next_steps: list
    insights: str | None = None

@router.post("/capability", response_model=AssessmentResponse)
async def submit_capability_assessment(request: AssessmentRequest):
    """Submit capability assessment and get AI-powered recommendations"""

    try:
        result = await ai_service.analyze_assessment(
            assessment_type="capability",
            answers=request.answers
        )
        return AssessmentResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resource", response_model=AssessmentResponse)
async def submit_resource_assessment(request: AssessmentRequest):
    """Submit resource assessment and get AI-powered recommendations"""

    result = await ai_service.analyze_assessment(
        assessment_type="resource",
        answers=request.answers
    )
    return AssessmentResponse(**result)

@router.post("/interest", response_model=AssessmentResponse)
async def submit_interest_assessment(request: AssessmentRequest):
    """Submit interest assessment and get AI-powered recommendations"""

    result = await ai_service.analyze_assessment(
        assessment_type="interest",
        answers=request.answers
    )
    return AssessmentResponse(**result)
```

**Step 4: Register router in main app**

```python
# backend/api/__init__.py
# ... existing imports ...
from api.assessments import router as assessments_router

# ... in app creation ...
app.include_router(assessments_router)
```

**Step 5: Run test to verify it passes**

```bash
cd backend && pytest tests/test_assessments_api.py -v
```
Expected: PASS

**Step 6: Commit**

```bash
git add backend/api/assessments.py backend/api/__init__.py backend/tests/test_assessments_api.py
git commit -m "feat: add assessment API endpoints with AI integration"
```

---

### Task 6.3: Update Frontend API Client

**Files:**
- Modify: `frontend/lib/api.ts`

**Step 1: Add assessment API methods**

```typescript
// frontend/lib/api.ts - add at end of file

// ============ Assessments API ============
export interface AssessmentRequest {
  answers: Record<string, string>;
}

export interface AssessmentResponse {
  score: number;
  level: string;
  recommendations: Array<{
    title: string;
    description: string;
    link: string;
  }>;
  next_steps: string[];
  insights?: string;
}

export const assessmentsApi = {
  async submitCapability(answers: Record<string, string>): Promise<AssessmentResponse> {
    return apiClient.post('/api/v1/assessments/capability', { answers }, true);
  },

  async submitResource(answers: Record<string, string>): Promise<AssessmentResponse> {
    return apiClient.post('/api/v1/assessments/resource', { answers }, true);
  },

  async submitInterest(answers: Record<string, string>): Promise<AssessmentResponse> {
    return apiClient.post('/api/v1/assessments/interest', { answers }, true);
  }
};
```

**Step 2: Update CapabilityCard to use real API**

```typescript
// frontend/components/function-cards/capability-card.tsx - update handleSubmit
import { assessmentsApi } from '@/lib/api';

const handleSubmit = async (answers: Record<string, string>) => {
  try {
    const result = await assessmentsApi.submitCapability(answers);
    setResult(result);
  } catch (error) {
    console.error('Assessment failed:', error);
    alert('评估失败，请稍后重试');
  }
};
```

**Step 3: Commit**

```bash
git add frontend/lib/api.ts frontend/components/function-cards/capability-card.tsx
git commit -m "feat: connect frontend to assessment API"
```

---

## Phase 7: Hero Search Functionality

### Task 7.1: Create Hero Search Component

**Files:**
- Create: `frontend/components/home/hero-search.tsx`

**Step 1: Write test for hero search**

```typescript
// frontend/__tests__/hero-search.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { HeroSearch } from '@/components/home/hero-search';

describe('HeroSearch', () => {
  it('renders search input', () => {
    render(<HeroSearch />);
    expect(screen.getByPlaceholderText('搜索国家、平台、产品...')).toBeInTheDocument();
  });

  it('navigates to search results on submit', async () => {
    render(<HeroSearch />);

    const input = screen.getByRole('searchbox');
    fireEvent.change(input, { target: { value: '泰国' } });
    fireEvent.click(screen.getByRole('button', { name: /搜索/i }));

    await waitFor(() => {
      expect(window.location.pathname).toBe('/search?q=泰国');
    });
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- hero-search.test.tsx
```
Expected: FAIL - component doesn't exist

**Step 3: Create HeroSearch component**

```typescript
// frontend/components/home/hero-search.tsx
'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';

const QUICK_FILTERS = [
  { label: '最新', value: 'latest' },
  { label: '热门', value: 'trending' },
  { label: '机会', value: 'opportunity' },
  { label: '风险', value: 'risk' }
];

export function HeroSearch() {
  const router = useRouter();
  const [query, setQuery] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  const handleFilterClick = (filter: string) => {
    router.push(`/search?filter=${filter}`);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-16 text-center">
      <h1 className="text-5xl font-bold text-white mb-4">
        发现全球电商新机遇
      </h1>
      <p className="text-xl text-white/90 mb-8">
        AI驱动的市场洞察，助您轻松开启跨境之旅
      </p>

      {/* Search Bar */}
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex gap-2">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索国家、平台、产品..."
            className="flex-1 px-6 py-4 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-accent-green"
          />
          <button
            type="submit"
            className="px-8 py-4 bg-accent-green text-gray-900 font-semibold rounded-lg hover:opacity-90 transition-opacity"
          >
            🔍 搜索
          </button>
        </div>
      </form>

      {/* Quick Filters */}
      <div className="flex flex-wrap gap-2 justify-center">
        {QUICK_FILTERS.map(filter => (
          <button
            key={filter.value}
            onClick={() => handleFilterClick(filter.value)}
            className="px-4 py-2 bg-white/20 backdrop-blur text-white rounded-lg hover:bg-white/30 transition-colors"
          >
            {filter.label}
          </button>
        ))}
      </div>
    </div>
  );
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- hero-search.test.tsx
```
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/components/home/hero-search.tsx frontend/__tests__/hero-search.test.tsx
git commit -m "feat: add hero search component with quick filters"
```

---

### Task 7.2: Create Search Results Page

**Files:**
- Create: `frontend/app/search/page.tsx`

**Step 1: Write test for search page**

```typescript
// frontend/__tests__/search-page.test.tsx
import { render, screen } from '@testing-library/react';
import SearchPage from '@/app/search/page';

// Mock articlesApi
jest.mock('@/lib/api', () => ({
  articlesApi: {
    search: jest.fn().mockResolvedValue({
      articles: [{ id: '1', title: 'Test' }],
      total: 1
    })
  }
}));

describe('SearchPage', () => {
  it('renders search results', async () => {
    // Mock searchParams
    const searchParams = { q: '泰国' };
    render(await SearchPage({ searchParams }));

    expect(screen.getByText('搜索结果: 泰国')).toBeInTheDocument();
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- search-page.test.tsx
```
Expected: FAIL - page doesn't exist

**Step 3: Create search page**

```typescript
// frontend/app/search/page.tsx
import { articlesApi } from '@/lib/api';
import { SearchResults } from '@/components/search/search-results';

interface PageProps {
  searchParams: { q?: string; filter?: string };
}

export default async function SearchPage({ searchParams }: PageProps) {
  const query = searchParams.q || '';
  const filter = searchParams.filter;

  const articles = await articlesApi.getArticles({
    per_page: 100
  });

  // Filter articles based on query
  const filtered = articles.articles.filter(article => {
    if (!query) return true;
    const searchLower = query.toLowerCase();
    return (
      article.title?.toLowerCase().includes(searchLower) ||
      article.summary?.toLowerCase().includes(searchLower) ||
      article.tags?.some(tag => tag.toLowerCase().includes(searchLower))
    );
  });

  return (
    <div className="min-h-screen bg-bg-warm py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          搜索结果: {query || filter || '全部'}
          <span className="text-gray-500 font-normal ml-2">
            ({filtered.length} 篇)
          </span>
        </h1>
        <SearchResults articles={filtered} />
      </div>
    </div>
  );
}
```

**Step 4: Create SearchResults component**

```typescript
// frontend/components/search/search-results.tsx
import Link from 'next/link';
import { Article } from '@/lib/api';

interface SearchResultsProps {
  articles: Article[];
}

export function SearchResults({ articles }: SearchResultsProps) {
  if (articles.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-6xl mb-4">🔍</div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          没有找到相关内容
        </h2>
        <p className="text-gray-600">
          试试其他关键词或浏览我们的推荐内容
        </p>
      </div>
    );
  }

  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      {articles.map(article => (
        <Link
          key={article.id}
          href={`/articles/${article.id}`}
          className="bg-white rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow"
        >
          <h3 className="font-semibold text-gray-900 line-clamp-2 mb-2">
            {article.title}
          </h3>
          <p className="text-sm text-gray-600 line-clamp-3 mb-3">
            {article.summary}
          </p>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span>{article.region}</span>
            <span>•</span>
            <span>{article.source}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}
```

**Step 5: Run test to verify it passes**

```bash
cd frontend && npm test -- search-page.test.tsx
```
Expected: PASS

**Step 6: Commit**

```bash
git add frontend/app/search/ frontend/components/search/ frontend/__tests__/search-page.test.tsx
git commit -m "feat: add search results page"
```

---

## Phase 8: Progress Tracking (Growth Timeline)

### Task 8.1: Create Progress Storage System

**Files:**
- Create: `frontend/lib/progress.ts`

**Step 1: Write test for progress storage**

```typescript
// frontend/__tests__/progress.test.ts
import { saveProgress, getProgress, updateMilestone } from '@/lib/progress';

describe('Progress storage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('saves and retrieves user progress', () => {
    saveProgress('capability', { score: 10, completed: ['q1', 'q2'] });
    const progress = getProgress('capability');

    expect(progress).toEqual({ score: 10, completed: ['q1', 'q2'] });
  });

  it('updates milestone completion', () => {
    updateMilestone('growth-path', 'milestone-1', true);
    const progress = getProgress('growth-path');

    expect(progress.milestones['milestone-1']).toBe(true);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- progress.test.ts
```
Expected: FAIL - module doesn't exist

**Step 3: Create progress storage module**

```typescript
// frontend/lib/progress.ts

interface Progress {
  [key: string]: any;
}

const STORAGE_KEY = 'zenconsult_progress';

export function saveProgress(type: string, data: any): void {
  if (typeof window === 'undefined') return;

  const existing = getProgress();
  existing[type] = { ...existing[type], ...data, updatedAt: Date.now() };

  localStorage.setItem(STORAGE_KEY, JSON.stringify(existing));
}

export function getProgress(type?: string): any {
  if (typeof window === 'undefined') return {};

  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) return {};

  const progress: Progress = JSON.parse(stored);

  return type ? progress[type] || {} : progress;
}

export function updateMilestone(
  path: string,
  milestoneId: string,
  completed: boolean
): void {
  const progress = getProgress(path);

  if (!progress.milestones) {
    progress.milestones = {};
  }

  progress.milestones[milestoneId] = completed;
  progress.lastUpdated = Date.now();

  saveProgress(path, progress);
}

export function getMilestoneProgress(path: string, milestones: string[]): number {
  const progress = getProgress(path);
  if (!progress.milestones) return 0;

  const completed = milestones.filter(m => progress.milestones[m]).length;
  return Math.round((completed / milestones.length) * 100);
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- progress.test.ts
```
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/lib/progress.ts frontend/__tests__/progress.test.ts
git commit -m "feat: add local storage progress tracking"
```

---

### Task 8.2: Create Interactive Growth Timeline Component

**Files:**
- Create: `frontend/components/function-cards/growth-timeline.tsx`

**Step 1: Write test for growth timeline**

```typescript
// frontend/__tests__/growth-timeline.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { GrowthTimeline } from '@/components/function-cards/growth-timeline';

describe('GrowthTimeline', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders all 5 stages', () => {
    render(<GrowthTimeline />);

    expect(screen.getByText('小白探索期')).toBeInTheDocument();
    expect(screen.getByText('新手起步期')).toBeInTheDocument();
    expect(screen.getByText('成长期')).toBeInTheDocument();
    expect(screen.getByText('熟手期')).toBeInTheDocument();
    expect(screen.getByText('专家期')).toBeInTheDocument();
  });

  it('marks milestones as complete', () => {
    render(<GrowthTimeline />);

    const milestone = screen.getByText('完成市场调研');
    fireEvent.click(milestone);

    // Check if progress was saved
    const progress = JSON.parse(localStorage.getItem('zenconsult_progress') || '{}');
    expect(progress['growth-path'].milestones['milestone-1-1']).toBe(true);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- growth-timeline.test.tsx
```
Expected: FAIL - component doesn't exist

**Step 3: Create GrowthTimeline component**

```typescript
// frontend/components/function-cards/growth-timeline.tsx
'use client';

import { useState } from 'react';
import { updateMilestone, getMilestoneProgress } from '@/lib/progress';

const GROWTH_STAGES = [
  {
    id: 'stage-1',
    name: '小白探索期',
    duration: '1-2个月',
    milestones: [
      { id: 'milestone-1-1', text: '完成市场调研', resource: '/guide/market-research' },
      { id: 'milestone-1-2', text: '选定目标国家/品类', resource: '/guide/select-niche' },
      { id: 'milestone-1-3', text: '开通账号', resource: '/guide/register' }
    ]
  },
  {
    id: 'stage-2',
    name: '新手起步期',
    duration: '2-4个月',
    milestones: [
      { id: 'milestone-2-1', text: '选品上架', resource: '/guide/product-selection' },
      { id: 'milestone-2-2', text: '完成首单', resource: '/guide/first-sale' },
      { id: 'milestone-2-3', text: '积累10个好评', resource: '/guide/reviews' }
    ]
  },
  {
    id: 'stage-3',
    name: '成长期',
    duration: '4-8个月',
    milestones: [
      { id: 'milestone-3-1', text: '月销50+单', resource: '/guide/scale-50' },
      { id: 'milestone-3-2', text: '店铺评分4.5+', resource: '/guide/rating' },
      { id: 'milestone-3-3', text: '建立供应链', resource: '/guide/supply-chain' }
    ]
  },
  {
    id: 'stage-4',
    name: '熟手期',
    duration: '8-12个月',
    milestones: [
      { id: 'milestone-4-1', text: '月销200+单', resource: '/guide/scale-200' },
      { id: 'milestone-4-2', text: '拓展第2个平台', resource: '/guide/multi-platform' },
      { id: 'milestone-4-3', text: '组建小团队', resource: '/guide/team-building' }
    ]
  },
  {
    id: 'stage-5',
    name: '专家期',
    duration: '12个月+',
    milestones: [
      { id: 'milestone-5-1', text: '自有品牌', resource: '/guide/branding' },
      { id: 'milestone-5-2', text: '本土化运营', resource: '/guide/localization' },
      { id: 'milestone-5-3', text: '年销百万+', resource: '/guide/million-scale' }
    ]
  }
];

export function GrowthTimeline() {
  const [expandedStage, setExpandedStage] = useState('stage-1');

  // Calculate overall progress
  const allMilestones = GROWTH_STAGES.flatMap(s => s.milestones.map(m => m.id));
  const overallProgress = getMilestoneProgress('growth-path', allMilestones);

  return (
    <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">🌱 业主养成记</h3>
        <div className="text-sm text-gray-500">进度: {overallProgress}%</div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
        <div
          className="bg-gradient-hero h-2 rounded-full transition-all"
          style={{ width: `${overallProgress}%` }}
        />
      </div>

      {/* Stages */}
      <div className="space-y-2">
        {GROWTH_STAGES.map((stage, index) => (
          <div key={stage.id} className="border border-gray-200 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandedStage(expandedStage === stage.id ? '' : stage.id)}
              className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-accent-green/20 flex items-center justify-center text-sm font-bold text-accent-green">
                  {index + 1}
                </div>
                <div className="text-left">
                  <div className="font-medium text-gray-900">{stage.name}</div>
                  <div className="text-xs text-gray-500">{stage.duration}</div>
                </div>
              </div>
              <div className="text-gray-400">
                {expandedStage === stage.id ? '▼' : '▶'}
              </div>
            </button>

            {expandedStage === stage.id && (
              <div className="px-4 pb-4 border-t border-gray-100">
                {/* Stage Goal */}
                <div className="py-3 text-sm text-gray-600">
                  <strong>目标:</strong> {getStageGoal(stage.id)}
                </div>

                {/* Milestones */}
                <div className="space-y-2">
                  {stage.milestones.map(milestone => {
                    const isCompleted = getMilestoneProgress('growth-path', [milestone.id]) > 0;

                    return (
                      <label
                        key={milestone.id}
                        className="flex items-start gap-3 p-2 rounded hover:bg-gray-50 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={isCompleted}
                          onChange={(e) => {
                            updateMilestone('growth-path', milestone.id, e.target.checked);
                            // Force re-render
                            window.dispatchEvent(new Event('storage'));
                          }}
                          className="mt-1 w-4 h-4 text-accent-green rounded"
                        />
                        <div className="flex-1">
                          <div className={`text-sm ${isCompleted ? 'line-through text-gray-400' : 'text-gray-900'}`}>
                            {milestone.text}
                          </div>
                          <a
                            href={milestone.resource}
                            className="text-xs text-accent-green hover:underline"
                          >
                            查看指南 →
                          </a>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Current Status */}
      <div className="mt-4 pt-4 border-t border-gray-200 text-sm text-gray-600">
        <strong>当前进度:</strong> {getCurrentStage(overallProgress)}
      </div>
    </div>
  );
}

function getStageGoal(stageId: string): string {
  const goals: Record<string, string> = {
    'stage-1': '了解行业，选择方向',
    'stage-2': '完成首单，跑通流程',
    'stage-3': '稳定出单，优化运营',
    'stage-4': '规模化，多品类/多平台',
    'stage-5': '品牌化，本土化'
  };
  return goals[stageId] || '';
}

function getCurrentStage(progress: number): string {
  if (progress < 20) return '小白探索期';
  if (progress < 40) return '新手起步期';
  if (progress < 60) return '成长期';
  if (progress < 80) return '熟手期';
  return '专家期';
}
```

**Step 4: Run test to verify it passes**

```bash
cd frontend && npm test -- growth-timeline.test.tsx
```
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/components/function-cards/growth-timeline.tsx frontend/__tests__/growth-timeline.test.tsx
git commit -m "feat: add interactive growth timeline with progress tracking"
```

---

## Phase 9: Final Integration & Testing

### Task 9.1: End-to-End Testing

**Step 1: Create E2E test for complete user flow**

```typescript
// frontend/e2e/user-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Complete user journey', () => {
  test('new user discovers and assesses', async ({ page }) => {
    // 1. Visit homepage
    await page.goto('http://localhost:3000');
    await expect(page.locator('h1')).toContainText('发现全球电商新机遇');

    // 2. Browse region cards
    await expect(page.locator('text=东南亚')).toBeVisible();
    await page.click('text=泰国');
    await expect(page).toHaveURL(/\/country\/thailand/);

    // 3. Go back and take assessment
    await page.goBack();
    await page.click('text=个人能力照妖镜');
    await page.click('text=开始评估');

    // 4. Complete assessment
    await page.click('text=完全新手');
    await page.click('text=少于10小时');
    await page.click('text=1万以下');
    await page.click('text=仅中文');
    await page.click('text=提交评估');

    // 5. View recommendations
    await expect(page.locator('text=新手路径')).toBeVisible();
    await expect(page.locator('text=泰国 Shopee')).toBeVisible();

    // 6. Browse growth timeline
    await page.goto('http://localhost:3000');
    await page.click('text=业主养成记');
    await expect(page.locator('text=小白探索期')).toBeVisible();

    // 7. Mark milestone
    await page.click('text=完成市场调研');
    await expect(page.locator('input[type="checkbox"]')).toBeChecked();
  });

  test('search functionality', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Use hero search
    await page.fill('input[placeholder*="搜索"]', '美妆');
    await page.click('button:has-text("搜索")');

    await expect(page).toHaveURL(/\/search\?q=美妆/);
    await expect(page.locator('text=搜索结果')).toBeVisible();
  });

  test('theme portals navigation', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Click theme tab
    await page.click('role=tab[name="机会发现"]');

    // Should filter articles
    await expect(page.locator('role=tab[aria-selected="true"]')).toHaveText('机会发现');
  });
});
```

**Step 2: Run E2E tests**

```bash
cd frontend && npx playwright test
```

**Step 3: Fix any failures and commit**

```bash
git add frontend/e2e/
git commit -m "test: add end-to-end user journey tests"
```

---

### Task 9.2: Update Environment Configuration

**Files:**
- Modify: `frontend/.env.production`

**Step 1: Update production API URL**

```bash
# Update to use custom domain instead of Railway URL
NEXT_PUBLIC_API_URL=https://api.zenconsult.top
```

**Step 2: Commit**

```bash
git add frontend/.env.production
git commit -m "config: update production API URL to custom domain"
```

---

### Task 9.3: Final Deployment Verification

**Step 1: Pre-deployment checklist**

```bash
# Run all tests
cd frontend && npm test
cd backend && pytest

# Build frontend
cd frontend && npm run build

# Check for TypeScript errors
cd frontend && npx tsc --noEmit
cd backend && mypy .
```

**Step 2: Create deployment commit**

```bash
git add -A
git commit -m "chore: prepare for production deployment

- Complete visual redesign with exotic romantic theme
- 4 interactive function cards with AI assessments
- Country portals with horizontal tabs
- Progress tracking for growth timeline
- Search functionality
- E2E tests passing

Ready for Vercel + Railway deployment"
```

**Step 3: Push and verify deployments**

```bash
git push origin main
```

**Step 4: Verify live site**

```bash
# Check frontend
curl https://www.zenconsult.top

# Check backend
curl https://api.zenconsult.top/health

# Check API docs
curl https://api.zenconsult.top/docs
```

---

## Summary

**Total Tasks:** 35+
**Estimated Time:** 4-6 weeks
**Lines of Code:** ~5,000+

### Completed Features:
✅ Exotic romantic color system
✅ Reordered homepage layout
✅ Region cards with keyword clouds
✅ 4 interactive function cards (capability, resource, interest, growth)
✅ Theme portals with horizontal tabs
✅ Country portals with 6-tab layout
✅ AI-powered assessments (Zhipu AI integration)
✅ Hero search functionality
✅ Progress tracking with localStorage
✅ E2E test coverage

### Tech Stack Used:
- Next.js 15 (App Router, Server Components)
- TypeScript
- Tailwind CSS (custom color variables)
- shadcn/ui components
- FastAPI (Python backend)
- Zhipu AI (assessment analysis)
- PostgreSQL + Redis
- Playwright (E2E testing)
- Jest + React Testing Library

---

**End of Implementation Plan**

Ready for execution with superpowers:executing-plans or superpowers:subagent-driven-development.
