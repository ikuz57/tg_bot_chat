# tg_bot_chat
Это бот для telegram, который использует API OpenAI GPT-3.5 turbo для генерации ответов. Он принимает пользовательский ввод и использует его для генерации ответа. Он также отслеживает контекст беседы, сохраняя в беседе последние сообщения. Но из-за ограничения в 4097 токенов, если диалог становится слишком длинным, контекст урезается. Присутствует регистрация, для регистрации необходимо отправить сообщение в фаормате "/reg ваш_никнейм", запрос отправиться администратору и после обработки им вашего запроса вы сможете полльзоваться ботом.

## Установка
1. клонировать
2. установить и активировать виртуальное окружение, находясь в папке с проктом
   - py -m venv venv
   - source venv/scripts/activate
3. установить зависимости из requirmenets.txt
    pip install -r requiremnets.txt
4. Создайте и заполните .env, по примеру .example.env
5. Запустите run.py

## Команды
1. "/ai ваш_запрос" - все запросы к боту идут после /ai
2. "/ai_clear" - очистить историю диалогов. Бот иногда застревает на одной теме.
3. "/reg ваш_никнейм" - зарегестрироваться
3. "/add_user никнейм" - разрешить пользователю использовать бота(для админа)
3. "/del_user никнейм" - запретить пользователю использовать бота(для админа)
3. "/help" - помощь
