import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ConversationHandler, CallbackContext, MessageHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os


# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


# Выключаем логирование
logging.disable(logging.CRITICAL)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токена из переменных окружения
bot_token = os.getenv('BOT_TOKEN')

# Определение состояний для ConversationHandler
ASK_NAME, QUESTION1, QUESTION2, GET_DATA, RESULT = range(5)

# Вопросы и варианты ответов
questions = [
    "<b>Для начала</b> выберите свой ЗНАК ЗОДИАКА",
    "Здесь будут предоставлены базовые рекомендации.\n✨✨✨\n<i>Для индивидуального разбора укажите ваши <b>дату, время и город рождения</b>.</i>"
]
options = [
    ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"],
    ["Отправить данные", "Нет, спасибо"]
]

# Описание результатов на основе ответов
results = {
    "Овен": {
        "description": "<i><u>ОВЕН</u></i>\n\nПора вспомнить о ваших лидерских качествах. Выходите из тени, выделяйтесь, выступайте инициатором и берите на себя ответственность за реализацию проектов. Лучше действовать единолично. Говорите прямо о своих мыслях и идеях. Введите системные физические нагрузки, таким образом, вы активируете вашу жизненную энергию.",
        "image": os.getenv('OVEN')
    },
    "Телец": {
        "description": "<i><u>ТЕЛЕЦ</u></i>\n\nВспомните о том, что вас заземляет и приносит стабильность. Это может быть как накопление материальных благ, красивых предметов искусства, так и выращивание цветов в своё удовольствие. Неторопливо погрузитесь в ваш личный гедонизм, это принесёт вам заряд энергии.",
        "image": os.getenv('TELEC')
    },
    "Близнецы": {
        "description": "<i><u>БЛИЗНЕЦЫ</u></i>\n\nВозобновите полезные коммуникации и получение свежей информации, в том числе, благодаря обучению. Смените обстановку, чтобы зарядиться новыми впечатлениями. Знакомьтесь и общайтесь, делитесь своими знаниями и энергией через разговор, чтобы активировать её и получить еще больше взамен.",
        "image": os.getenv('BLIZNECU')
    },
    "Рак": {
        "description": "<i><u>РАК</u></i>\n\nСоздайте уют вокруг себя, чтобы эмоционально расслабиться и получить заряд энергии. Комфортно обустройте ваше жилье, позаботьтесь о детях и семье, возобновите семейные традиции, приготовьте любимое блюдо и пригласите близких на обед, вспомните о ваших ценностях рода. Активируйте вашу энергию через любимое творчество.",
        "image": os.getenv('RAK')
    },
    "Лев": {
        "description": "<i><u>ЛЕВ</u></i>\n\nНеобходимо выбрать дело или проект, в котором вы с уверенностью достигните успеха, выступите в роли настоящего предводителя или командира и приобретете долгожданный авторитет. Благодаря этому вы восполнитесь энергией, даже если сперва всё покажется незначительным. Не забывайте, демонстрировать свои достоинства: щедрость и благородство. Не пренебрегайте атрибутами роскоши. Всё это придаст вам дополнительный заряд и активизируют жизненные силы.",
        "image": os.getenv('LEV')
    },
    "Дева": {
        "description": "<i><u>ДЕВА</u></i>\n\nВспомните, что кропотливая работа - ваш конёк. Никто лучше вас не справится с ней. Поэтому воспользуйтесь возможностью стать еще более незаменимым и полезным человеком. Таким образом, вы зарядитесь  положительными эмоциями. Облагородьте и упорядочите ваше пространство, займитесь своим здоровьем и красотой, поухаживайте за домашними питомцами, вспомните о любимом хобби. Выполните любые действия, благодаря которым вы почувствуете себя под надежной защитой. Для вас это важно, плюс это активирует вашу энергию.",
        "image": os.getenv('DEVA')
    },
    "Весы": {
        "description": "<i><u>ВЕСЫ</u></i>\n\nПосетите любое светское мероприятие, где вы сможете получить удовольствие от искусства и эстетики, красоты и приятного общения. В повседневной жизни создайте гармоничное пространство, где вы сможете наполняться энергетически. Проявите дипломатические способности в переговорах и не забывайте, у вас это получается лучше всех.",
        "image": os.getenv('VESU')
    },
    "Скорпион": {
        "description": "<i><u>СКОРПИОН</u></i>\n\nЗаймитесь расследованием какой-либо жизненной тайны, прикоснитесь к неизведанному. Ваши проницательность и внимание к деталям не оставят никого равнодушным. Активизируйте свою энергию, раскрывая секреты, и помогая другим. Погружайтесь в психоанализ или эзотерику. Совершенствуйтесь и не останавливайтесь на развитии, тем самым вы аккумулируете ваши силы.",
        "image": os.getenv('SKORPION')
    },
    "Стрелец": {
        "description": "<i><u>СТРЕЛЕЦ</u></i>\n\nВам рекомендуются постоянно расширять кругозор - путешествовать и познавать мир любыми способами. Изучайте языки и страны, учитесь и учите сами, обретите  духовного наставника. Применяйте свои знания, становитесь авторитетным экспертом в своей сфере, достигайте поставленных целей. Вам необходимо чувствовать себя значимым человеком, к которому все могут обратиться за советом. Не забывайте, что таким образом вы получаете огромный заряд энергии.",
        "image": os.getenv('STRELEC')
    },
    "Козерог": {
        "description": "<i><u>КОЗЕРОГ</u></i>\n\nНаправьте свой контроль на достижение глобальной цели, благодаря которой вы активируете вашу энергию и у вас появятся силы. Важно повышать социальный статус и окружать себя стабильностью. Выстроите личный жизненный план, чтобы точно двигаться к своей задаче. Ограничьте хаос в жизни и излишнюю эмоциональность, чтобы это не отнимало вашу энергию. Заряжайтесь от общения со статусными и сильными духом людьми.",
        "image": os.getenv('KOZEROG')
    },
    "Водолей": {
        "description": "<i><u>ВОДОЛЕЙ</u></i>\n\nПредоставьте себе возможность самовыражаться. Для вас важно чувствовать независимость и свободу в действиях. Это ваш источник энергии. Не забывайте, вас ценят за креативность, дружелюбие и умение поддержать разговор, с кем бы то ни было. Вы способны создавать необыкновенные вещи, имея особое чутье на современные тенденции. Вас это заряжает.",
        "image": os.getenv('VODOLEJ')
    },
    "Рыбы": {
        "description": "<i><u>РЫБЫ</u></i>\n\nНачните с вашего внутреннего мира. Займитесь духовным развитием. Зарядиться энергией помогут медитации, эзотерика, искусство, выражение своих талантов через творчество. Погрузитесь в поиски смыслов через религию или помощь ближнему. Благотворительность, милосердие и сострадание придаст вам сил. Для вас важно немного отдавать частичку себя.",
        "image": os.getenv('RUBU')
    }
    # Дополнительные знаки зодиака
}

