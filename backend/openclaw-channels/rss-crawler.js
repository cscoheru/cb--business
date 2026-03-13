/**
 * OpenClaw Channel: RSS Crawler (Fresh Data)
 * 
 * 功能：从RSS源直接采集最新文章
 * 调度：每2小时
 * 超时：5分钟
 */

const http = require('http');
const https = require('https');
const { parseString } = require('xml2js');

// 配置
const FASTAPI_URL = 'http://127.0.0.1:8000';

// RSS源列表 - 优先使用可用的源
const RSS_SOURCES = [
    { url: 'https://techcrunch.com/feed/', name: 'TechCrunch', language: 'en' },
    { url: 'https://www.pymnts.com/feed/', name: 'PYMNTS', language: 'en' },
    { url: 'https://feeds.arstechnica.com/arstechnica/index', name: 'Ars Technica', language: 'en' },
    { url: 'https://www.theverge.com/rss/index.xml', name: 'The Verge', language: 'en' },
    { url: 'https://www.wired.com/feed/rss', name: 'Wired', language: 'en' },
    { url: 'https://www.businessinsider.com/sai/rss', name: 'Business Insider', language: 'en' },
    { url: 'https://nrf.com/blog/feed', name: 'NRF Retail Blog', language: 'en' },
    { url: 'https://www.practicalecommerce.com/feed', name: 'Practical Ecommerce', language: 'en' },
    { url: 'https://marketplacepulse.com/feed', name: 'Marketplace Pulse', language: 'en' },
    { url: 'https://www.aboutamazon.com/news/feed', name: 'Amazon News', language: 'en' },
    { url: 'https://www.mercopress.com/rss/feed', name: 'Mercopress', language: 'es' },
    { url: 'https://www.techinasia.com/feed', name: 'Tech in Asia', language: 'en' },
    { url: 'https://e27.co/feed', name: 'e27', language: 'en' },
];

/**
 * 发起HTTP请求获取RSS内容
 */
function fetchRSS(url, timeout = 15000) {
    return new Promise((resolve, reject) => {
        const client = url.startsWith('https') ? https : http;
        
        const options = {
            headers: {
                'User-Agent': 'Mozilla/5.0 (compatible; OpenClaw-RSS/1.0)',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*'
            },
            timeout: timeout
        };

        const req = client.request(url, options, (res) => {
            let data = '';
            
            if (res.statusCode === 301 || res.statusCode === 302) {
                const redirectUrl = res.headers.location;
                if (redirectUrl) {
                    return fetchRSS(redirectUrl, timeout).then(resolve).catch(reject);
                }
            }
            
            if (res.statusCode !== 200) {
                return reject(new Error(`HTTP ${res.statusCode}`));
            }
            
            res.setEncoding('utf8');
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        });
        
        req.on('error', reject);
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Request timeout'));
        });
        
        req.setTimeout(timeout);
        req.end();
    });
}

/**
 * 解析RSS XML内容
 */
function parseRSS(xmlContent, sourceName, language) {
    return new Promise((resolve, reject) => {
        parseString(xmlContent, { explicitArray: false, mergeAttrs: true }, (err, result) => {
            if (err) return reject(err);

            try {
                const items = [];
                const channel = result.rss?.channel || result.feed || result;
                const articles = channel.item || channel.entry || [];

                const articleArray = Array.isArray(articles) ? articles : [articles];

                articleArray.forEach(item => {
                    const title = item.title?.['#'] || item.title || 'Untitled';
                    let link = item.link?.['#'] || item.link || item.id || '';
                    
                    if (Array.isArray(item.link)) {
                        const hrefLink = item.link.find(l => l.$.href);
                        if (hrefLink) link = hrefLink.$.href;
                    }
                    
                    const description = item.description?.['#'] || item.description || 
                                     item.summary?.['#'] || item.summary || '';
                    
                    const content = item['content:encoded'] || description;
                    const pubDate = item.pubDate || item.published || item.updated;

                    const cleanContent = description.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();

                    items.push({
                        title: title.substring(0, 500),
                        summary: cleanContent.substring(0, 1000),
                        content: content.substring(0, 10000),
                        url: link,
                        source_name: `openclaw-${sourceName}`,
                        language: language,
                        published_at: pubDate ? new Date(pubDate).toISOString() : new Date().toISOString()
                    });
                });

                resolve(items);
            } catch (e) {
                reject(e);
            }
        });
    });
}

