# Материализированные представления
### Создание таблицы:
- Создайте таблицу sales с полями:
- id (UInt32) — уникальный идентификатор продажи
- product_id (UInt32) — идентификатор продукта
- quantity (UInt32) — количество проданных единиц
- price (Float32) — цена за единицу
- sale_date (DateTime) — дата продажи
- Заполните таблицу тестовыми данными.

```sql
-- Создаем тестовую табличку
CREATE TABLE sales(
    id UInt32,
    product_id UInt32,
    quantity UInt32,
    price Float32,
    sale_date DATETIME
) Engine MergeTree()
ORDER BY product_id;

-- Заполняем тестовыми данными
INSERT INTO sales
SELECT
    abs(rand32()) as id,
    abs(rand()%30) as product_id,
    abs(rand()%50) as quantity,
    round(randNormal(10,2),2) as price,
    toDateTime('2024-01-01 00:00:00')
    + INTERVAL (rand() % 12) MONTH
    + INTERVAL (rand() % 28) DAY
    + INTERVAL (rand() % 24) HOUR
    + INTERVAL (rand() % 60) MINUTE
    + INTERVAL (rand() % 60) SECOND AS sale_date
FROM numbers(10000);
```


### Создание проекции:
- Создайте проекцию для таблицы sales, которая будет агрегировать данные по product_id и считать общую сумму продаж (количество и сумма по цене) за каждый продукт.
```sql
-- Создаем проекцию
ALTER TABLE sales ADD PROJECTION sales_proj (
    SELECT
        product_id,
        SUM(quantity) as total_quantity,
        SUM(price) as total_sales
    GROUP BY product_id
);
-- Материализуем ее
ALTER TABLE sales MATERIALIZE PROJECTION sales_proj;
```

### Создание материализованного представления:
- Создайте материализованное представление sales_mv, которое будет автоматически обновляться при вставке новых данных в таблицу sales. Оно должно хранить общие продажи по продуктам с полями:
- product_id
- total_quantity
- total_sales
```sql
CREATE MATERIALIZED VIEW sales_mv
ENGINE = SummingMergeTree()
ORDER BY product_id
POPULATE AS
    SELECT
        sales.product_id,
        sum(quantity) as total_quantity,
        sum(price) as total_sales
    FROM sales
GROUP BY product_id;
```


### Запросы к данным:
- Напишите запрос, который извлекает данные из проекции sales_projection.
```sql
--  Попадем в проекцию
SELECT
        product_id,
        SUM(quantity) as total_quantity,
        SUM(price) as total_sales
FROM sales
GROUP BY product_id;

-- Проверим что попали!
SELECT query,
       projections
FROM system.query_log
         WHERE databases = ['mv_experiments']
         ORDER BY event_time DESC LIMIT 1 FORMAT Vertical;

+------------------------------------------------+
|results                                         |
+------------------------------------------------+
|Row 1:                                          |
|──────                                          |
|query:       SELECT                             |
|        product_id,                             |
|        SUM(quantity) as total_quantity,        |
|        SUM(price) as total_sales               |
|FROM sales                                      |
|GROUP BY product_id                             |
|projections: ['mv_experiments.sales.sales_proj']|
+------------------------------------------------+


```
- Напишите запрос, который извлекает данные из материализованного представления sales_mv.
```sql
-- Забираем финальный результат агрегируя строчки из материализованного представления ( которое отрабатывает на каждый инсерт )
SELECT
        product_id,
        SUM(total_quantity) as total_quantity,
        SUM(total_sales) as total_sales
FROM sales_mv
GROUP BY product_id;
```


