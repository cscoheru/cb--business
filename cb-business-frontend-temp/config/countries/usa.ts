import { CountryConfig } from './types';

export const usa: CountryConfig = {
  // 基本信息
  name: '美国',
  nameEn: 'United States',
  nameLocal: 'United States',
  flag: '🇺🇸',
  code: 'US',
  region: 'north_america',

  // 经济数据
  population: '3.3亿',
  gdp: '$26.85万亿',
  ecommerce: '$1.1万亿',
  growth: '+10%',
  capital: '华盛顿特区',
  currency: 'USD ($)',
  language: '英语',

  // 电商信息
  platforms: [
    {
      name: 'Amazon',
      nameEn: 'Amazon',
      share: 65,
      color: 'orange',
      sellerCount: '200万+',
      description: '全球最大电商平台，FBA成熟'
    },
    {
      name: 'Walmart',
      nameEn: 'Walmart',
      share: 15,
      color: 'blue',
      sellerCount: '15万+',
      description: '新兴平台，增长快速'
    },
    {
      name: 'eBay',
      nameEn: 'eBay',
      share: 10,
      color: 'colorful',
      sellerCount: '18万+',
      description: '拍卖起家，二手市场大'
    }
  ],
  mobileCommerceRate: '45%',
  paymentMethods: ['信用卡', 'PayPal', 'Apple Pay', 'Google Pay'],

  // 成本参考
  costs: {
    amazon: {
      openFee: '$39.99/月',
      commission: '8-15%',
      description: '专业卖家计划$39.99/月'
    },
    walmart: {
      openFee: '免费',
      commission: '6-12%',
      description: '需邀请入驻'
    },
    ebay: {
      openFee: '免费',
      commission: '10-12%',
      description: '每笔交易费+$0.30'
    }
  },

  // 物流信息
  logistics: {
    domestic: '2-5天（标准快递）',
    international: '中国→美国 7-15天',
    cost: '$2-5/lb'
  },

  // 文化特色
  culture: {
    greeting: 'Hi! What\'s up? 👋',
    emojis: ['🗽', '🦅', '🍔', '⚾', '🎬'],
    features: ['消费能力强', '高客单价', '重视品牌', '专利严格']
  },

  // SEO
  slug: 'us',
  description: '美国跨境电商门户 - 全球最大电商市场，Amazon FBA攻略，美国消费者行为分析，高客单价机会'
};
