-- Recalcula los KPIs de los últimos 2 días (idempotente: MERGE en lugar de INSERT)
MERGE `${curated_table}` AS t
USING (
  SELECT
    DATE(event_ts)              AS day,
    IFNULL(country, 'NA')       AS country,
    event_type,
    COUNT(DISTINCT event_id)    AS events,
    COUNT(DISTINCT user_id)     AS unique_users,
    SUM(IF(event_type = 'purchase', amount, 0)) AS revenue
  FROM `${raw_table}`
  WHERE event_ts >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY))
  GROUP BY day, country, event_type
) AS s
ON t.day = s.day AND t.country = s.country AND t.event_type = s.event_type
WHEN MATCHED THEN
  UPDATE SET events = s.events, unique_users = s.unique_users, revenue = s.revenue
WHEN NOT MATCHED THEN
  INSERT (day, country, event_type, events, unique_users, revenue)
  VALUES (s.day, s.country, s.event_type, s.events, s.unique_users, s.revenue)
