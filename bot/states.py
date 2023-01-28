from aiogram.dispatcher.filters.state import State, StatesGroup


# state`ы для стартовых состояний бота
class DefaultStates(StatesGroup):
    CHOOSING_METHOD = State()
    ERROR = State()


# state`ы для состояний бота, при выборе NST
class NSTStates(StatesGroup):
    NST_WORKING = State()
    NST_WAITING_SECOND_IMAGE = State()
    NST_WAITING_FOR_IMAGES = State()


# state`ы для состояний бота, при выборе GAN`а
class GANStates(StatesGroup):
    GAN_WORKING = State()
    GAN_WAITING_FOR_IMAGE = State()
    GAN_WAITING_FOR_ARTIST = State()
