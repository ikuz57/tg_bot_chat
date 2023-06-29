import asyncio
import os
import logging
import openai
import json

from art import tprint
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, filters, types, F
from pydub import AudioSegment
from ..chatgpt_ai.gpt import chatgpt_response

load_dotenv()

log_format = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
logging.basicConfig(
    level=logging.DEBUG,
    filename="tg_chatgpt.log",
    filemode="w",
    format=log_format
)

bot = Bot(token=os.getenv('TG_BOT_TOKEN'))
dp = Dispatcher()

context_dict = {}


# Проверка наличия файла users.json. Из за его отсутствия падает ошибка.
async def check_exists_file():
    if not os.path.exists('./users.json'):
        with open('./users.json', 'x'):
            pass


# Декоратор для проверки регистрации у пользователя
def check_auth(func):
    async def wrapper(*args):
        logging.info("WRAPPER")
        message = args[0]
        users_id = []
        await check_exists_file()
        try:
            with open('./users.json') as file:
                data = json.load(file)
        except json.decoder.JSONDecodeError:
            data = []
        for user in data:
            if user['active'] is True:
                users_id.append(user['user_id'])
        if message.from_user.id in users_id:
            return await func(*args)
        else:
            return await message.answer(
                "Незарегестрированный пользователь. Введите /reg и имя"
                " пользователя через пробел."
            )
    return wrapper


async def chek_context(message: types.Message):
    token_count = 0
    for msg in context_dict[message.chat.id]:
        token_count += len(msg['content'].split(' '))
    if (token_count*3+500) < 3000:
        return
    else:
        context_dict[message.chat.id] = context_dict[message.chat.id][1:]
        await chek_context(message)


@dp.message(filters.Command(commands=["start"]))
async def cmd_start(message: types.Message):
    await message.answer(
        "Вас приветствует прослойка между вами и\n"
        "серверами OpenAI.\n"
        "Для использования бота необходимо зарегестрироваться\n"
        "используя команду /reg 'username'.\n"
        "Для отправки вопроса поставьте /ai перед сообщением."
    )
    logging.info(f"start chat with chat_id = {message.chat.id}")


@dp.message(filters.Command(commands=["reg"]))
async def registration(message: types.Message, command: filters.CommandObject):
    """
    При регистрации мы добавляем пользовател в users.json,
    что бы не добавлять дубли проверяем username и user_id,
    в дальнейшем пользователя надо будет только активировать.
    """
    if command.args:
        usernames = set()
        users_id = set()
        username = command.args.split()[0]
        await check_exists_file()
        try:
            with open('./users.json') as file:
                data = json.load(file)
        except json.decoder.JSONDecodeError:
            data = []
        for user in data:
            usernames.add(user['username'])
            users_id.add(user['user_id'])
        if username in usernames:
            await message.answer('Такой username уже занят!')
        elif message.from_user.id in users_id:
            await message.answer('Вы уже отправляли запрос!')
        else:
            user = {
                'user_id': message.from_user.id,
                'username': username,
                'active': False
            }
            data.append(user)
            with open('./users.json', 'w+') as file:
                json.dump(data, file)
            await message.answer('Запрос отправлен!')
            await bot.send_message(
                os.getenv('BOT_ADMIN_USER_ID'),
                text=f"Запрос доступа - {command.args}"
            )
    else:
        await message.answer("Укажите username")
    logging.info(
        f"запрос на регистрацию user_id={message.from_user.id} "
        f"username={command.args.split()[0]}"
    )


@dp.message(filters.Command(commands=["add_user"]))
async def add_user(message: types.Message, command: filters.CommandObject):
    """
    Добавляем пользователя - пользователь уже в users.josn должен
    быть после регистрации, теперь мы его активируем.
    """
    if message.from_user.id == int(os.getenv('BOT_ADMIN_USER_ID')):
        notfound_flag = True
        user_to_add = command.args.split()[0]
        await check_exists_file()
        try:
            with open('./users.json') as file:
                data = json.load(file)
        except json.decoder.JSONDecodeError:
            data = []
        for user in data:
            if user['username'] == user_to_add:
                user['active'] = True
                notfound_flag = False
                await bot.send_message(
                    user['user_id'],
                    text="Вам предоставлен доступ!"
                )
        if notfound_flag:
            await message.answer('Такого пользователя не существует')
            logging.debug('wow wow')
        else:
            with open('./users.json', 'w+') as file:
                json.dump(data, file)
            await message.answer('Пользователь добавлен!')
    else:
        await message.answer('У вас нет доступа!')


