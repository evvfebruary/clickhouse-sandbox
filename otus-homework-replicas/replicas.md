## Домашнее задание по репликации
## Replica
![img.png](
screenshots/img.png)


### 1. Взять любой демонстрационный DATASET, не обязательно полный набор данных:
https://clickhouse.com/docs/en/getting-started/example-datasets
```sql
-- Взял данные про недвижимость в UK, создаем 
CREATE DATABASE otus_hw_replication ON CLUSTER cluster_4R;
CREATE TABLE otus_hw_replication.uk_price_paid on cluster cluster_4R
(
    price UInt32,
    date Date, -- Кстати колонка date уже на месте, приятно
    postcode1 LowCardinality(String),
    postcode2 LowCardinality(String),
    type Enum8('terraced' = 1, 'semi-detached' = 2, 'detached' = 3, 'flat' = 4, 'other' = 0),
    is_new UInt8,
    duration Enum8('freehold' = 1, 'leasehold' = 2, 'unknown' = 0),
    addr1 String,
    addr2 String,
    street LowCardinality(String),
    locality LowCardinality(String),
    town LowCardinality(String),
    district LowCardinality(String),
    county LowCardinality(String)
)
ENGINE = MergeTree
ORDER BY (postcode1, postcode2, addr1, addr2);

INSERT INTO otus_hw_replication.uk_price_paid
WITH
   splitByChar(' ', postcode) AS p
SELECT
    toUInt32(price_string) AS price,
    parseDateTimeBestEffortUS(time) AS date,
    p[1] AS postcode1,
    p[2] AS postcode2,
    transform(a, ['T', 'S', 'D', 'F', 'O'], ['terraced', 'semi-detached', 'detached', 'flat', 'other']) AS type,
    b = 'Y' AS is_new,
    transform(c, ['F', 'L', 'U'], ['freehold', 'leasehold', 'unknown']) AS duration,
    addr1,
    addr2,
    street,
    locality,
    town,
    district,
    county
FROM url(
    'http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-complete.csv',
    'CSV',
    'uuid_string String,
    price_string String,
    time String,
    postcode String,
    a String,
    b String,
    c String,
    addr1 String,
    addr2 String,
    street String,
    locality String,
    town String,
    district String,
    county String,
    d String,
    e String'
) LIMIT 1000 SETTINGS max_http_get_redirects=10;
```

### 2.Конвертировать таблицу в реплицируемую, используя макрос replica
```sql
-- Создаем новую таблицу с движком репликации
CREATE TABLE otus_hw_replication.uk_price_paid_replicated on cluster cluster_4R
    AS otus_hw_replication.uk_price_paid
        ENGINE ReplicatedMergeTree('/clickhouse/tables/{database}/{table}', 'replicas_{shard}_{replica}')
        ORDER BY (postcode1, postcode2, addr1, addr2);

-- Перекидываем партиции в новую таблицу
ALTER TABLE otus_hw_replication.uk_price_paid_replicated ATTACH PARTITION ID
'all' FROM otus_hw_replication.uk_price_paid;
```

### 3,4. Добавляем реплики и проверяем работоспособность:
```sql
-- Забираем информацию по партициям со всех реплик
SELECT
getMacro('replica'),
*
FROM remote('clickhouse-02,clickhouse-03,clickhouse-04',system.parts)
FORMAT JSONEachRow;
```
Результат:
[getMacro__replica_.csv](files%2FgetMacro__replica_.csv)

```sql
SELECT * FROM system.replicas FORMAT JSONEachRow;
```
Результат: 
[system_replicas.csv](files%2Fsystem_replicas.csv)    

### 5. Добавить/выбрать колонку с типом Date в таблице, добавить TTL на таблицу «хранить последние 7 дней».       Предоставить результат запроса «SHOW CREATE TABLE таблица» на проверку.
```sql
-- Добавляем ttl
ALTER TABLE otus_hw_replication.uk_price_paid_replicated ON CLUSTER cluster_4R MODIFY TTL date + INTERVAL 7 DAY;
SHOW CREATE TABLE otus_hw_replication.uk_price_paid_replicated;

CREATE TABLE otus_hw_replication.uk_price_paid_replicated
(
    `price` UInt32,
    `date` Date,
    `postcode1` LowCardinality(String),
    `postcode2` LowCardinality(String),
    `type` Enum8('other' = 0, 'terraced' = 1, 'semi-detached' = 2, 'detached' = 3, 'flat' = 4),
    `is_new` UInt8,
    `duration` Enum8('unknown' = 0, 'freehold' = 1, 'leasehold' = 2),
    `addr1` String,
    `addr2` String,
    `street` LowCardinality(String),
    `locality` LowCardinality(String),
    `town` LowCardinality(String),
    `district` LowCardinality(String),
    `county` LowCardinality(String)
)
ENGINE = ReplicatedMergeTree('/clickhouse/tables/otus_hw_replication/uk_price_paid_replicated', 'replicas_{shard}_{replica}')
ORDER BY (postcode1, postcode2, addr1, addr2)
TTL date + toIntervalDay(7)
SETTINGS index_granularity = 8192
```