import { CountryConfig } from './types';

export const mexico: CountryConfig = {
  // 基本信息
  name: '墨西哥',
  nameEn: 'Mexico',
  nameLocal: 'México',
  flag: '🇲🇽',
  code: 'MX',
  region: 'latin_america',

  // 经济数据
  population: '1.29亿',
  gdp: '$1.32万亿',
  ecommerce: '$280亿',
  growth: '+23%',
  capital: '墨西哥城',
  currency: 'MXN ($)',
  language: '西班牙语',

  // 电商信息
  platforms: [
    {
      name: 'Mercado Libre',
      nameEn: 'Mercado Libre',
      share: 65,
      color: 'yellow',
      sellerCount: '60万+',
      description: '市场主导者，信任度高'
    },
    {
      name: 'Amazon',
      nameEn: 'Amazon',
      share: 25,
      color: 'orange',
      sellerCount: '12万+',
      description: '墨西哥城物流中心'
    },
    {
      name: 'Shopee',
      nameEn: 'Shopee',
      share: 8,
      color: 'orange',
      sellerCount: '新兴平台',
      description: '刚刚进入，早期机会'
    }
  ],
  mobileCommerceRate: '68%',
  paymentMethods: ['信用卡', '货到付款 (COD)', 'OXX店铺支付', 'SPEI转账'],

  // 成本参考
  costs: {
    mercadolibre: {
      openFee: '免费',
      commission: '12-16%',
      description: '墨西哥是Mercado Libre第二大市场'
    },
    amazon: {
      openFee: '$19.99/月',
      commission: '10-15%',
      description: '靠近美国，物流相对方便'
    },
    shopee: {
      openFee: '免费',
      commission: '8-12%',
      description: '新市场，竞争小'
    }
  },

  // 物流信息
  logistics: {
    domestic: '3-7天',
    international: '中国→墨西哥 10-18天',
    cost: '¥18-35/kg'
  },

  // 文化特色
  culture: {
    greeting: '¡Hola! ¿Qué tal? 🌮',
    emojis: ['🌮', '🎸', '🏵', '💀', '🎉'],
    features: ['玛雅文明', '音乐/舞蹈', '美食文化', '热情友好']
  },

  // SEO
  slug: 'mx',
  description: '墨西哥跨境电商门户 - 拉美第二大市场，Mercado Libre和Amazon平台对比，美国邻居，物流优势明显'
};