@dp.message(filters.Command(commands=["del_user"]))
async def del_user(message: types.Message, command: filters.CommandObject):
    """
    Удаляем пользователя путем удаления обьекта из user.json.
    """
    if message.from_user.id == int(os.getenv('BOT_ADMIN_USER_ID')):
        del_user = None
        user_to_del = command.args.split()[0]
        await check_exists_file()
        try:
            with open('./users.json') as file:
                data = json.load(file)
        except json.decoder.JSONDecodeError:
            data = []
        for user in data:
            if user['username'] == user_to_del:
                del_user = user
                await bot.send_message(
                    user['user_id'],
                    text="Вы заблокированы!"
                )
        if del_user is not None:
            data.remove(del_user)
            with open('./users.json', 'w+') as file:
                json.dump(data, file)
            await message.answer('Пользователь удален!')
        else:
            await message.answer('Пользователь не найден!')
    else:
        await message.answer('У вас нет доступа!')


@dp.channel_post(filters.Command(commands=["help"]))
@dp.message(filters.Command(commands=["help"]))
@check_auth
async def cmd_help(message: types.Message):
    await message.answer(
        "Вводите свое сообщение после '/ai '."
    )
    logging.info(f"command /help for chat_id = {message.chat.id}")


async def audio_to_text(file_path: str) -> str:
    """Принимает путь к аудио файлу, возвращает текст файла."""
    with open(file_path, "rb") as audio_file:
        transcript = await openai.Audio.atranscribe(
            "whisper-1", audio_file
        )
    return transcript["text"]


async def save_voice_as_mp3(bot, voice) -> str:
    """Скачивает голосовое сообщение и сохраняет в формате mp3."""
    voice_file_info = await bot.get_file(voice.file_id)
    f_path_voice_ogg = "temp.ogg"
    await bot.download_file(voice_file_info.file_path, f_path_voice_ogg)
    voice_mp3_path = "voice.mp3"

    ogg = AudioSegment.from_ogg(f_path_voice_ogg)
    ogg.export(voice_mp3_path, format="mp3")
    return voice_mp3_path


@dp.channel_post(filters.Command(commands=["ai"]))
@dp.message(F.content_type == "voice")
@dp.message(filters.Command(commands=["ai"]))
@check_auth
async def cmd_ai(message: types.Message):
    if message.content_type == types.ContentType.VOICE:
        audio_file = await save_voice_as_mp3(bot, message.voice)
        msg = await audio_to_text(audio_file)
        if msg:
            await message.answer(f'Ваш запрос:\n{msg}')
    else:
        msg = message.text
    data_to_send = {
        'role': 'user',
        'content': msg
    }
    if message.chat.id not in context_dict:
        context_dict[message.chat.id] = [data_to_send, ]
    else:
        context_dict[message.chat.id].append(data_to_send)
    try:
        await chek_context(message)
        bot_response = chatgpt_response(msg=context_dict[message.chat.id])
        await message.answer(bot_response['choices'][0]['message']['content'])
        data_to_context = {
            'role': 'assistant',
            'content': bot_response['choices'][0]['message']['content']
        }
        context_dict[message.chat.id].append(data_to_context)
    except openai.error.ServiceUnavailableError:
        await message.answer(
            "Error on the server or it's not available, come on "
            "let's try again?"
        )
    except openai.error.RateLimitError:
        await message.answer(
            "Достигнут предел запросов в минуту(3 сообщения).\n"
            "Попробуйте еще раз чуть позже."
        )
    except openai.error.InvalidRequestError:
        await message.answer(
            "Я сломался, почистите историю сообщений."
        )
    finally:
        logging.info(context_dict)


@dp.channel_post(filters.Command(commands=["ai_clear"]))
@dp.message(filters.Command(commands=["ai_clear"]))
@check_auth
async def cmd_ai_clear(message: types.Message):
    context_dict[message.chat.id].clear()
    await message.answer('Почистили')


async def bot_in_loop() -> None:
    tprint("the bot is launched")
    logging.info("START_BOT")
    await dp.start_polling(bot)


def run_bot():
    asyncio.run(bot_in_loop())


if __name__ == "__main__":
    run_bot()
