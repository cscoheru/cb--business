// 国家配置类型定义

export interface PlatformInfo {
  name: string;
  nameEn: string;
  share: number; // 市场份额 %
  color: string; // 用于UI显示的颜色
  url?: string; // 平台官网
  sellerCount?: string; // 卖家数量
  description?: string;
}

export interface CostInfo {
  openFee: string; // 开店费用
  commission: string; // 佣金比例
  description?: string;
}

export interface CountryConfig {
  // 基本信息
  name: string; // 中文名称
  nameEn: string; // 英文名称
  nameLocal: string; // 本地语言名称
  flag: string; // 国旗emoji
  code: string; // 国家代码（如TH, VN）
  region: string; // 所属区域（southeast_asia, north_america等）

  // 经济数据
  population: string; // 人口
  gdp: string; // GDP
  ecommerce: string; // 电商市场规模
  growth: string; // 增长率
  capital: string; // 首都
  currency: string; // 货币
  language: string; // 语言

  // 电商信息
  platforms: PlatformInfo[]; // 主流平台
  mobileCommerceRate: string; // 移动电商占比
  paymentMethods: string[]; // 主要支付方式

  // 成本参考
  costs: {
    [platform: string]: CostInfo;
  };

  // 物流信息
  logistics: {
    domestic: string; // 本地派送时效
    international: string; // 国际物流时效
    cost: string; // 物流成本
  };

  // 文化特色
  culture: {
    greeting?: string; // 问候语
    emojis?: string[]; // 代表性emoji
    features?: string[]; // 特色标签
  };

  // SEO
  slug: string; // URL友好名称
  description: string; // 描述
}
