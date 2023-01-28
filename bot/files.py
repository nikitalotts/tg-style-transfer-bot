import pathlib
import aiogram
from typing import List
from aiogram import types
import os


def read_file(file_name):
    with open(file_name, 'r', encoding="utf8") as file:
        return file.read()


async def group_files(message: types.Message, album: List[types.Message]):
    """функция группировки файлов"""
    media_group = list()
    for obj in album:
        if obj.photo:
            file_id = obj.photo[-1].file_id
        else:
            file_id = obj[obj.content_type].file_id
        try:
            # We can also add a caption to each file by specifying `"caption": "text"`
            media_group.append({"file_id": file_id, "type": obj.content_type})
        except ValueError:
            return await message.answer("This type of album is not supported by aiogram.")

    return media_group


async def select_files(bot: aiogram.bot.bot, media_group):
    """функция выбора подходящих файлов из медиа групп"""
    files_to_download = []
    for file in media_group:
        if len(files_to_download) >= 2:
            break
        file_info = await bot.get_file(file["file_id"])
        if not await is_extension_allowed(file_info):
            continue
        else:
            files_to_download.append(file_info)

    return files_to_download


async def download_file(bot: aiogram.bot.bot, file):
    """функция загрузки файла"""
    try:
        file = await bot.get_file(file["file_id"])
        downloading_file = await bot.download_file(file.file_path)
        path = "./tmp"
        is_exist = os.path.exists(path)
        if not is_exist:
            os.makedirs(path)
            print('created path')
        src = path + f"/{file.file_id}.{pathlib.Path(file.file_path).suffix.lower()[1:]}"
        with open(src, 'wb') as new_file:
            new_file.write(downloading_file.read())
    except Exception as e:
        raise ConnectionError("Cannot download file")
    return src


async def is_extension_allowed(file_info):
    """функция проверки расширений файлов"""
    file_extension = pathlib.Path(file_info["file_path"]).suffix.lower()[1:]
    return file_extension in ["jpg", "png", "jpeg"]


async def delete_temp_file(*files):
    """функция удалений файлов с диска"""
    try:
        for file in files:
            if os.path.exists(file):
                os.remove(file)
    except Exception as e:
        raise ConnectionError("Cannot delete file")


async def get_input_files(bot: aiogram.bot.bot, message: types.Message = None,
                          album: List[types.Message] = None, is_media_group: bool = True, data_to_download: dict = None):
    """получение на диск подходящих входящих файлов"""
    folder = "./tmp"
    is_exist = os.path.exists(folder)
    if not is_exist:
        os.makedirs(folder)
        print('created path')
    files_paths = []
    files_to_download = []
    if is_media_group:
        media_group = await group_files(message, album)
        files_to_download = await select_files(bot, media_group)
    else:
        if 'photo' in data_to_download['first_image'].keys():
            files_to_download.append(data_to_download['first_image']['photo'])
        if 'document' in data_to_download['first_image'].keys():
            files_to_download.append(data_to_download['first_image']['document'])
        if 'photo' in data_to_download['second_image'].keys():
            files_to_download.append(data_to_download['second_image']['photo'])
        if 'document' in data_to_download['second_image'].keys():
            files_to_download.append(data_to_download['second_image']['document'])
    for file in files_to_download:
        try:
            if not is_media_group:
                file = await bot.get_file(file["file_id"])
            downloading_file = await bot.download_file(file['file_path'])

            src = folder + f"/{file.file_id}.{pathlib.Path(file['file_path']).suffix.lower()[1:]}"
            # print(src)
            with open(src, 'wb') as new_file:
                new_file.write(downloading_file.read())
            files_paths.append(src)
        except Exception as e:
            raise e
    return files_paths
