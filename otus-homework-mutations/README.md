# Мутации

### 1. Создание таблицы:
#### Создайте таблицу user_activity с полями:
- user_id (UInt32) — идентификатор пользователя    
- activity_type (String) — тип активности (например, 'login', 'logout', 'purchase')    
- activity_date (DateTime) — дата и время активности 
- Используйте MergeTree как движок таблицы и настройте партиционирование по дате активности (activity_date).     
```sql
-- Создание таблицы
CREATE TABLE mutations.user_activity (
    user_id UInt32,
    activity_type String,
    activity_date DATETIME
) ENGINE MergeTree()
PARTITION BY toYYYYMM(activity_date)
PRIMARY KEY activity_type;
```
### 2. Заполнение таблицы:
- Вставьте несколько записей в таблицу user_activity. Используйте различные user_id, activity_type и activity_date.


```sql
-- Заполняем табличку ( над этим инсертом я сидел больше чем над всем остальным заданием )ъ
INSERT INTO mutations.user_activity
SELECT abs(rand32() % 10) + 1 as user_id,
       arrayJoin(arrayShuffle(['activity1', 'activity2', 'activity3'])) as activity_type,
       toDateTime('2024-01-01 00:00:00')
    + INTERVAL (rand() % 12) MONTH
    + INTERVAL (rand() % 28) DAY
    + INTERVAL (rand() % 24) HOUR
    + INTERVAL (rand() % 60) MINUTE
    + INTERVAL (rand() % 60) SECOND AS activity_date
FROM numbers(10000);
```

### 3. Выполнение мутаций:
- Выполните мутацию для изменения типа активности у пользователя(-ей)
```sql
-- Меняем тип активности у пользователя
ALTER TABLE mutations.user_activity
UPDATE activity_type = 'updated-activity' WHERE user_id = 5;
```

### 4. Проверка результатов:
- Напишите запрос для проверки изменений в таблице `user_activity`. Убедитесь, что тип активности у пользователей изменился. Приложите логи отслеживания мутаций в системной таблице.
```sql
-- Меняем тип активности у пользователя
ALTER TABLE mutations.user_activity
UPDATE activity_type = 'updated-activity' WHERE user_id = 5;


-- Проверим глазками
SELECT * FROM mutations.user_activity WHERE user_id = 5 LIMIT 2 FORMAT Vertical;
+----------------------------------+
|results                           |
+----------------------------------+
|Row 1:                            |
|──────                            |
|user_id:       5                  |
|activity_type: updated-activity   |
|activity_date: 2024-07-11 18:54:54|
|                                  |
|Row 2:                            |
|──────                            |
|user_id:       5                  |
|activity_type: updated-activity   |
|activity_date: 2024-07-11 18:54:54|
+----------------------------------+



-- Смотрим на происходившие мутации
SELECT * FROM system.mutations WHERE database='mutations' FORMAT Vertical;
+---------------------------------------------------------------------------------------+
|results                                                                                |
+---------------------------------------------------------------------------------------+
|Row 1:                                                                                 |
|──────                                                                                 |
|database:                   mutations                                                  |
|table:                      user_activity                                              |
|mutation_id:                mutation_13.txt                                            |
|command:                    UPDATE activity_type = 'updated-activity' WHERE user_id = 5|
|create_time:                2024-07-30 19:18:21                                        |
|block_numbers.partition_id: ['']                                                       |
|block_numbers.number:       [13]                                                       |
|parts_to_do_names:          []                                                         |
|parts_to_do:                0                                                          |
|is_done:                    1                                                          |
|is_killed:                  0                                                          |
|latest_failed_part:                                                                    |
|latest_fail_time:           1970-01-01 00:00:00                                        |
|latest_fail_reason:                                                                    |
+---------------------------------------------------------------------------------------+
```


### Манипуляции с партициями:
- Удалите партицию за определённый месяц.
```sql
-- Проверим, что данные за 202407 месяц действительно есть 
SELECT COUNT(1) as cnt FROM mutations.user_activity WHERE toYYYYMM(activity_date) = '202407' FORMAT Vertical
+---------+
|results  |
+---------+
|Row 1:   |
|──────   |
|cnt: 2508|
+---------+

-- Удалим партицию за этот месяц
ALTER TABLE mutations.user_activity
DROP PARTITION 202407;
```
     
### Проверка состояния таблицы:
- Проверьте текущее состояние таблицы после удаления партиции. Убедитесь, что данные за указанный месяц были удалены.     
```sql
-- Проверим есть ли записи за этот месяц в таблице
SELECT COUNT(1) as cnt FROM mutations.user_activity WHERE toYYYYMM(activity_date) = '202407' FORMAT Vertical
+-------+
|results|
+-------+
|Row 1: |
|────── |
|cnt: 0 |
+-------+
          
-- Так же посмотрим в системную табличку
SELECT partition, active,marks, rows, remove_time, last_removal_attempt_time
FROM system.parts WHERE database ='mutations' AND partition = '202407' FORMAT Vertical;

+----------------------------------------------+
|results                                       |
+----------------------------------------------+
|Row 1:                                        |
|──────                                        |
|partition:                 202407             |
|active:                    0                  | 
|marks:                     0                  |
|rows:                      0                  |
|remove_time:               2024-07-30 19:31:20|
|last_removal_attempt_time: 2024-07-30 19:33:03|
+----------------------------------------------+
```



