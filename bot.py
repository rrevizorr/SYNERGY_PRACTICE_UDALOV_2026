import json
import re
import random
import os

from rapidfuzz import fuzz, process  # pip install rapidfuzz
# Для Telegram-бота:
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


# ---------- Загрузка интентов ----------

with open('intents.json', 'r', encoding='utf-8') as f:
    INTENTS = json.load(f)['intents']

pattern_map = []
for intent in INTENTS:
    for p in intent.get('patterns', []):
        pattern_map.append((intent['tag'], p))


# ---------- Обработка текста ----------

def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^а-яa-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def predict_intent(text: str, threshold: int = 70) -> str:
    text = preprocess(text)

    # Прямое вхождение ключевой фразы
    for tag, patt in pattern_map:
        if patt in text:
            return tag

    # Нечеткое сопоставление
    choices = [p for (_, p) in pattern_map]
    if not choices:
        return 'fallback'

    match, score, idx = process.extractOne(text, choices, scorer=fuzz.token_sort_ratio)
    if score >= threshold:
        matched_tag = pattern_map[idx][0]
        return matched_tag

    return 'fallback'


def get_response(tag: str) -> str:
    for intent in INTENTS:
        if intent['tag'] == tag:
            return random.choice(intent['responses'])
    # на случай отсутствия тега
    for intent in INTENTS:
        if intent['tag'] == 'fallback':
            return random.choice(intent['responses'])
    return "Извините, я не понял запрос."


# ---------- Консольный режим ----------

def console_chat():
    print("Чат-бот Университета «Синергия». Введите 'exit' или 'выход' для завершения.")
    while True:
        user_text = input("Вы: ")
        if user_text.strip().lower() in ("exit", "выход"):
            print("Бот: До свидания!")
            break
        tag = predict_intent(user_text)
        resp = get_response(tag)
        print("Бот:", resp)


# ---------- Telegram-бот ----------

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Здравствуйте! Я чат-бот Университета «Синергия».\n"
        "Задайте вопрос о поступлении, контактах, факультете информационных технологий, практике или расписании."
    )


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Я могу отвечать на вопросы об Университете «Синергия»:\n"
        "- поступление и приёмная комиссия\n"
        "- контакты университета\n"
        "- факультет информационных технологий\n"
        "- практика и расписание\n"
        "Просто напишите ваш вопрос."
    )


def handle_message(update: Update, context: CallbackContext):
    user_text = update.message.text or ""
    tag = predict_intent(user_text)
    resp = get_response(tag)
    update.message.reply_text(resp)


def run_telegram_bot():
    token = os.getenv("TG_TOKEN")
    if not token:
        print("Переменная окружения TG_TOKEN не задана. Запускаю консольный режим.")
        console_chat()
        return

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("Telegram-бот запущен. Нажмите Ctrl+C для остановки.")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    # Если хотите только консольный вариант — вызовите console_chat().
    # Для автоматического выбора (по наличию TG_TOKEN) используем:
    run_telegram_bot()