# Путь к локальному изображению для приветственного сообщения
WELCOME_PHOTO_PATH = os.getenv('WELCOME_PHOTO_PATH')

# Функция для генерации inline клавиатуры
def create_inline_keyboard(options, row_width=2):
    keyboard = []
    for i in range(0, len(options), row_width):
        keyboard.append([InlineKeyboardButton(option, callback_data=option) for option in options[i:i+row_width]])
    return InlineKeyboardMarkup(keyboard)

# Функция для генерации стартовой inline клавиатуры
def start_keyboard():
    keyboard = [[InlineKeyboardButton("⚡Узнать", callback_data="start_survey")]]
    return InlineKeyboardMarkup(keyboard)

# Настройка доступа к Google Sheets
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(os.getenv('GOOGLE_CREDENTIALS_PATH'), scope)
    client = gspread.authorize(creds)
    return client

# Запись данных в Google Sheets
def write_to_google_sheets(user_data):
    client = get_gspread_client()
    sheet = client.open("ChatBotBD").worksheet("Energy")

    # Подготовка данных для записи
    row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_data['username'], user_data['telegram_account']] + user_data['answers'] + [user_data.get('addit_data', '')]
    sheet.append_row(row)

# Функция для обработки команды /start
async def start(update: Update, context: CallbackContext) -> int:
    with open(WELCOME_PHOTO_PATH, 'rb') as photo:
        await context.bot.send_photo(
            chat_id=update.message.chat_id,
            photo=photo,
            caption='<b><u>Как раскачать свою энергию для успешной реализации? И не идти на поводу апатии и выгорания?!</u>\n\n<i>Ответ прост - надо ⚡️узнать СЕБЯ лучше.\n\nБлагодаря астро-боту вы познакомитесь с важными действиями, которые являются для вас ЖИЗНЕННО необходимыми, чтобы прийти к личной РЕАЛИЗАЦИИ👇🏼</i></b>\n\n<i>Я Наталия Бонум, профессиональный и дипломированный астролог. Помогаю вам найти СЕБЯ, свою вторую ПОЛОВИНКУ, решить вопрос с ПЕРЕЕЗДом, КАРЬЕРОЙ и ФИНАНСАМИ, и не только.</i>',
            parse_mode='HTML',
            reply_markup=start_keyboard()
        )
    return ASK_NAME

