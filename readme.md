CMC Data Collector
A Python script that fetches cryptocurrency market data from CoinMarketCap API and stores it in a Supabase database. The script collects:

Global market metrics (market caps, volumes, dominance)
Top 100 cryptocurrencies data (prices, volumes, supply info)

Setup

Clone the repository
Install dependencies:

bashCopypip install python-dotenv requests supabase

Create a .env file with your credentials:

CopySUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
CMC_API_KEY=your_cmc_api_key

Set up the database tables in Supabase SQL Editor:

sqlCopy-- Global Metrics Table
create table global_metrics (
    id bigint primary key generated always as identity,
    timestamp timestamptz not null,
    btc_dominance numeric(10,2),
    eth_dominance numeric(10,2),
    total_market_cap numeric,
    total_volume_24h numeric,
    total_volume_24h_reported numeric,
    altcoin_volume_24h numeric,
    altcoin_volume_24h_reported numeric,
    altcoin_market_cap numeric,
    defi_volume_24h numeric,
    defi_volume_24h_reported numeric,
    defi_market_cap numeric,
    defi_24h_percentage_change numeric(10,2),
    stablecoin_volume_24h numeric,
    stablecoin_volume_24h_reported numeric,
    stablecoin_market_cap numeric,
    derivatives_volume_24h numeric,
    derivatives_volume_24h_reported numeric,
    total_market_cap_yesterday numeric,
    total_volume_24h_yesterday numeric,
    market_cap_change_24h numeric(10,2),
    volume_change_24h numeric(10,2),
    last_updated timestamptz
);

-- Coins Table
create table coins (
    id bigint primary key generated always as identity,
    timestamp timestamptz not null,
    cmc_id integer not null,
    name text not null,
    symbol text not null,
    slug text not null,
    cmc_rank integer,
    num_market_pairs integer,
    circulating_supply numeric,
    total_supply numeric,
    max_supply numeric,
    infinite_supply boolean,
    last_updated timestamptz,
    date_added timestamptz,
    tags text[],
    platform text,
    self_reported_circulating_supply numeric,
    self_reported_market_cap numeric,
    price_usd numeric,
    volume_24h numeric,
    volume_change_24h numeric,
    percent_change_1h numeric,
    percent_change_24h numeric,
    percent_change_7d numeric,
    percent_change_30d numeric,
    market_cap numeric,
    market_cap_dominance numeric,
    fully_diluted_market_cap numeric
);

-- Enable RLS and set permissions
alter table global_metrics enable row level security;
alter table coins enable row level security;

-- Create policies for anonymous access
create policy "allow_anonymous_select" on global_metrics for select to anon using (true);
create policy "allow_anonymous_select" on coins for select to anon using (true);

-- Grant permissions
grant select, insert on global_metrics to anon;
grant select, insert on coins to anon;

-- Create useful indexes
create index idx_coins_timestamp on coins(timestamp desc);
create index idx_coins_cmc_rank on coins(cmc_rank);
create index idx_coins_market_cap on coins(market_cap desc);
create index idx_coins_symbol on coins(symbol);
create index idx_coins_name on coins(name);

Run the script:

bashCopypython fetcher.py
How it Works
The script runs in a continuous loop:

Every 5 minutes, it fetches:

Global market metrics
Data for top 100 cryptocurrencies


Data is timestamped and stored in Supabase
Historical data is maintained for analysis

Example Queries
Get latest Bitcoin price:
sqlCopySELECT timestamp, price_usd 
FROM coins 
WHERE symbol = 'BTC' 
ORDER BY timestamp DESC 
LIMIT 1;
Get latest global market cap:
sqlCopySELECT timestamp, total_market_cap 
FROM global_metrics 
ORDER BY timestamp DESC 
LIMIT 1;
Get hourly average prices for any coin:
sqlCopySELECT 
    date_trunc('hour', timestamp) as hour,
    avg(price_usd) as avg_price
FROM coins 
WHERE symbol = 'ETH' 
    AND timestamp > now() - interval '24 hours'
GROUP BY date_trunc('hour', timestamp)
ORDER BY hour DESC;
Notes

Data is collected every 5 minutes
Historical data is preserved
Designed for AI agents to easily query market data
Uses public schema for easy access
Requires CoinMarketCap API key (get from https://coinmarketcap.com/api/)
Requires Supabase project setup (create at https://supabase.com)