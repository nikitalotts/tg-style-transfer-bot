import torch.nn as nn
from torchmetrics.functional import mean_squared_error
from neural_style_transfer.models.calculations import gram


class ContentLoss(nn.Module):
    """Класс для подсчета Контент-лосса"""
    def __init__(self, target,):
        super(ContentLoss, self).__init__()
        self.target = target.detach()

    def forward(self, image):
        self.loss = mean_squared_error(image, self.target)
        return image


class StyleLoss(nn.Module):
    """Класс для подсчета Стайл-лосса"""
    def __init__(self, target_feature):
        super(StyleLoss, self).__init__()
        self.target = gram(target_feature).detach()

    def forward(self, input):
        gram_matrix = gram(input)
        self.loss = mean_squared_error(gram_matrix, self.target)
        return input