# Функция для обработки начала опроса
async def start_survey(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text('Пожалуйста, введите ваше имя:')
    return ASK_NAME

# Функция для обработки имени пользователя
async def ask_name(update: Update, context: CallbackContext) -> None:
    context.user_data['username'] = update.message.text
    context.user_data['telegram_account'] = update.message.from_user.username  # Сохраняем аккаунт Telegram
    
    # Инициализация переменной answers
    context.user_data['answers'] = []
    
    await update.message.reply_text(
        questions[0],
        parse_mode='HTML',
        reply_markup=create_inline_keyboard(options[0], row_width=3)  # Задаем 3 кнопки в ряду
    )
    return QUESTION1

# Функция для обработки ответов на вопросы
async def handle_question(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    # Получаем answers или создаем пустой список
    answers = context.user_data.setdefault('answers', [])
    answers.append(query.data)
    
    logger.info(f'Answers after appending: {answers}')  # Логируем значения answers после добавления

    current_state = len(answers)
    
    if current_state < len(questions):  # Учитываем, что последний вопрос - это вопрос о данных
        await query.message.reply_text(
            questions[current_state],
            reply_markup=create_inline_keyboard(options[current_state]),
            parse_mode='HTML'
        )
        return QUESTION1 + current_state
    
    elif current_state == len(questions) and query.data == "Отправить данные":
        await query.message.reply_text(
            'Пожалуйста, введите данные:'
        )
        return GET_DATA

    else:
        logger.info(f'First answer: {answers[0]}')  # Логируем первый ответ
        first_answer = answers[0]
        result_description = results.get(first_answer, {"description": "Ваши ответы уникальны, и мы не можем дать конкретное описание."})
                
        if result_description:
            description = result_description['description']
            image_path = result_description.get('image')
    
            if image_path:
                try:
                    with open(image_path, 'rb') as photo:
                        await context.bot.send_photo(
                            chat_id=query.message.chat_id,
                            photo=photo,
                            caption=f'<b>Рекомендации:</b>\n\n{description}',
                            parse_mode='HTML'
                        )
                except FileNotFoundError:
                    await query.message.reply_text(
                        f'<b>Рекомендации:</b>\n\n{description}',
                        parse_mode='HTML'
                    )
            else:
                await query.message.reply_text(
                    f'<b>Рекомендации:</b>\n\n{description}',
                    parse_mode='HTML'
                )

        write_to_google_sheets(context.user_data)
        context.user_data['answers'] = []
        await query.message.reply_text('Присоединяйтесь к моему <a href="https://t.me/astro_nataly_bonum">ТГ-каналу</a> и <a href="https://www.instagram.com/nataly_bonum?igsh=MWo5emFvczUwaHUyNQ==">Инсте</a>, где я делюсь астро-тенденциями и своей жизнью.\nА также познакомьтесь с моим <a href="https://astronbonum.tilda.ws">сайтом</a>.\n\n❤️ Буду ждать вас там!\n\nДо встречи!',
                                       parse_mode='HTML'
                                       )
        return ConversationHandler.END
    
# Функция для обработки данных
async def get_addit_data(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    context.user_data['addit_data'] = user_input
    
    # Проверяем, есть ли ключ 'answers' в user_data
    answers = context.user_data.get('answers', [])
    logger.info(f'Answers: {answers}')  # Логируем значения answers

    # Если 'answers' отсутствует или пуст, информируем пользователя
    if not answers:
        await update.message.reply_text(
            'Не удалось получить ваши ответы. Пожалуйста, начните опрос заново.',
            parse_mode='HTML'
        )
        return ConversationHandler.END

    first_answer = answers[0]
    result_description = results.get(first_answer, {"description": "Ваши ответы уникальны, и мы не можем дать конкретное описание.", "image": None})

    if result_description:
        description = result_description['description']
        image_path = result_description['image']
        
        # Отправляем изображение, если оно есть
        if image_path:
            try:
                with open(image_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=update.message.chat_id,
                        photo=photo,
                        caption=f'<b>Рекомендации:</b>\n\n{description}',
                        parse_mode='HTML'
                    )
            except FileNotFoundError:
                await update.message.reply_text(
                    f'<b>Рекомендации:</b>\n\n{description}',
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text(
                f'<b>Рекомендации:</b>\n\n{description}',
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            f'<b>Рекомендации:</b>\n\n{result_description}',
            parse_mode='HTML'
        )
    
    write_to_google_sheets(context.user_data)
    context.user_data['answers'] = []
    await update.message.reply_text('<i>В ближайшее время я свяжусь с вами ❤️\nИ предоставлю <b>ИНДИВИДУАЛЬНУЮ</b> характеристику вашей главной планеты "Личности" ☀️\nКоторая вам поможет лучше <b>понять СЕБЯ</b> и свои <b>ЖЕЛАНИЯ в жизни!</b></i>\n\nА пока вы можете присоединиться к моему <a href="https://t.me/astro_nataly_bonum">ТГ-каналу</a> и <a href="https://www.instagram.com/nataly_bonum?igsh=MWo5emFvczUwaHUyNQ==">Инсте</a>, где я делюсь астро-тенденциями и своей жизнью.\nА также познакомиться с моим <a href="https://astronbonum.tilda.ws">сайтом</a>.\n\nДо связи!', 
                                    parse_mode='HTML'
                                    )
    return ConversationHandler.END

# Функция для обработки отмены опроса
async def cancel(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        'Опрос прерван.'
    )
    return ConversationHandler.END

# Обработчик ошибок
async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f'Update {update} caused error {context.error}')

async def send_ping(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    await context.bot.send_message(chat_id="504662108", text="Ping!")

def main() -> None:
    application = ApplicationBuilder().token(bot_token).build()

    # Создаем JobQueue для периодических задач
    job_queue = application.job_queue
    #job_queue.run_repeating(send_ping, interval=3600, first=0, data="504662108")  # Пример задания задачи
    if job_queue is None:
        print("JobQueue не инициализирован!")
        return

    job_queue.run_repeating(send_ping, interval=timedelta(minutes=180), first=timedelta(seconds=10), name="ping_job", data="chat_id")

    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_survey, pattern='start_survey')],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            QUESTION1: [CallbackQueryHandler(handle_question, pattern='^(Овен|Телец|Близнецы|Рак|Лев|Дева|Весы|Скорпион|Стрелец|Козерог|Водолей|Рыбы)$')],
            QUESTION2: [CallbackQueryHandler(handle_question, pattern='^(Отправить данные|Нет, спасибо)$')],
            GET_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_addit_data)],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")]
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cancel))  # Обработка текстовых сообщений
    application.add_error_handler(error_handler)

    # Конфигурация и запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()

