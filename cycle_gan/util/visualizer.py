import os
import ntpath
from . import util


def save_images(visuals, image_path, aspect_ratio=1.0):
    """Сохранить картинки"""
    short_path = ntpath.basename(image_path[0])
    name = os.path.splitext(short_path)[0]
    extension = os.path.splitext(short_path)[1][1:]
    save_pathes = []

    ims = []
    for label, im_data in visuals.items():
        if label == 'fake':
            im = util.tensor2im(im_data)
            image_name = f'%s_%s.{extension}' % (name, label)
            save_path = os.path.join('./tmp', image_name)
            util.save_image(im, save_path, aspect_ratio=aspect_ratio)
            ims.append(image_name)
            save_pathes.append(save_path)

    return save_pathes

