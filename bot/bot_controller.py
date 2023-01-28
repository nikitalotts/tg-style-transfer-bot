import aiogram
from typing import List
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters.state import State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from bot.keyboards import start_keyboard, gan_types_keyboard, back_keyboard
from aiogram.types import ContentType
from bot.config import token
from bot.files import get_input_files, is_extension_allowed, download_file, delete_temp_file
from cycle_gan.api import process_image
from neural_style_transfer.api import transfer_image
from bot.states import *
from bot.enums import *


bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.async_task
@dp.message_handler(state="*", commands=['start'])
async def start(message: types.Message):
    """обработка запуска бота"""
    await switch_state(user=message.from_user.id, state=DefaultStates.CHOOSING_METHOD.state)
    await message.answer("Выберете каким способом хотите перенести стиль:", reply_markup=start_keyboard)


@dp.async_task
@dp.message_handler(state="*", commands=['help'])
async def show_help(message: types.Message):
    """обработка команды помощи"""
    await message.answer("Если возникли неподалдки - перезапустите бота, введя команду /start ")


@dp.async_task
@dp.message_handler(state=DefaultStates.CHOOSING_METHOD, text='GAN')
async def chose_gan(message: types.Message):
    """обработка выбора гана"""
    await switch_state(user=message.from_user.id, state=GANStates.GAN_WAITING_FOR_ARTIST.state)
    await message.answer("Выберете стиль в который нужно перевест изображение:", reply_markup=gan_types_keyboard)


@dp.async_task
@dp.message_handler(state=GANStates.GAN_WAITING_FOR_ARTIST, text=['Vangogh', 'Ukiyoe', 'Monet', 'Cezanne'])
async def chose_style(message: types.Message):
    """обработка выбора стиля гана"""
    state = dp.current_state(user=message.from_user.id)
    await switch_state(user=message.from_user.id, state=GANStates.GAN_WAITING_FOR_IMAGE.state, current_state=state)

    async with state.proxy() as data:
        data['gan_type'] = message.text.lower()

    await message.answer("Пожалуйста, отправьте изображение, для которого нужно изменить стиль",
                         reply_markup=back_keyboard)


@dp.async_task
@dp.message_handler(state=DefaultStates.CHOOSING_METHOD, text='NST')
async def chose_nst(message: types.Message):
    """обработка выбора nst"""
    await switch_state(user=message.from_user.id, state=NSTStates.NST_WAITING_FOR_IMAGES.state)
    await bot.send_message(message.from_user.id,
                           "Пожалуйста, отправьте два изображения: с первого будет взят стиль и перенесен на второе",
                           reply_markup=back_keyboard)


@dp.message_handler(state=NSTStates.NST_WAITING_FOR_IMAGES, is_media_group=True, content_types=types.ContentType.ANY)
@dp.async_task
async def process_many_images(message: types.Message, album: List[types.Message]):
    """
    обработка множественного получения файлов,
    когда в одном сообщении несколько фото или документов
    """
    images = await get_input_files(bot, message, album)
    if len(images) == 1:
        await bot.send_message(chat_id=message.chat.id,
                               text='Ошибка: среди отправленных файлов только одно изображение')
    elif not images:
        await bot.send_message(chat_id=message.chat.id, text='Ошибка: проверьте формат отправляемых файлов')
    else:
        style_image_path = images[0]
        content_image_path = images[1]
        await remove_keyboard(message)
        transferred_image = await transfer_image(style_img_path=style_image_path, content_img_path=content_image_path)
        photo = open(transferred_image, "rb")
        await bot.send_photo(message.chat.id, photo=photo)
        await delete_temp_file(transferred_image, style_image_path, content_image_path)
        await return_home(message)


@dp.async_task
@dp.message_handler(state=[NSTStates.NST_WAITING_FOR_IMAGES, GANStates.GAN_WAITING_FOR_IMAGE],
                    content_types=ContentType.ANY)
async def process_first_image(message: types.Message):
    """
    обработка первого полученного изображения,
    случай когда в сообщениии одно фото/файл
    """
    state = dp.current_state(user=message.from_user.id)
    method_type = Model.NST if await state.get_state() == NSTStates.NST_WAITING_FOR_IMAGES.state else Model.GAN
    photo = message.photo
    document = message.document
    if not photo and document is None:
        await bot.send_message(message.chat.id, 'Ошибка: вы отправили не фото')
    elif document is not None and not await is_extension_allowed(await bot.get_file(document.file_id)):
        await bot.send_message(message.chat.id, 'Ошибка: вы отправили не фото')
    else:
        async with state.proxy() as data:
            data['first_image'] = {}
            if photo:
                data['first_image']['photo'] = photo[-1]
            if document:
                data['first_image']['document'] = document
        if method_type == Model.NST:
            await switch_state(user=message.from_user.id, state=NSTStates.NST_WAITING_SECOND_IMAGE.state,
                               current_state=state)
            await bot.send_message(message.chat.id, 'Отправьте второе фото')
        elif method_type == Model.GAN:
            await switch_state(user=message.from_user.id, state=GANStates.GAN_WORKING.state, current_state=state)
            await remove_keyboard(message)
            async with state.proxy() as data:
                if photo:
                    input_file_path = await download_file(bot, data['first_image']['photo'])
                elif document is not None:
                    input_file_path = await download_file(bot, data['first_image']['document'])
                else:
                    raise FileNotFoundError('No attachments to message')
                output_file_path = await process_image(file_path=input_file_path, artist_name=data['gan_type'])
            image = open(output_file_path, "rb")
            if photo:
                await bot.send_photo(message.chat.id, photo=image)
            elif document is not None:
                await bot.send_document(message.chat.id, document=image)
            else:
                raise NotImplementedError('No such type')
            await return_home(message)
            await delete_temp_file(input_file_path, output_file_path)
        else:
            raise ValueError('No such type')


