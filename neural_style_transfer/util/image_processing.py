import os
import torch
import torchvision.transforms as transforms
from PIL import Image
from neural_style_transfer.settings import device, x_size, y_size


def get_images(style_img_path, content_img_path):
    """Функция получения и резайса картинок"""
    style_img, content_img = Image.open(style_img_path), Image.open(content_img_path)
    x, y = content_img.size

    if x_size is not None and y_size is not None:
        size = (x_size, y_size)
    elif x_size is not None and y_size is None:
        ratio = y / x
        size = (x_size, int(x_size * ratio))
    elif x_size is None and y_size is not None:
        ratio = x / y
        size = (int(y_size * ratio), y_size)
    else:
        size = (x, y)

    style_img_loader, content_img_loader = get_image_loader(resize_size=size), get_image_loader(resize_size=size)

    style_img = style_img_loader(style_img).unsqueeze(0)
    content_img = content_img_loader(content_img).unsqueeze(0)

    style_img = style_img.to(device, torch.float)
    content_img = content_img.to(device, torch.float)

    return style_img, content_img


def get_image_loader(resize_size=None):
    """Функция генерации необходимых трансформаций"""
    transformations = []
    if resize_size is not None:
        transformations.append(transforms.Resize((resize_size[1], resize_size[0])))
    transformations.append(transforms.ToTensor())
    loader = transforms.Compose(transformations)
    return loader


def save_image(image_tensor, image_path):
    """Функция сохранения картинок"""
    if image_tensor.shape[0] == 1:
        image_tensor = image_tensor.squeeze()
    else:
        raise ValueError('Входной формат не соответствует ожидаемому')
    transform = transforms.ToPILImage()
    image_pil = transform(image_tensor)
    image_pil.save(image_path)


def get_output_file_path(file_path):
    """Функция получения пути выходного файла"""
    folder = './tmp'
    file_name = os.path.basename(file_path)
    file = os.path.splitext(file_name)
    new_path = file[0] + '_transferred' + file[1]
    return os.path.join(folder, new_path)


def delete_temp_file(*files):
    """Функция удаления временных файлов"""
    try:
        for file in files:
            if os.path.exists(file):
                os.remove(file)
    except Exception as e:
        raise ConnectionError("Cannot delete file")

