import { CountryConfig } from './types';

export const thailand: CountryConfig = {
  // 基本信息
  name: '泰国',
  nameEn: 'Thailand',
  nameLocal: 'สยาม', // สยาม
  flag: '🇹🇭',
  code: 'TH',
  region: 'southeast_asia',

  // 经济数据
  population: '7,100万',
  gdp: '$5,490亿',
  ecommerce: '$190亿',
  growth: '+18%',
  capital: '曼谷',
  currency: 'THB (฿)',
  language: '泰语/英语',

  // 电商信息
  platforms: [
    {
      name: 'Shopee',
      nameEn: 'Shopee',
      share: 42,
      color: 'orange',
      sellerCount: '50万+',
      description: '东南亚最大电商平台，9.9和12.12大促影响巨大'
    },
    {
      name: 'Lazada',
      nameEn: 'Lazada',
      share: 35,
      color: 'blue',
      sellerCount: '30万+',
      description: '阿里巴巴旗下，拥有LazMall高端品牌'
    },
    {
      name: 'TikTok Shop',
      nameEn: 'TikTok Shop',
      share: 18,
      color: 'black',
      sellerCount: '增长最快',
      description: '直播带货兴起，年轻用户首选'
    }
  ],
  mobileCommerceRate: '82%',
  paymentMethods: ['货到付款 (COD)', '电子钱包', '银行转账', 'PromptPay'],

  // 成本参考
  costs: {
    shopee: {
      openFee: '免费',
      commission: '5-8%',
      description: '新卖家前3个月免佣金'
    },
    lazada: {
      openFee: '฿1,500/年',
      commission: '5-7%',
      description: '包含店铺管理费'
    },
    tiktok: {
      openFee: '免费',
      commission: '5-6%',
      description: '直播带货额外收取服务费'
    }
  },

  // 物流信息
  logistics: {
    domestic: '曼谷1-2天，外府3-5天',
    international: '中国→泰国 5-7天',
    cost: '¥15-25/kg'
  },

  // 文化特色
  culture: {
    greeting: '萨瓦迪卡！🙏',
    emojis: ['🐘', '🌺', '🍜', '💎', '🏛️', '🛕'],
    features: ['大象之国', '兰花之都', '泰餐文化', '宝石王国', '微笑之国']
  },

  // SEO
  slug: 'th',
  description: '泰国跨境电商门户 - 探索东南亚第二大经济体的电商机遇，了解Shopee、Lazada、TikTok Shop等平台开店指南、政策法规、成本参考'
};
