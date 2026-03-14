INSERT INTO cards (id, title, category, content, analysis, amazon_data, is_published, created_at, published_at, views, likes)
VALUES
  ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', '无线耳机市场信息 - 2026-03-13', 'wireless_earbuds',
   '{"summary":{"title":"无线耳机","opportunity_score":85,"market_size":16,"sweet_spot":{"min":20,"max":30,"best":25},"reliability":0.95},"market_data":{"price":{"min":15,"max":80,"avg":32,"count":16},"rating":{"min":3.8,"max":4.7,"avg":4.3,"count":14}},"insights":{"price_sweet_spot":{"min":20,"max":30,"best":25},"top_products":[{"asin":"B0B66CJZL5","title":"Anker P20i True Wireless","price":19.99,"rating":4.6,"reviews_count":97900}],"market_saturation":"high"},"recommendations":["目标价格: $25-35","核心卖点: 防丢失设计 + 稳定连接"],"data_sources":["Oxylabs Amazon API (95%)"],"generated_at":"2026-03-13T09:00:00"}'::jsonb,
   '{"category":"wireless_earbuds","category_name":"无线耳机","market_data":{"total_products":16},"opportunity_score":85}'::jsonb,
   '{"products":[{"asin":"B0B66CJZL5","title":"Anker P20i True Wireless","price":19.99,"rating":4.6,"reviews_count":97900}]}'::jsonb,
   true, NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC', 142, 23),

  ('b2c3d4e5-f6a7-8901-bcde-f12345678901', '智能插座市场信息 - 2026-03-13', 'smart_plugs',
   '{"summary":{"title":"智能插座","opportunity_score":72,"market_size":14,"sweet_spot":{"min":20,"max":30,"best":25},"reliability":0.95},"market_data":{"price":{"min":12,"max":45,"avg":26,"count":14},"rating":{"min":3.9,"max":4.6,"avg":4.3,"count":12}},"insights":{"price_sweet_spot":{"min":20,"max":30,"best":25},"top_products":[{"asin":"B08R6WK6W8","title":"Kasa Smart Plug HS103P","price":14.99,"rating":4.6,"reviews_count":285000}],"market_saturation":"high"},"recommendations":["目标价格: $20-30","核心功能: 能耗监测"],"data_sources":["Oxylabs Amazon API (95%)"],"generated_at":"2026-03-13T09:00:00"}'::jsonb,
   '{"category":"smart_plugs","category_name":"智能插座","market_data":{"total_products":14},"opportunity_score":72}'::jsonb,
   '{"products":[{"asin":"B08R6WK6W8","title":"Kasa Smart Plug HS103P","price":14.99,"rating":4.6,"reviews_count":285000}]}'::jsonb,
   true, NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC', 89, 15),

  ('c3d4e5f6-a7b8-9012-cdef-123456789012', '健身追踪器市场信息 - 2026-03-13', 'fitness_trackers',
   '{"summary":{"title":"健身追踪器","opportunity_score":78,"market_size":18,"sweet_spot":{"min":30,"max":50,"best":45},"reliability":0.95},"market_data":{"price":{"min":25,"max":150,"avg":58,"count":18},"rating":{"min":3.7,"max":4.7,"avg":4.2,"count":16}},"insights":{"price_sweet_spot":{"min":30,"max":50,"best":45},"top_products":[{"asin":"B0BPHHZ6HS","title":"Fitbit Inspire 3","price":79.95,"rating":4.6,"reviews_count":18500}],"market_saturation":"medium"},"recommendations":["目标价格: $40-60","核心功能: 长续航"],"data_sources":["Oxylabs Amazon API (95%)"],"generated_at":"2026-03-13T09:00:00"}'::jsonb,
   '{"category":"fitness_trackers","category_name":"健身追踪器","market_data":{"total_products":18},"opportunity_score":78}'::jsonb,
   '{"products":[{"asin":"B0BPHHZ6HS","title":"Fitbit Inspire 3","price":79.95,"rating":4.6,"reviews_count":18500}]}'::jsonb,
   true, NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC', 156, 31);