### Дополнительные задания (по желанию):


#### Исследуйте, как работают другие типы мутаций.

```sql
-- Замораживает партицию за январь 2024 года
ALTER TABLE user_activity
FREEZE PARTITION 202401;

-- Отсоединяет партицию за февраль 2024 года
ALTER TABLE user_activity
DETACH PARTITION 202402;

-- Добавляем новую колонку
ALTER TABLE user_activity
ADD COLUMN user_name Nullable(String) AFTER user_id;

-- Меняем имя колонке
ALTER TABLE user_activity
RENAME COLUMN user_name TO username;
```

Можем увидить, что в таблице `system.mutations` отобразились только неопсредственно манипуляции с данными, тогда как добавление колонки, `freeze` и `detach` партишнов в табличке не появились.
```sql
SELECT * FROM system.mutations WHERE table = 'user_activity'
+---------------------------------------------------------------------------------------+
|results                                                                                |
+---------------------------------------------------------------------------------------+
|Row 1:                                                                                 |
|──────                                                                                 |
|database:                   mutations                                                  |
|table:                      user_activity                                              |
|mutation_id:                mutation_13.txt                                            |
|command:                    UPDATE activity_type = 'updated-activity' WHERE user_id = 5|
|create_time:                2024-07-30 19:18:21                                        |
|block_numbers.partition_id: ['']                                                       |
|block_numbers.number:       [13]                                                       |
|parts_to_do_names:          []                                                         |
|parts_to_do:                0                                                          |
|is_done:                    1                                                          |
|is_killed:                  0                                                          |
|latest_failed_part:                                                                    |
|latest_fail_time:           1970-01-01 00:00:00                                        |
|latest_fail_reason:                                                                    |
|                                                                                       |
|Row 2:                                                                                 |
|──────                                                                                 |
|database:                   mutations                                                  |
|table:                      user_activity                                              |
|mutation_id:                mutation_14.txt                                            |
|command:                    RENAME COLUMN user_name TO username                        |
|create_time:                2024-07-30 19:40:48                                        |
|block_numbers.partition_id: ['']                                                       |
|block_numbers.number:       [14]                                                       |
|parts_to_do_names:          []                                                         |
|parts_to_do:                0                                                          |
|is_done:                    1                                                          |
|is_killed:                  0                                                          |
|latest_failed_part:                                                                    |
|latest_fail_time:           1970-01-01 00:00:00                                        |
|latest_fail_reason:                                                                    |
+---------------------------------------------------------------------------------------+

```


### Попробуйте создать новую партицию и вставить в неё данные.
Вообще при вставке данных партиция создается сама ( или возможно имелось ввиду `ATTACH PARTITION`, что не могу назвать ее созданием все таки ).    

```sql
-- Вставляем данные
INSERT INTO mutations.user_activity
VALUES (1, 'evv', 'inserted', toDateTime('2099-05-05 16:40:40'));

-- Любуемся на новую партиции
SELECT * FROM system.parts WHERE table = 'user_activity' AND partition = '209905' FORMAT Vertical;
+-------------------------------------------------------------------------------------------------------------------------+
|results                                                                                                                  |
+-------------------------------------------------------------------------------------------------------------------------+
|Row 1:                                                                                                                   |
|──────                                                                                                                   |
|partition:                             209905                                                                            |
|name:                                  209905_19_19_0                                                                    |
|uuid:                                  00000000-0000-0000-0000-000000000000                                              |
|part_type:                             Compact                                                                           |
|active:                                1                                                                                 |
|marks:                                 2                                                                                 |
|rows:                                  1                                                                                 |
 ......
+-------------------------------------------------------------------------------------------------------------------------+

```


### Изучите возможность использования TTL (Time to Live) для автоматического удаления старых партиций.
```sql
-- Изначально в таблице
SELECT COUNT(1) FROM user_activity;
+--------+
|COUNT(1)|
+--------+
|25061   |
+--------+

-- Добавим TTL
ALTER TABLE user_activity
MODIFY TTL activity_date + INTERVAL 1 MONTH;

-- Проверим теперь
SELECT COUNT(1) FROM user_activity;
+--------+
|COUNT(1)|
+--------+
|12544   |
+--------+



-- Проверим также, что мы увидим TTL в табличке с мутациями
SELECT * FROM system.mutations WHERE table = 'user_activity' and command LIKE '%TTL%' FORMAT Vertical;
+-----------------------------------------------+
|results                                        |
+-----------------------------------------------+
|Row 1:                                         |
|──────                                         |
|database:                   mutations          |
|table:                      user_activity      |
|mutation_id:                mutation_20.txt    |
|command:                    MATERIALIZE TTL    |
|create_time:                2024-07-30 19:52:47|
|block_numbers.partition_id: ['']               |
|block_numbers.number:       [20]               |
|parts_to_do_names:          []                 |
|parts_to_do:                0                  |
|is_done:                    1                  |
|is_killed:                  0                  |
|latest_failed_part:                            |
|latest_fail_time:           1970-01-01 00:00:00|
|latest_fail_reason:                            |
+-----------------------------------------------+

```