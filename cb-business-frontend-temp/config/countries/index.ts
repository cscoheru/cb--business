// 先导入，再导出
import { thailand } from './thailand';
import { vietnam } from './vietnam';
import { malaysia } from './malaysia';
import { usa } from './usa';
import { brazil } from './brazil';
import { mexico } from './mexico';
import type { CountryConfig, PlatformInfo, CostInfo } from './types';

// 重新导出所有国家配置
export { thailand, vietnam, malaysia, usa, brazil, mexico };
export type { CountryConfig, PlatformInfo, CostInfo };

// 所有国家配置列表
export const countries = [thailand, vietnam, malaysia, usa, brazil, mexico];

// 按区域分组
export const countriesByRegion = {
  southeast_asia: [thailand, vietnam, malaysia],
  north_america: [usa],
  latin_america: [brazil, mexico],
};

// 根据slug获取国家配置
export function getCountryBySlug(slug: string) {
  return countries.find(c => c.slug === slug);
}

// 根据代码获取国家配置
export function getCountryByCode(code: string) {
  return countries.find(c => c.code === code);
}

// 获取区域内的所有国家
export function getCountriesByRegion(region: string) {
  return countriesByRegion[region as keyof typeof countriesByRegion] || [];
}
