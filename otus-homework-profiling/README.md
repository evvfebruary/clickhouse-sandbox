# Профилирование запросов

### Преподготовка таблицы
```sql
create database profiling;
use profiling;

-- Логируем запросы и добавляем трейсы
set log_queries = 1;
set send_logs_level='trace';

-- Создаем отдельную табличку для экспериментов с ключом date
CREATE TABLE profiling.table_with_pk(
    id Int32,
    date DATE,
    value Int32
) ENGINE MergeTree()
primary key date; 

-- Наполняем ее рандомными данными
INSERT INTO profiling.table_with_pk
SELECT
    number AS id,
    toDate('2024-01-01') + INTERVAL rand() % 365 DAY AS date,
    rand() % 1000 AS value
FROM numbers(50000);
```

### Выполнить запрос с WHERE не использующим ПК.
```sql
-- Берем запрос мимо нашего ключа, но все равно пытаемся отфильтровать
SELECT id, date, value FROM profiling.table_with_pk WHERE value > 100 FORMAT NULL;;
```

```shell
<Debug> executeQuery: (from 127.0.0.1:53976) SELECT id, date, value FROM profiling.table_with_pk WHERE value > 100 FORMAT NULL;; (stage: Complete)
<Trace> Planner: Query to stage Complete
<Trace> Planner: Query from stage FetchColumns to stage Complete
<Trace> QueryPlanOptimizePrewhere: The min valid primary key position for moving to the tail of PREWHERE is -1
<Debug> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Key condition: unknown
# Попытались что-то отфильтровать по ключу, ничего не получилось и в итоге прочитали все парты и гранулы
<Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Filtering marks by primary and secondary keys
<Debug> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Selected 4/4 parts by partition key, 4 parts by primary key, 9/9 marks by primary key, 9 marks to read from 4 ranges
<Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Spreading mark ranges among streams (default reading)
<Debug> MergeTreeReadPool: min_marks_for_concurrent_read=24
<Debug> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Reading approx. 60200 rows with 4 streams
<Trace> MergeTreeSelectProcessor: PREWHERE condition was split into 1 steps: "greater(__table1.value, 100_UInt8)"
<Trace> MergeTreeSelectProcessor: PREWHERE condition was split into 1 steps: "greater(__table1.value, 100_UInt8)"
<Trace> MergeTreeSelectProcessor: PREWHERE condition was split into 1 steps: "greater(__table1.value, 100_UInt8)"
<Trace> MergeTreeSelectProcessor: PREWHERE condition was split into 1 steps: "greater(__table1.value, 100_UInt8)"
<Debug> executeQuery: Read 60200 rows, 587.89 KiB in 0.039044 sec., 1541850.220264317 rows/sec., 14.70 MiB/sec.
<Debug> MemoryTracker: Peak memory usage (for query): 574.98 KiB.
<Debug> TCPHandler: Processed in 0.042138292 sec.
```

### Выполнить запрос с WHERE использующим ПК. 
```sql
SELECT id, date, value FROM profiling.table_with_pk WHERE date > '2024-08-20' FORMAT NULL;
```

