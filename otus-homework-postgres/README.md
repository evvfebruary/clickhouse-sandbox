## Проработать варианты интеграции ClickHouse и PostgreSQL на базовом уровне




### Инициализировать БД PostgreSQL любым способом.

```yaml
  postgres-db:
    image: postgres:latest
    container_name: postgres
    volumes:
      - ./postgres/data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=mydatabase
      - POSTGRES_USER=myuser
      - POSTGRES_PASSWORD=mypassword
```



```sql
-- Создадим синтетическую таблицу
CREATE TABLE synthetic_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    value FLOAT
);

-- Накинем туда не менее синтетических данных
INSERT INTO synthetic_table (name, value) VALUES
('Alice', 10.5),
('Bob', 20.3),
('Charlie', 30.7),
('Diana', 40.2),
('Eve', 50.1);
```

### На стороне ClickHouse с помощью функции postgres запросить данные.


```sql
-- Попробуем еще и вставить данные
INSERT INTO TABLE FUNCTION postgresql('postgres-db:5432',
                                      'mydatabase',
                                      'synthetic_table',
                                      'myuser',
                                      'mypassword') (name, value) 
VALUES ('Name from Ch', 0.01);

-- Посмотрим, какие данные сможем получить
SELECT * FROM postgresql('postgres-db:5432',
                                      'mydatabase',
                                      'synthetic_table',
                                      'myuser',
                                      'mypassword');
```
![img.png](img.png)


### На стороне ClickHouse создать таблицу для интеграции с движком Postgres для связи с таблицей из PostgreSQL
```sql
CREATE TABLE postgres_synthetic_table
(
    id UInt32,
    name String,
    value Float32
)
ENGINE = PostgreSQL('postgres:5432', 'mydatabase', 'synthetic_table', 'myuser', 'mypassword');
```

![img_1.png](img_1.png)

### На стороне ClickHouse создать БД для интеграции с движком Postgres для связи с БД из PostgreSQL

```sql
CREATE DATABASE ch_postgred_db ENGINE = PostgreSQL('postgres:5432', 'mydatabase', 'myuser', 'mypassword');
```

Создадим новую таблицу на стороне Postgres
```sql
CREATE TABLE synthetic_table_2 (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    value FLOAT
);
```

Проверим, появилось ли на стороне клика
```sql
USE ch_postgred_db;
SHOW TABLES;
```

![img_2.png](img_2.png)

```sql
-- Вот что кстати покажет show create
SHOW CREATE TABLE synthetic_table_2;

-- CREATE TABLE ch_postgred_db.synthetic_table_2
-- (
--     `id` Int32,
--     `name` Nullable(String),
--     `value` Nullable(Float64)
-- )
-- ENGINE = PostgreSQL('postgres:5432', 'mydatabase', 'synthetic_table_2', 'myuser', '[HIDDEN]')
```