### Сравнение производительности:
- Сравните время выполнения запроса к основной таблице sales с запросом к проекции sales_projection и материализованному представлению sales_mv. Обратите внимание на разницу в производительности.
```sql
-- Сделаем легкий бенчмарк
SELECT
    count(query) as query_cnt,
    query,
    tables,
    projections,
    quantiles(0.25, 0.5, 0.75, 0.95)(query_duration_ms) as duration_quants,
    quantiles(0.25, 0.5, 0.75, 0.95)(memory_usage) as memory_quants,
    quantiles(0.25, 0.5, 0.75, 0.95)(read_bytes) as read_bytes_quants
FROM system.query_log
WHERE databases = ['mv_experiments'] and tables = ['mv_experiments.sales_mv'] and type='QueryFinish'
  and event_time > '2024-08-01 17:42:32'
and query like '%SELECT
        product_id,
        SUM(total_quantity) as total_quantity,
        SUM(total_sales) as total_sales
FROM sales_mv
GROUP BY product_id%'
GROUP BY tables, query, projections
HAVING count(query) > 100

UNION ALL

SELECT
    count(query) as query_cnt,
    query,
    tables,
    projections,
    quantiles(0.25, 0.5, 0.75, 0.95)(query_duration_ms) as duration_quants,
    quantiles(0.25, 0.5, 0.75, 0.95)(memory_usage) as memory_quants,
    quantiles(0.25, 0.5, 0.75, 0.95)(read_bytes) as read_bytes_quants
FROM system.query_log
WHERE databases = ['mv_experiments'] and tables = ['mv_experiments.sales'] and type='QueryFinish'
  and event_time > '2024-08-01 17:42:32'
and query like '%SELECT
        product_id,
        SUM(quantity) as total_quantity,
        SUM(price) as total_sales
FROM sales
GROUP BY product_id%'
GROUP BY tables, query, projections
FORMAT Vertical;
```

```bash
# Результаты бенчмарка!
+------------------------------------------------------+
|results                                               |
+------------------------------------------------------+
|Row 1:                                                |
|──────                                                |
# Количество сделанны запросов
|query_cnt:         5000                               | 
|query:                                                |
|SELECT                                                |
|        product_id,                                   |
|        SUM(total_quantity) as total_quantity,        |
|        SUM(total_sales) as total_sales               |
|FROM sales_mv                                         |
|GROUP BY product_id                                   |
|                                                      |
| FORMAT Native                                        |
# Тут обращились к материализованному представлению
|tables:            ['mv_experiments.sales_mv']        |
|projections:       []                                 |
# Посчитали квантили (0.25, 0.5, 0.75, 0.95) по
# времении исполнения
|duration_quants:   [3,4,4,6]                          |
# использованное памяти
|memory_quants:     [43170,57436,57540,69973.6]        |
# прочитанных байт
|read_bytes_quants: [1800,1800,1800,1800]              |
|                                                      |
|Row 2:                                                |
|──────                                                |
|query_cnt:         5000                               |
|query:                                                |
|SELECT                                                |
|        product_id,                                   |
|        SUM(quantity) as total_quantity,              |
|        SUM(price) as total_sales                     |
|FROM sales                                            |
|GROUP BY product_id                                   |
|                                                      |
| FORMAT Native                                        |
|tables:            ['mv_experiments.sales']           |
# А вот тут попали в проекцию!
|projections:       ['mv_experiments.sales.sales_proj']|
# Смотрим на квантили в работе с проекцией
|duration_quants:   [4,4,5,10]                         |
|memory_quants:     [49064,58026,58790,85868]          |
|read_bytes_quants: [3240,3240,3240,3240]              |
+------------------------------------------------------+

```

### Вывод
Квантили по выполнению и памяти выглядят лучше при работе с `materialized view`:    


| quantiles(0.25, 0.5, 0.75, 0.95)  | Materialized View  ( sales_mv )                                  | Projections (sales.sales_proj) |
|-----------------------------------|------------------------------------------------------------------|--------------------------------|
| Duration Quantiles                | [3, 4, 4, 6] ( меньше время исполнения ) ✅                       | [4, 4, 5, 10]                  |
| Memory Quantiles                  | [43170,57436,57540,69973.6] ( меньше памяти было использовано )✅ | [49064,58026,58790,85868]      |
| Read Bytes Quantiles              | [1800,1800,1800,1800] ( меньше байт пришлось прочитать ) ✅       | [3240,3240,3240,3240]          |


