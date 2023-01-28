from PIL import Image

from cycle_gan.models import create_model
from cycle_gan.options.test_options import TestOptions
from cycle_gan.util.image_processing import get_transform
from cycle_gan.util.visualizer import save_images


async def process_image(file_path, artist_name, preprocess=None):
    """Главная функция переноса стиля"""
    # setup options
    opt = TestOptions().parse()  # get test options
    opt.model = 'test'
    opt.name = artist_name
    if preprocess is not None:
        opt.preprocess = preprocess

    # create a model given opt.model and other options
    model = create_model(opt)
    model.setup(opt)

    # load image
    image = Image.open(file_path).convert('RGB')
    input_nc = 3 if image.mode == "RGB" else 1
    if input_nc not in (1, 2, 3):
        raise Exception

    # transform
    transform = get_transform(opt, grayscale=(input_nc == 1))
    image_path = file_path
    image = transform(image)

    # create input data
    if len(image.shape) == 3:
        image = image.unsqueeze(0)
    inp_dict = {'image': image, 'image_path': image_path}

    # load input data
    model.set_input(inp_dict)

    # convert
    model.convert_single_image(model.real)

    # get results
    visuals = model.get_current_visuals()
    img_path = [model.get_image_paths()]  # get image paths
    return save_images(visuals, img_path, aspect_ratio=opt.aspect_ratio)[0]



