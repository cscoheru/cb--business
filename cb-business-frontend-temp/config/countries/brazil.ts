import { CountryConfig } from './types';

export const brazil: CountryConfig = {
  // 基本信息
  name: '巴西',
  nameEn: 'Brazil',
  nameLocal: 'Brasil',
  flag: '🇧🇷',
  code: 'BR',
  region: 'latin_america',

  // 经济数据
  population: '2.15亿',
  gdp: '$2.08万亿',
  ecommerce: '$500亿',
  growth: '+20%',
  capital: '巴西利亚',
  currency: 'BRL (R$)',
  language: '葡萄牙语',

  // 电商信息
  platforms: [
    {
      name: 'Mercado Libre',
      nameEn: 'Mercado Libre',
      share: 75,
      color: 'yellow',
      sellerCount: '100万+',
      description: '拉美最大平台，几乎垄断'
    },
    {
      name: 'Shopee',
      nameEn: 'Shopee',
      share: 15,
      color: 'orange',
      sellerCount: '30万+',
      description: '快速增长，投资力度大'
    },
    {
      name: 'Amazon',
      nameEn: 'Amazon',
      share: 8,
      color: 'orange',
      sellerCount: '5万+',
      description: '高端市场，圣保罗/里约为主'
    }
  ],
  mobileCommerceRate: '70%',
  paymentMethods: ['信用卡', 'Boleto (票付款)', 'Pix', '货到付款'],

  // 成本参考
  costs: {
    mercadolibre: {
      openFee: '免费',
      commission: '12-16%',
      description: '销售佣金较高，流量大'
    },
    shopee: {
      openFee: '免费',
      commission: '8-12%',
      description: '新卖家扶持政策好'
    },
    amazon: {
      openFee: '$19.99/月',
      commission: '10-15%',
      description: 'FBA费用较高'
    }
  },

  // 物流信息
  logistics: {
    domestic: '5-10天（地域广阔）',
    international: '中国→巴西 15-25天',
    cost: '¥25-45/kg'
  },

  // 文化特色
  culture: {
    greeting: 'Oi! Tudo bem? 👋',
    emojis: ['⚽', '🎉', '🏖️', '🌴', '💃'],
    features: ['热情奔放', '足球王国', '狂欢节', '热爱社交']
  },

  // SEO
  slug: 'br',
  description: '巴西跨境电商门户 - 拉美最大市场，Mercado Libre平台攻略，了解巴西消费者购物习惯和物流解决方案'
};
