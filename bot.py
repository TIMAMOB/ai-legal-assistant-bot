from google import genai
import asyncio
import os
import PyPDF2
from docx import Document
from dotenv import load_dotenv

from aiogram import Bot,Dispatcher,types, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.enums import ParseMode

load_dotenv()

TOKEN = os.getenv("TOKEN")
API_TOKEN = os.getenv("API_TOKEN")

# 1. Настройка клиента
client = genai.Client(api_key=API_TOKEN)
bot = Bot(token=TOKEN)
dp = Dispatcher()

def consultant(text):
    prompt_one = f"""
    Ты профессиональный юрист по гражданскому и договорному праву.
    
    Общайся с клиентом простым и понятным языком.
    Если вазможно, как можно короче отвечай клиентам.
    Не используй сложные юридические термины без объяснения.
    Если не хватает информации — задавай уточняющие вопросы.
    Давай практические советы, а не теорию.
    Будь спокойным, профессиональным и уверенным.

    Текст: {text}
    """

    # 2. Новый способ вызова модели
    response = client.models.generate_content(
        model="gemini-2.5-flash",  # В 2026 используем актуальную версию
        contents=prompt_one
    )

    return response.text

def analyze_contract(text):
    prompt_two = f"""
    Ты — профессиональный юрист.
    Проанализируй текст договора.
    
    Выведи:
    1. 3 главных риска
    2. Краткую суть (до 5 предложений)
    3. 3 рекомендации
    
    Отвечай кратко и по делу.
    Не более 1500 слов
    
    Текст: {text}
    """

    # 2. Новый способ вызова модели
    response = client.models.generate_content(
        model="gemini-2.5-flash",  # В 2026 используем актуальную версию
        contents=prompt_two
    )

    return response.text


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Здраствуйте!. Я помощьник бот юрист')

@dp.message(F.document)
async def handle_ai_request(message: types.Message):
    file_name = message.document.file_name.lower()
    await message.answer('Анализ по новому стандарту...')

    if not file_name.endswith((".pdf", ".docx")):
        await message.answer("Поддерживаются только PDF или DOCX файлы")
        return

    await message.answer("Документ получен. Анализирую...")

    file = await bot.get_file(message.document.file_id)
    file_path = file.file_path

    import tempfile

    # Сохраняем временный файл
    downloaded_bytes = await bot.download_file(file_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_name) as tmp:
        tmp.write(downloaded_bytes.read())
        tmp_path = tmp.name

    # Читаем текст
    text = ""
    if file_name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(tmp_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"

    elif file_name.endswith(".docx"):
        doc = Document(tmp_path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    if not text.strip():
        await message.answer('Не удалось извлечь текст из документа')
        return

    # Отправляем в GPT
    answer = analyze_contract(text)
    await message.answer(answer)

@dp.message()
async def chat_handler(message: Message):
    answer = consultant(message.text)
    await message.answer(answer)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())