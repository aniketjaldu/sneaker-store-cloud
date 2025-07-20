SELECT 
  b.brand_name,
  p.product_name,
  ROUND(p.market_price * (1 - p.discount_percent / 100), 2) AS current_price,
  p.market_price,
  p.discount_percent
FROM 
  products p
JOIN 
  brands b ON p.brand_id = b.brand_id
ORDER BY 
  b.brand_name ASC,
  p.product_name ASC;

