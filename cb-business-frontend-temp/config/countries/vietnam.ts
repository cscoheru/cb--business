import { CountryConfig } from './types';

export const vietnam: CountryConfig = {
  // 基本信息
  name: '越南',
  nameEn: 'Vietnam',
  nameLocal: 'Việt Nam',
  flag: '🇻🇳',
  code: 'VN',
  region: 'southeast_asia',

  // 经济数据
  population: '9,900万',
  gdp: '$4,330亿',
  ecommerce: '$130亿',
  growth: '+25%',
  capital: '河内',
  currency: 'VND (₫)',
  language: '越南语/英语',

  // 电商信息
  platforms: [
    {
      name: 'Shopee',
      nameEn: 'Shopee',
      share: 45,
      color: 'orange',
      sellerCount: '40万+',
      description: '市场领导者，年轻用户最多'
    },
    {
      name: 'Lazada',
      nameEn: 'Lazada',
      share: 35,
      color: 'blue',
      sellerCount: '25万+',
      description: '快速增长，投资力度大'
    },
    {
      name: 'TikTok Shop',
      nameEn: 'TikTok Shop',
      share: 15,
      color: 'black',
      sellerCount: '新兴平台',
      description: '直播带货刚刚起步'
    }
  ],
  mobileCommerceRate: '78%',
  paymentMethods: ['货到付款 (COD)', '电子钱包', '银行转账'],

  // 成本参考
  costs: {
    shopee: {
      openFee: '免费',
      commission: '5-7%',
      description: '新卖家扶持政策好'
    },
    lazada: {
      openFee: '₫500,000/年',
      commission: '5-6%',
      description: '费用相对较低'
    },
    tiktok: {
      openFee: '免费',
      commission: '5-6%',
      description: '市场早期，机会多'
    }
  },

  // 物流信息
  logistics: {
    domestic: '河内/胡志明1-2天，外省3-5天',
    international: '中国→越南 5-7天',
    cost: '¥12-20/kg'
  },

  // 文化特色
  culture: {
    greeting: 'Xin chào! 👋',
    emojis: ['🛵', '🥫', '🍜', '🏝️', '🌺'],
    features: ['年轻人口', '制造业基地', '咖啡文化', '海岛旅游']
  },

  // SEO
  slug: 'vn',
  description: '越南跨境电商门户 - 探索东南亚增长最快的电商市场，年轻人口众多，成本优势明显，Shopee/Lazada开店指南'
};
