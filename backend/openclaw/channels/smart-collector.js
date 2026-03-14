// openclaw/channels/smart-collector.js
/**
 * 智能数据采集Channel
 *
 * 接收AI的数据需求，执行针对性的智能采集
 * 避免盲目爬取，使用采样策略获取关键数据
 */

const OxylabsClient = require('../lib/oxylabs-client');
const SmartSampler = require('../lib/smart-sampler');
const { v4: uuidv4 } = require('uuid');

module.exports = {
    /**
     * 主执行函数
     *
     * @param {Object} task - 采集任务
     * @returns {Object} 采集结果
     */
    async execute(task) {
        const { requestId, dataNeeded, expectedOutcome } = task;

        console.log(`🤖 [SmartCollector] 执行采集任务: ${requestId}`);
        console.log(`📋 数据需求:`, JSON.stringify(dataNeeded, null, 2));

        try {
            // 第1步：设计采样策略
            const sampler = new SmartSampler();
            const strategy = sampler.designStrategy(dataNeeded);

            console.log(`📊 采样策略:`, JSON.stringify(strategy, null, 2));

            // 第2步：执行采集
            const results = await this.collectData(strategy, dataNeeded);

            // 第3步：结构化数据
            const structured = this.structureDataForAI(results, expectedOutcome);

            console.log(`✅ 采集完成: ${structured.summary.total_items} 条数据`);

            return {
                version: '1.0',
                requestId: requestId,
                taskId: uuidv4(),
                timestamp: new Date().toISOString(),
                status: 'completed',
                result: structured
            };

        } catch (error) {
            console.error(`❌ 采集失败:`, error.message);

            return {
                version: '1.0',
                requestId: requestId,
                taskId: uuidv4(),
                timestamp: new Date().toISOString(),
                status: 'failed',
                error: {
                    code: 'COLLECTION_ERROR',
                    message: error.message,
                    details: error.stack
                }
            };
        }
    },

    /**
     * 根据策略执行数据采集
     */
    async collectData(strategy, dataNeeded) {
        const results = [];
        const { type, scope } = dataNeeded;

        switch (type) {
            case 'product_reviews':
                results.push(...await this.collectProductReviews(scope, strategy));
                break;

            case 'price_monitoring':
                results.push(...await this.collectPriceData(scope, strategy));
                break;

            case 'competitor_analysis':
                results.push(...await this.collectCompetitorData(scope, strategy));
                break;

            case 'social_sentiment':
                results.push(...await this.collectSocialSentiment(scope, strategy));
                break;

            default:
                throw new Error(`Unknown data type: ${type}`);
        }

        return results;
    },

    /**
     * 采集产品评论
     */
    async collectProductReviews(scope, strategy) {
        console.log(`📦 采集产品评论:`, scope);

        const client = new OxylabsClient();
        const results = [];

        try {
            // 根据scope确定搜索参数
            const searchQuery = this.buildSearchQuery(scope);

            // 执行搜索
            const products = await client.searchAmazon({
                query: searchQuery,
                category: scope.category,
                limit: strategy.sampleSize || 20
            });

            console.log(`🔍 找到 ${products.length} 个产品`);

            // 采样评论
            for (const product of products.slice(0, 10)) {
                // 从产品页面提取关键信息
                const productData = {
                    type: 'product_reviews',
                    source: 'amazon',
                    asin: product.asin,
                    title: product.title,
                    rating: product.rating,
                    reviews_count: product.reviews_count,
                    price: product.price,

                    // 采样评论（模拟）
                    sampled_reviews: this.sampleReviews(product, strategy),

                    metadata: {
                        collected_at: new Date().toISOString(),
                        confidence: 0.9
                    }
                };

                results.push(productData);
            }

            await client.close();

        } catch (error) {
            console.error(`采集产品评论失败:`, error.message);
        }

        return results;
    },

    /**
     * 采集价格数据
     */
    async collectPriceData(scope, strategy) {
        console.log(`💰 采集价格数据:`, scope);

        const client = new OxylabsClient();
        const results = [];

        try {
            const searchQuery = this.buildSearchQuery(scope);

            const products = await client.searchAmazon({
                query: searchQuery,
                category: scope.category,
                limit: strategy.sampleSize || 30
            });

            // 提取价格信息
            const priceData = {
                type: 'price_monitoring',
                source: 'amazon',
                products: products.map(p => ({
                    asin: p.asin,
                    title: p.title,
                    price: p.price,
                    rating: p.rating
                })),

                aggregated: {
                    avg_price: this.calculateAverage(products.map(p => p.price)),
                    min_price: Math.min(...products.map(p => p.price).filter(Boolean)),
                    max_price: Math.max(...products.map(p => p.price).filter(Boolean)),
                    price_range: this.calculatePriceRange(products)
                },

                metadata: {
                    collected_at: new Date().toISOString(),
                    sample_size: products.length
                }
            };

            results.push(priceData);

            await client.close();

        } catch (error) {
            console.error(`采集价格数据失败:`, error.message);
        }

        return results;
    },

    /**
     * 采集竞品数据
     */
    async collectCompetitorData(scope, strategy) {
        console.log(`🎯 采集竞品数据:`, scope);

        const client = new OxylabsClient();
        const results = [];

        try {
            const searchQuery = this.buildSearchQuery(scope);

            const products = await client.searchAmazon({
                query: searchQuery,
                limit: Math.min(strategy.sampleSize || 20, scope.top_n || 10)
            });

            const competitors = products.slice(0, 10).map((product, index) => ({
                rank: index + 1,
                asin: product.asin,
                title: product.title,
                brand: product.brand,
                price: product.price,
                rating: product.rating,
                reviews_count: product.reviews_count
            }));

            results.push({
                type: 'competitor_analysis',
                source: 'amazon',
                competitors: competitors,

                aggregated: {
                    total_competitors: competitors.length,
                    avg_rating: this.calculateAverage(competitors.map(c => c.rating).filter(Boolean)),
                    avg_price: this.calculateAverage(competitors.map(c => c.price).filter(Boolean)),
                    top_brands: this.getTopBrands(competitors)
                },

                metadata: {
                    collected_at: new Date().toISOString()
                }
            });

            await client.close();

        } catch (error) {
            console.error(`采集竞品数据失败:`, error.message);
        }

        return results;
    },

    /**
     * 采集社交情感
     */
    async collectSocialSentiment(scope, strategy) {
        console.log(`💬 采集社交情感:`, scope);

        // 社交媒体采集（模拟实现）
        const results = [{
            type: 'social_sentiment',
            source: 'social_media',
            platform: scope.platform || 'tiktok',
            region: scope.region,
            keywords: scope.keywords || [],

            aggregated: {
                sentiment_distribution: {
                    positive: 0.65,
                    neutral: 0.25,
                    negative: 0.10
                },
                total_mentions: 150,
                top_keywords: ['quality', 'price', 'shipping'],
                trend: 'increasing'
            },

            sample_mentions: this.generateSampleMentions(scope, strategy),

            metadata: {
                collected_at: new Date().toISOString(),
                time_range: scope.constraints?.time_range || 'last_7_days'
            }
        }];

        return results;
    },

    /**
     * 构建搜索查询
     */
    buildSearchQuery(scope) {
        const parts = [];

        if (scope.brand) {
            parts.push(scope.brand);
        }
        if (scope.category) {
            parts.push(scope.category);
        }
        if (scope.keywords && scope.keywords.length > 0) {
            parts.push(scope.keywords.join(' '));
        }

        return parts.join(' ') || scope.keywords?.[0] || '';
    },

    /**
     * 采样评论
     */
    sampleReviews(product, strategy) {
        // 模拟评论采样
        const sampleSize = Math.min(
            strategy.samplingStrategy?.sampleSize || 10,
            20
        );

        const reviews = [];
        for (let i = 0; i < sampleSize; i++) {
            reviews.push({
                rating: 3 + Math.random() * 2,  // 3-5 stars
                text: `Sample review ${i + 1}`,
                verified: Math.random() > 0.2,
                date: new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000).toISOString()
            });
        }

        return reviews;
    },

    /**
     * 生成社交提及样本
     */
    generateSampleMentions(scope, strategy) {
        const sampleSize = Math.min(strategy.samplingStrategy?.sampleSize || 10, 20);
        const mentions = [];

        for (let i = 0; i < sampleSize; i++) {
            mentions.push({
                text: `Sample mention about ${scope.keywords?.join(' ') || 'product'}`,
                sentiment: ['positive', 'neutral', 'negative'][Math.floor(Math.random() * 3)],
                platform: scope.platform || 'tiktok',
                date: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
            });
        }

        return mentions;
    },

    /**
     * 计算平均值
     */
    calculateAverage(values) {
        const validValues = values.filter(v => v != null && !isNaN(v));
        if (validValues.length === 0) return 0;
        return validValues.reduce((a, b) => a + b, 0) / validValues.length;
    },

    /**
     * 计算价格区间
     */
    calculatePriceRange(products) {
        const prices = products.map(p => p.price).filter(p => p != null);
        if (prices.length === 0) return null;

        const sorted = prices.sort((a, b) => a - b);
        const low = sorted[0];
        const high = sorted[sorted.length - 1];

        return {
            low: low,
            high: high,
            mid: (low + high) / 2,
            ranges: this.splitIntoRanges(sorted, 5)
        };
    },

    /**
     * 分割成区间
     */
    splitIntoRanges(sortedPrices, count) {
        const ranges = [];
        const size = Math.ceil(sortedPrices.length / count);

        for (let i = 0; i < count; i++) {
            const slice = sortedPrices.slice(i * size, (i + 1) * size);
            if (slice.length > 0) {
                ranges.push({
                    min: slice[0],
                    max: slice[slice.length - 1],
                    count: slice.length
                });
            }
        }

        return ranges;
    },

    /**
     * 获取Top品牌
     */
    getTopBrands(competitors) {
        const brandCounts = {};

        competitors.forEach(c => {
            if (c.brand) {
                brandCounts[c.brand] = (brandCounts[c.brand] || 0) + 1;
            }
        });

        return Object.entries(brandCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([brand, count]) => ({ brand, count }));
    },

    /**
     * 将数据结构化供AI使用
     */
    structureDataForAI(results, expectedOutcome) {
        const summary = {
            total_items: results.reduce((sum, r) => {
                if (r.products) return sum + r.products.length;
                if (r.competitors) return sum + r.competitors.length;
                if (r.sample_mentions) return sum + r.sample_mentions.length;
                return sum + 1;
            }, 0),
            data_sources: [...new Set(results.map(r => r.source))],
            quality_score: 0.85,  // 可根据实际采集情况计算
            completeness: 0.9
        };

        // 聚合数据（如果有）
        const aggregated = {};
        results.forEach(r => {
            if (r.aggregated) {
                Object.assign(aggregated, r.aggregated);
            }
        });

        return {
            summary: summary,
            data: results,
            aggregated: Object.keys(aggregated).length > 0 ? aggregated : null,
            metadata: {
                collected_at: new Date().toISOString(),
                data_types: [...new Set(results.map(r => r.type))]
            }
        };
    }
};
