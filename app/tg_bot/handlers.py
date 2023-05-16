import logging
import io
from aiogram import filters, types, F
import openai
from pydub import AudioSegment

from ..chatgpt_ai.gpt import chatgpt_response
from .bot import bot, dp

context_dict = {}

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
        "серверами OpenAI, для отправки вопроса поставьте /ai перед сообщением.",
        # reply_markup=keyboard,
    )
    logging.info(f"start chat with chat_id = {message.chat.id}")


@dp.channel_post(filters.Command(commands=["help"]))
@dp.message(filters.Command(commands=["help"]))
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
    voice_ogg = io.BytesIO()
    await bot.download_file(voice_file_info.file_path, voice_ogg)
    voice_mp3_path = f"voice_files/voice-{voice.file_unique_id}.mp3"
    AudioSegment.from_file(voice_ogg, format="oga").export(
	    voice_mp3_path, format="mp3"
	)
    return voice_mp3_path


@dp.channel_post(filters.Command(commands=["ai"]))
@dp.message(F.content_type == "voice")
@dp.message(filters.Command(commands=["ai"]))
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
        context_dict[message.chat.id] = [data_to_send,]
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
            "Достигнут предел запросов в минуту(3 сообщения).\nПопробуйте еще раз чуть позже."
        )
    except openai.error.InvalidRequestError:
        await message.answer(
            "Я сломался, почистите историю сообщений."
        )
    finally:
        logging.info(context_dict)


@dp.channel_post(filters.Command(commands=["ai_clear"]))
@dp.message(filters.Command(commands=["ai_clear"]))
async def cmd_ai_clear(message: types.Message):
    context_dict[message.chat.id].clear()
    await message.answer('Почистили')
