1) В качестве менеджера пакетов используется Poetry:

2) Миграции:
> aerich init -s . -t settings.DATABASE_CONFIG --location src/database/migrations
> aerich init-db

3) В переменных среды должно быть:

BOT_TOKEN=ТОКЕНиз@BotFather
OWNER_IDS=12345,678910
DB_URL=postgres://USERNAME:PASSWD@HOST:PORT/DB_NAME

4) 
Нужно сделать:

1) вход и создание игр из бота
2) навигация в боте
3) throttling middleware и фильтр существования юзера для игр в чате
4) удаление игр


Добавление метода пополнения: 

в src/misc/enums класс DepositMethod добавить метод.
в src/keyboards/user функцию 
в src/handlers/user/private/profile функцию handle_show_deposit_method_callbacks() 
добавить обработчик для нажатия на метода
