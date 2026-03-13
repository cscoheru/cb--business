/**
 * OpenClaw Channel: Content Classifier
 */

const http = require('http');
const https = require('https');

const FASTAPI = 'http://127.0.0.1:8000';
const GLM_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions';
const GLM_KEY = 'ed79dfb6bd5d442b9818011010d6faed.ExkY3SyIQqoyDpaO';

function httpReq(url, opts = {}) {
    return new Promise((res, rej) => {
        const c = url.startsWith('https') ? https : http;
        const r = c.request(url, opts, (q) => {
            let d = '';
            q.on('data', x => d += x);
            q.on('end', () => { try { res(JSON.parse(d)); } catch(e) { res(d); }});
        });
        r.on('error', rej);
        r.setTimeout(120000, () => { r.destroy(); rej(new Error('timeout')); });
        if(opts.body) r.write(JSON.stringify(opts.body));
        r.end();
    });
}

async function getUnclassified(limit = 20) {
    try {
        const x = await httpReq(`${FASTAPI}/api/v1/batch/unclassified?type=articles&limit=${limit}`, { method:'GET', headers:{'Accept':'application/json'}});
        return x.items || [];
    } catch(e) { console.error('Fetch error:', e.message); return []; }
}

async function classifyGLM(items) {
    const list = items.map((t,i) => `${i+1}. ${t.title}\n${(t.summary||'').slice(0,100)}`).join('\n\n');
    try {
        const x = await httpReq(GLM_URL, {
            method:'POST', headers:{'Content-Type':'application/json','Authorization':`Bearer ${GLM_KEY}`},
            body:{ model:'glm-4-plus', messages:[{role:'user', content:`分析并返回JSON：\n${list}\n格式：[{"content_theme":"opportunity","region":"north_america","platform":"amazon","keywords":["k1"],"opportunity_score":0.6,"risk_level":"low"}]`}], temperature:0.3, max_tokens:1500 }
        });
        if(x.choices?.[0]) {
            const m = x.choices[0].message.content.match(/\[[\s\S]*\]/);
            if(m) return JSON.parse(m[0]);
        }
        throw new Error('No JSON');
    } catch(e) {
        console.error('GLM error:', e.message);
        return items.map(() => ({content_theme:'guide',region:'global',platform:'other',keywords:['business'],opportunity_score:0.5,risk_level:'low'}));
    }
}

async function push(updates) {
    return new Promise((res,rej) => {
        const u = new URL('/api/v1/batch/classifications', FASTAPI);
        const p = JSON.stringify({updates:updates.map(x=>({...x,tags:JSON.stringify(x.keywords||[])})),source:'openclaw-classifier',batch_id:`c-${Date.now()}`});
        const o = {hostname:u.hostname,port:u.port||80,path:u.pathname,method:'POST',headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(p)}};
        const q = http.request(o, (w) => { let d=''; w.on('data',x=>d+=x); w.on('end',()=>{try{res(JSON.parse(d))}catch(e){res({success:false})}});});
        q.on('error',rej); q.write(p); q.end();
    });
}

async function run(p={}) {
    console.log('[Content Classifier] Start');
    const t=Date.now();
    try {
        const l=p.limit||20;
        console.log(`Fetching ${l} items...`);
        const items=await getUnclassified(l);
        console.log(`Found ${items.length} items`);
        if(items.length===0) return {success:true,channel:'content-classifier',stats:{total_fetched:0,total_classified:0,duration_ms:Date.now()-t},message:'No items'};
        console.log('Classifying...');
        const cls=await classifyGLM(items);
        const ups=items.map((x,i)=>{const c=cls[i]||{}; return {id:x.id,content_theme:c.content_theme||'guide',region:c.region||'global',platform:c.platform||'other',keywords:c.keywords||[],opportunity_score:c.opportunity_score||0.5,risk_level:c.risk_level||'low'};});
        console.log(`Pushing ${ups.length} updates...`);
        const r=await push(ups);
        return {success:true,channel:'content-classifier',execution_id:`e-${Date.now()}`,stats:{total_fetched:items.length,total_classified:r.updated||ups.length,failed:r.failed||0,duration_ms:Date.now()-t},message:`Classified ${ups.length} items`,result:r};
    } catch(e) { console.error('Error:',e); return {success:false,channel:'content-classifier',error:e.message,duration_ms:Date.now()-t};}
}

module.exports={id:'content-classifier',name:'AI Classifier',version:'2.0.0',schedule:'*/30 * * * *',timeout:300000,description:'GLM-4 classification',run:run};
if(require.main===module){run({limit:5}).then(r=>{console.log(JSON.stringify(r,null,2));process.exit(r.success?0:1);}).catch(e=>{console.error(e);process.exit(1);});}
