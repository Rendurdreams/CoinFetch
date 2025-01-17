# CMC Data Collector for AI Systems

An automated cryptocurrency market data collection and analysis system designed for AI consumption. The system collects detailed market data and generates periodic analysis reports, making it ideal for AI agents needing real-time and historical crypto market data.

## System Overview

### Data Collection
- Collects data every 5 minutes from CoinMarketCap API
- Stores in Supabase for easy AI accessibility
- Maintains historical data with timestamps

### Data Types
1. Global Market Metrics:
   - Total market capitalization
   - Trading volumes
   - Market dominance
   - DeFi metrics
   - Stablecoin data
   
2. Top 100 Cryptocurrencies:
   - Price data
   - Volume metrics
   - Supply information
   - Market caps
   - Price changes (1h, 24h, 7d, 30d)

## AI Integration Points

### Data Access
```sql
-- Get latest market state
SELECT * FROM global_metrics 
ORDER BY timestamp DESC 
LIMIT 1;

-- Get specific coin metrics
SELECT * FROM coins 
WHERE symbol = 'BTC' 
ORDER BY timestamp DESC 
LIMIT 1;

-- Get trend analysis
SELECT 
    symbol,
    price_usd,
    percent_change_24h,
    market_cap_dominance
FROM coins 
WHERE timestamp = (SELECT MAX(timestamp) FROM coins)
ORDER BY market_cap DESC
LIMIT 10;
```

### Use Cases for AI
1. Market Analysis:
   - Price trend detection
   - Volume analysis
   - Market dominance shifts
   - Correlation analysis

2. Risk Assessment:
   - Volatility tracking
   - Market health indicators
   - Liquidity analysis

3. Pattern Recognition:
   - Price movement patterns
   - Volume anomalies
   - Market sentiment indicators

## Setup Instructions

1. Environment Setup:
```bash
pip install python-dotenv requests supabase
```

2. Configuration (.env file):
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
CMC_API_KEY=your_cmc_api_key
```

3. Database Setup:
```sql
-- Create report table for automated analysis
create table market_reports (
    id bigint primary key generated always as identity,
    timestamp timestamptz not null,
    report_type text not null,
    summary jsonb not null,
    metrics jsonb not null,
    insights text[],
    anomalies jsonb,
    recommendations text[]
);

-- Enable RLS and access
alter table market_reports enable row level security;
create policy "allow_anonymous_select" on market_reports for select to anon using (true);
grant select on market_reports to anon;

-- (Previous tables setup SQL here...)
```

## Coming Soon: Automated Analysis
- 6-hour interval market analysis reports
- Key metrics and trends identification
- Anomaly detection
- Market sentiment analysis
- Performance correlations
- Volume analysis
- Risk metrics

## Notes for AI Consumption
- All timestamps are in UTC
- Numeric values use standard decimal format
- Missing values are explicitly null
- Boolean flags used for status indicators
- Arrays used for multiple values
- JSONB fields for complex data structures

## Data Update Frequencies
- Market Data: Every 5 minutes
- Coin Data: Every 5 minutes
- Analysis Reports: Every 6 hours (coming soon)

## Error Handling
- Network errors logged
- Missing data handled gracefully
- Data validation on insert
- Automatic retry on failure

## Best Practices for AI Queries
1. Always check timestamps for data freshness
2. Use appropriate time ranges for trend analysis
3. Consider data granularity for analysis
4. Handle NULL values appropriately
5. Use indexes for efficient queries

## System Schema
```plaintext
Data Flow:
CMC API → Data Collector → Supabase → AI Access
                       ↓
              Analysis Engine (Coming Soon)
                       ↓
              Analysis Reports Table
```

For AI development support or system integration questions, please open an issue on the repository.
