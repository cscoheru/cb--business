import { CountryConfig } from './types';

export const malaysia: CountryConfig = {
  // 基本信息
  name: '马来西亚',
  nameEn: 'Malaysia',
  nameLocal: 'Malaysia',
  flag: '🇲🇾',
  code: 'MY',
  region: 'southeast_asia',

  // 经济数据
  population: '3,300万',
  gdp: '$4,550亿',
  ecommerce: '$110亿',
  growth: '+15%',
  capital: '吉隆坡',
  currency: 'MYR (RM)',
  language: '马来语/英语',

  // 电商信息
  platforms: [
    {
      name: 'Shopee',
      nameEn: 'Shopee',
      share: 48,
      color: 'orange',
      sellerCount: '35万+',
      description: '市场领导者，11.11和9.9大促'
    },
    {
      name: 'Lazada',
      nameEn: 'Lazada',
      share: 38,
      color: 'blue',
      sellerCount: '20万+',
      description: '竞争相对较小'
    },
    {
      name: 'TikTok Shop',
      nameEn: 'TikTok Shop',
      share: 10,
      color: 'black',
      sellerCount: '增长中',
      description: '穆斯林市场有特色'
    }
  ],
  mobileCommerceRate: '75%',
  paymentMethods: ['电子钱包', '货到付款 (COD)', '银行卡', '在线转账'],

  // 成本参考
  costs: {
    shopee: {
      openFee: '免费',
      commission: '5-8%',
      description: '市场成熟，竞争激烈'
    },
    lazada: {
      openFee: 'RM300/年',
      commission: '5-7%',
      description: '货币兑换方便'
    },
    tiktok: {
      openFee: '免费',
      commission: '5-6%',
      description: '穆斯林品类机会大'
    }
  },

  // 物流信息
  logistics: {
    domestic: '西马1-2天，东马3-5天',
    international: '中国→马来西亚 6-8天',
    cost: '¥14-22/kg'
  },

  // 文化特色
  culture: {
    greeting: 'Apa khabar! 👋',
    emojis: ['🕌', '🥘', '🌴', '🏖️', '🎆'],
    features: ['多元文化', '穆斯林市场', '双子塔', '美食天堂']
  },

  // SEO
  slug: 'my',
  description: '马来西亚跨境电商门户 - 探索多元文化市场，英语普及率高，穆斯林消费品类机会，Shopee/Lazada开店指南'
};