```shell
<Debug> executeQuery: (from 127.0.0.1:53976) SELECT id, date, value FROM profiling.table_with_pk WHERE date > '2024-08-20' FORMAT NULL;; (stage: Complete)
<Trace> Planner: Query to stage Complete
<Trace> Planner: Query from stage FetchColumns to stage Complete
<Trace> QueryPlanOptimizePrewhere: The min valid primary key position for moving to the tail of PREWHERE is 0
# По первых попали в PrimaryKey
<Debug> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Key condition: (column 0 in [19956, +Inf))
<Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Filtering marks by primary and secondary keys
# Бинарным поиском по нему прошерстили ( видимо прямо по primary.idx )
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Running binary search on index range for part all_3_3_0 (2 marks)
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Running binary search on index range for part all_4_4_0 (7 marks)
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Running binary search on index range for part all_1_1_0 (2 marks)
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Running binary search on index range for part all_2_2_0 (2 marks)
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Found (LEFT) boundary mark: 3
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Found (LEFT) boundary mark: 0
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Found (RIGHT) boundary mark: 7
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Found (LEFT) boundary mark: 0
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Found (LEFT) boundary mark: 0
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Found continuous range in 5 steps
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Found (RIGHT) boundary mark: 2
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Found (RIGHT) boundary mark: 2
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Found (RIGHT) boundary mark: 2
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Found continuous range in 2 steps
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Found continuous range in 2 steps
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Found continuous range in 2 steps
# В итоге получилось убрать несколько гранул из чтения, получается сэкономили времечко!
<Debug> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Selected 4/4 parts by partition key, 4 parts by primary key, 6/9 marks by primary key, 6 marks to read from 4 ranges
<Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Spreading mark ranges among streams (default reading)
<Debug> MergeTreeReadPool: min_marks_for_concurrent_read=24
<Debug> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Reading approx. 35624 rows with 4 streams
<Trace> MergeTreeSelectProcessor: PREWHERE condition was split into 1 steps: "greater(__table1.date, '2024-08-20'_String)"
<Trace> MergeTreeSelectProcessor: PREWHERE condition was split into 1 steps: "greater(__table1.date, '2024-08-20'_String)"
<Trace> MergeTreeSelectProcessor: PREWHERE condition was split into 1 steps: "greater(__table1.date, '2024-08-20'_String)"
<Trace> MergeTreeSelectProcessor: PREWHERE condition was split into 1 steps: "greater(__table1.date, '2024-08-20'_String)"
<Debug> executeQuery: Read 35624 rows, 347.89 KiB in 0.025831 sec., 1379118.1138941583 rows/sec., 13.15 MiB/sec.
<Debug> MemoryTracker: Peak memory usage (for query): 795.08 KiB.
<Debug> TCPHandler: Processed in 0.028981334 sec.


```


### Сравнить text_log запросов, предоставить строки лога относящиеся к пробегу основного индекса.


```shell
# Для запроса без ключа
# SELECT id, date, value FROM profiling.table_with_pk WHERE value > 100 FORMAT NULL;;
<Debug> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Key condition: unknown
# Попытались что-то отфильтровать по ключу, ничего не получилось и в итоге прочитали все парты и гранулы
<Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Filtering marks by primary and secondary keys
<Debug> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Selected 4/4 parts by partition key, 4 parts by primary key, 9/9 marks by primary key, 9 marks to read from 4 ranges
```

```shell
# Для запроса с ключом
# SELECT id, date, value FROM profiling.table_with_pk WHERE date > '2024-08-20';
# По первых попали в PrimaryKey
<Debug> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Key condition: (column 0 in [19956, +Inf))
<Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Filtering marks by primary and secondary keys
# Бинарным поиском по нему прошерстили ( видимо прямо по primary.idx )
 <Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Running binary search on index range for part all_3_3_0 (2 marks)
...
# В итоге получилось убрать несколько гранул из чтения, получается сэкономили времечко!
<Debug> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Selected 4/4 parts by partition key, 4 parts by primary key, 6/9 marks by primary key, 6 marks to read from 4 ranges
<Trace> profiling.table_with_pk (796d2dbf-8c6c-4997-aac3-cc23401a60e1) (SelectExecutor): Spreading mark ranges among streams (default reading)
<Debug> MergeTreeReadPool: min_marks_for_concurrent_read=24
```

### Показать тот же индекс через EXPLAIN

```sql
-- Запрос для EXPLAIN
EXPLAIN PLAN indexes=1, json = 1, description=1 
SELECT id, date, value FROM profiling.table_with_pk WHERE date > '2024-08-20';
```


```json
// Вывод запроса сверху
[
  {
    "Plan": {
      "Node Type": "Expression",
      "Description": "(Project names + Projection)",
      "Plans": [
        {
          "Node Type": "Expression",
          "Plans": [
            {
              "Node Type": "ReadFromMergeTree",
              "Description": "profiling.table_with_pk",
              "Indexes": [
                {
                  // Действительно PrimaryKey, хотя тут так же может быть значения Partition ,
                  // Skip, MinMax и тп
                  // https://clickhouse.com/docs/ru/sql-reference/statements/explain
                  "Type": "PrimaryKey",  
                  "Keys": ["date"], // Попали в нашу колонку, которая является первичным ключом
                  "Condition": "(date in [19956, +Inf))",
                  "Initial Parts": 4,
                  "Selected Parts": 4,
                  "Initial Granules": 9,
                  "Selected Granules": 6 // Видим, что пробежались не по всем гранулам
                }
              ]
            }
          ]
        }
      ]
    }
  }
]
```


