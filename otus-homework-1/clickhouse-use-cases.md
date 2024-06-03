## Домашнее задание #1
### Примеры использования


### Badooo и их применение clickhouse
Используется для сбора кликстрима с приложения, сервисных метрик.     
В дальнейшем происходит анализ этих данных и строятся статистики / метрики.     
**Источник**: https://github.com/ClickHouse/clickhouse-presentations/blob/master/meetup15/lightning/badoo.pdf

### WeChat и дата лужа
Неожиданно WeChat делает Data Lake на Clickhouse в связке с Iceberg.

**Источник:** https://github.com/ClickHouse/clickhouse-presentations/blob/master/meetup95/When-ClickHouse-Meets-Iceberg.pdf

### Ребята из Gojek варят fraud detection
Плотная интеграция с брокером сообщений, большое количество логов в Clickhouse и последующий fraud detection.
Признаются, что пока работают с батчами, но стремятся к аналитике в real time.

**Источник**: https://www.gojek.io/blog/detecting-fraudsters-in-near-real-time-with-clickhouse

----

### К каким классам систем относится ClickHouse?
Clickhouse можно охарактеризовать как **column-based OLAP Database Management System**.

----------
#### Какую проблему вы бы решили используя ClickHouse, а какую бы не стали?
**Подходящая задача:**
- Агрегация данных с целью построение финансовых отчетов за квартал / год.   

**Неподходящая задача**
- Использование Clickhouse в качестве базы данных для бэкенда мобильного приложения банка.
------
#### Где можно получить помощь по ClickHouse и куда сообщать о багах?
- https://clickhouse.com/docs, документация
- https://t.me/clickhouse_ru, большое коммьюнити в телеграмме, куда можно обратиться с вопросом
- https://github.com/ClickHouse/ClickHouse, можно создать issue, если вдруг будет повод