/**
 * 调用FastAPI批量写入文章
 */
async function pushArticlesToFastAPI(articles) {
    return new Promise((resolve, reject) => {
        const url = new URL('/api/v1/batch/articles', FASTAPI_URL);
        
        const data = JSON.stringify({
            articles: articles,
            source: 'openclaw-rss',
            batch_id: `rss-${Date.now()}`
        });

        const options = {
            hostname: url.hostname,
            port: url.port || 80,
            path: url.pathname,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            }
        };

        const req = http.request(options, (res) => {
            let responseData = '';
            res.on('data', chunk => responseData += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(responseData));
                } catch (e) {
                    resolve({ success: false, error: 'Invalid JSON response' });
                }
            });
        });

        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

/**
 * 从单个RSS源采集文章
 */
async function fetchFromSource(source, maxArticles = 20) {
    try {
        console.log(`[RSS Crawler] Fetching from ${source.name}...`);
        
        const xmlContent = await fetchRSS(source.url, 10000);
        const articles = await parseRSS(xmlContent, source.name, source.language);
        
        const limitedArticles = articles.slice(0, maxArticles);
        
        console.log(`[RSS Crawler] Got ${limitedArticles.length} articles from ${source.name}`);
        
        return {
            source: source.name,
            success: true,
            articles: limitedArticles,
            error: null
        };
    } catch (error) {
        console.error(`[RSS Crawler] Failed to fetch ${source.name}: ${error.message}`);
        return {
            source: source.name,
            success: false,
            articles: [],
            error: error.message
        };
    }
}

/**
 * 主执行函数
 */
async function run(params = {}) {
    console.log('[RSS Crawler] Starting execution...');
    const startTime = Date.now();

    try {
        const maxSources = params.sources || 5;
        const maxPerSource = params.maxPerSource || 20;
        
        console.log(`[RSS Crawler] Fetching from ${maxSources} RSS sources...`);

        const sourcesToFetch = RSS_SOURCES.slice(0, maxSources);
        const results = await Promise.all(
            sourcesToFetch.map(source => fetchFromSource(source, maxPerSource))
        );

        const allArticles = [];
        let successCount = 0;
        let failCount = 0;

        for (const result of results) {
            if (result.success) {
                successCount++;
                allArticles.push(...result.articles);
            } else {
                failCount++;
            }
        }

        console.log(`[RSS Crawler] Total articles fetched: ${allArticles.length}`);

        if (allArticles.length === 0) {
            return {
                success: true,
                channel: 'rss-crawler',
                stats: {
                    sources: maxSources,
                    successful: successCount,
                    failed: failCount,
                    total_fetched: 0,
                    total_pushed: 0,
                    duration_ms: Date.now() - startTime
                },
                message: 'No articles fetched from any source'
            };
        }

        console.log(`[RSS Crawler] Pushing ${allArticles.length} articles to FastAPI...`);
        const pushResult = await pushArticlesToFastAPI(allArticles);

        const duration = Date.now() - startTime;
        console.log(`[RSS Crawler] Completed in ${duration}ms`);

        return {
            success: true,
            channel: 'rss-crawler',
            execution_id: params.execution_id || `exec-${Date.now()}`,
            stats: {
                sources: maxSources,
                successful: successCount,
                failed: failCount,
                total_fetched: allArticles.length,
                total_pushed: pushResult.created || pushResult.total || allArticles.length,
                failed: pushResult.failed || 0,
                duration_ms: duration
            },
            message: `Successfully processed ${allArticles.length} articles from ${successCount}/${maxSources} sources`,
            result: pushResult
        };

    } catch (error) {
        console.error('[RSS Crawler] Error:', error);
        return {
            success: false,
            channel: 'rss-crawler',
            error: error.message,
            duration_ms: Date.now() - startTime
        };
    }
}

module.exports = {
    id: 'rss-crawler',
    name: 'RSS Article Crawler (Fresh Data)',
    version: '2.0.0',
    schedule: '0 */2 * * *',
    timeout: 300000,
    description: '直接从RSS源采集最新文章',
    run: run
};

if (require.main === module) {
    run({ sources: 5, maxPerSource: 20 }).then(result => {
        console.log('Result:', JSON.stringify(result, null, 2));
        process.exit(result.success ? 0 : 1);
    }).catch(error => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}
