from __future__ import print_function

from neural_style_transfer.models.networks import load_network
from neural_style_transfer.util.image_processing import *
from neural_style_transfer.util.util import start_nst
from neural_style_transfer.settings import model_type, model_path


async def transfer_image(style_img_path, content_img_path):
    """Главная функция переноса стиля"""
    style_img, content_img = get_images(style_img_path, content_img_path)
    net = await load_network(model_type, model_path)
    output = await start_nst(net, content_img, style_img)
    output_path = get_output_file_path(content_img_path)
    save_image(output, output_path)
    return output_path


