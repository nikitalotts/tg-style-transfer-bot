from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# стартовая клавиатура
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='NST'),
            KeyboardButton(text='GAN')
        ]
    ],
    resize_keyboard=True
)

# клавиатура выбора ганов
gan_types_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Vangogh'),
            KeyboardButton(text='Ukiyoe'),
            KeyboardButton(text='Monet'),
            KeyboardButton(text='Cezanne')
        ],
        [
            KeyboardButton(text='Back')
        ]
    ],
    resize_keyboard=True
)

# клавиатура с кнопкой назад
back_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Back'),
        ]
    ],
    resize_keyboard=True
)