@dp.message_handler(state=NSTStates.NST_WAITING_SECOND_IMAGE, content_types=ContentType.ANY)
@dp.async_task
async def process_second_image(message: types.Message):
    """
    обработка первого полученного изображения,
    случай когда в сообщениии одно фото/файл
    """
    state = dp.current_state(user=message.from_user.id)
    photo = message.photo
    document = message.document
    if not photo and document is None:
        await bot.send_message(message.chat.id, 'Ошибка: вы отправили не фото')
    elif document is not None and not await is_extension_allowed(await bot.get_file(document.file_id)):
        await bot.send_message(message.chat.id, 'Ошибка: вы отправили не фото')
    else:
        async with state.proxy() as data:
            data['second_image'] = {}
            if photo:
                data['second_image']['photo'] = photo[-1]
            if document:
                data['second_image']['document'] = document
        await switch_state(user=message.from_user.id, state=NSTStates.NST_WORKING.state, current_state=state)
        await remove_keyboard(message)
        async with state.proxy() as data:
            image_paths = await get_input_files(bot=bot, is_media_group=False, data_to_download=data)
            style_image_path = image_paths[0]
            content_image_path = image_paths[1]
            photos = await any_photos(data)
        transferred_image = await transfer_image(style_image_path, content_image_path)
        if photos:
            photo = open(transferred_image, "rb")
            await bot.send_photo(message.chat.id, photo=photo)
        else:
            document = open(transferred_image, "rb")
            await bot.send_document(message.chat.id, document=document)
        await delete_temp_file(transferred_image, style_image_path, content_image_path)
        await return_home(message)


@dp.async_task
@dp.message_handler(
    state=[NSTStates.NST_WAITING_FOR_IMAGES, NSTStates.NST_WAITING_SECOND_IMAGE, GANStates.GAN_WAITING_FOR_ARTIST,
           GANStates.GAN_WAITING_FOR_IMAGE], text='Back')
async def back(message: types.Message):
    """обработка команды назад"""
    current_state = dp.current_state(user=message.from_user.id)
    state = await current_state.get_state()
    await current_state.finish()
    if state == NSTStates.NST_WAITING_FOR_IMAGES.state or state == NSTStates.NST_WAITING_SECOND_IMAGE.state or state == GANStates.GAN_WAITING_FOR_ARTIST.state:
        await switch_state(user=message.from_user.id, state=DefaultStates.CHOOSING_METHOD.state,
                           current_state=current_state)
        await message.answer(text='Выберете каким способом хотите перенести стиль:', reply_markup=start_keyboard)
        if state == NSTStates.NST_WAITING_SECOND_IMAGE.state:
            async with current_state.proxy() as data:
                data['first_image'] = {}
    elif state == GANStates.GAN_WAITING_FOR_IMAGE.state:
        await switch_state(user=message.from_user.id, state=GANStates.GAN_WAITING_FOR_ARTIST.state,
                           current_state=current_state)
        await message.answer(text='Выберете стиль в который нужно перевести изображение:',
                             reply_markup=gan_types_keyboard)
    else:
        raise ValueError('Error in getting back')


@dp.message_handler(state=[NSTStates.NST_WORKING, GANStates.GAN_WORKING], content_types=ContentType.ANY)
async def handle_while_working(message: types.Message):
    """
    обработка сообщений во время обработки изображений:
    пока обработка изображения пользователя не закончилась,
    он не может отменить ее или запустить новую
    """
    await bot.send_message(message.chat.id, 'извините я работаю')


@dp.async_task
@dp.message_handler(state=DefaultStates.CHOOSING_METHOD, content_types=types.ContentType.ANY)
async def wrong_input(message: types.Message):
    """обработка некорректного ввода на главном меню"""
    if message.text == "/help":
        await show_help(message)
    else:
        await message.answer("Пожалуйста, выберите из меню каким способом хотите перенести изображение")


@dp.async_task
@dp.message_handler(state="*", commands=['cancel'])
async def cancel(message: types.Message):
    """обработка команды об отмене всех операций"""
    state = dp.current_state(user=message.from_user.id)
    await state.finish()
    await switch_state(user=message.from_user.id, state=DefaultStates.CHOOSING_METHOD.state)
    await message.answer("Завершаю все операции", reply_markup=start_keyboard)


async def return_home(message: types.Message):
    """обработка возврата на главное меню"""
    state = dp.current_state(user=message.from_user.id)
    await state.finish()
    await switch_state(user=message.from_user.id, state=DefaultStates.CHOOSING_METHOD.state)
    await message.answer("Обработка завершена", reply_markup=start_keyboard)


async def switch_state(user: int, state: aiogram.dispatcher.filters.state, current_state=None):
    """функция изменения состояния пользователя"""
    if current_state is None:
        current_state = dp.current_state(user=user)
    await current_state.set_state(state)


async def remove_keyboard(message: types.Message):
    """функция удаления клавиатуры во время начала обработки изображения"""
    await message.answer("Начинаю обработку изображения, примерное время работы 1-3 минуты",
                         reply_markup=aiogram.types.ReplyKeyboardRemove())


async def any_photos(data):
    """
    функция проверки, есть ли среди полученных файлов хоть один файл,
    отправленный как фото
    """
    has_photos = False
    if 'photo' in data['first_image'].keys():
        has_photos = True
    if 'photo' in data['second_image'].keys():
        has_photos = True
    return has_photos

# import asyncio
# import functools
# transferred_image = await asyncio.get_running_loop().run_in_executor(None, functools.partial(transfer_image,
#                                                                                                      style_img_path=style_image_path,
#                                                                                                      content_img_path=content_image_path)
