### Домашнее задание по RBAC
#### RBAC

**1) Создать пользователя `jhon` с паролем `qwery`**
```sql
-- Создаем пользователя Jhon, в этот раз просто plaintext
CREATE USER jhon IDENTIFIED WITH plaintext_password BY 'qwery';
```

**2) Создать роль `devs`**
```sql
-- Создаем роль devs
CREATE ROLE devs;
```

**3) Выдать роли `devs` права на `SELECT` на любую таблицу**
```sql
-- Дадим права на чтение на любую таблицу в базе данных default
GRANT SELECT ON *.* TO devs WITH GRANT OPTION;
```

**4) Выдать роль `devs` пользователю `jhon`**
```sql
-- Присвоим роль пользователю jhon, делаем дефолтной при каждом логине
GRANT devs to jhon;
SET DEFAULT ROLE devs TO jhon;
```


**5) предоставить результаты `SELECT` из system-таблиц соответсвующих созданным сущностям**

```sql
-- Проверим, как там наш новый "jhon", ох уж эта опечатка канеш в имени, приходится жмурится.
SELECT * FROM system.users WHERE name = 'jhon' FORMAT Vertical
```
![img.png](screenshots/img.png)


```sql
-- Посмотрим на созданную роль
SELECT * FROM system.roles WHERE name = 'devs' FORMAT Vertical
```
![img_1.png](screenshots/img_1.png)

```sql
-- Проверим какие гранты есть у роли
SELECT * FROM system.grants WHERE role_name = 'devs' FORMAT Vertical;
```
![img_2.png](screenshots/img_2.png)


**P.S, проверил подключившися как `jhon`, `SELECT` отработал отлично:**
```sql
SELECT currentUser() as whoami;
```
![img_3.png](screenshots/img_3.png)

```sql
-- Делаем селект от имени jhon
SELECT * FROM default.users_expenses FORMAT Vertical;
```

![img_4.png](screenshots/img_4.png)

```sql
-- Пробуем вставить значения
INSERT INTO default.users_expenses VALUES(1243, 'sfa', 199);
```
![img_5.png](screenshots/img_5.png)