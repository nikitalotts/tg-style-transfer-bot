import torch
import torchvision.models as models
from neural_style_transfer.settings import device


async def load_network(type, model_path):
    """Функция загрузки модели"""
    if type == 'vgg19':
        net = models.vgg19()
    else:
        raise FileExistsError('No model with such name')
    net.load_state_dict(torch.load(model_path))
    net = net.features.to(device).eval()
    return net
