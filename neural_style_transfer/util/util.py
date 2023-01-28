import torch
from torch import nn
import torch.optim as optim
from torchvision import transforms
from neural_style_transfer.models.losses import ContentLoss, StyleLoss
from neural_style_transfer.settings import num_steps, style_weight, content_weight


def generate_model_and_losses(cnn, style_img, content_img):
    """Функция генерации модели и лоссов"""
    content_layers = ['conv_4']
    style_layers = ['conv_1', 'conv_2', 'conv_3', 'conv_4', 'conv_5']

    content_losses = []
    style_losses = []

    normalization = nn.Sequential(
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
    )

    model = nn.Sequential(normalization)

    i = 0
    for layer in cnn.children():
        if isinstance(layer, nn.Conv2d):
            i += 1
            name = 'conv_{}'.format(i)
        elif isinstance(layer, nn.ReLU):
            name = 'relu_{}'.format(i)
            layer = nn.ReLU(inplace=False)
        elif isinstance(layer, nn.MaxPool2d):
            name = 'pool_{}'.format(i)
        elif isinstance(layer, nn.BatchNorm2d):
            name = 'bn_{}'.format(i)
        else:
            raise RuntimeError('Unrecognized layer: {}'.format(layer.__class__.__name__))

        model.add_module(name, layer)

        # добавляем слои Контент-лосса
        if name in content_layers:
            target = model(content_img).detach()
            content_loss = ContentLoss(target)
            model.add_module("content_loss_{}".format(i), content_loss)
            content_losses.append(content_loss)

        # добавляем слои Стайл-лосса
        if name in style_layers:
            target_feature = model(style_img).detach()
            style_loss = StyleLoss(target_feature)
            model.add_module("style_loss_{}".format(i), style_loss)
            style_losses.append(style_loss)

    for i in range(len(model) - 1, -1, -1):
        if isinstance(model[i], ContentLoss) or isinstance(model[i], StyleLoss):
            break

    model = model[:(i + 1)]
    return model, style_losses, content_losses


async def start_nst(cnn, content_img, style_img, num_steps=num_steps, style_weight=style_weight, content_weight=content_weight):
    """Функция запуска трансфера стиля"""

    # получаем модель и лосс-функции
    model, style_losses, content_losses = generate_model_and_losses(cnn, style_img, content_img)

    # подготавливаем данные
    input_img = content_img.clone()
    input_img.requires_grad_(True)
    model.requires_grad_(False)

    # создаем оптимизатор
    optimizer = optim.LBFGS([input_img])

    run = [0]
    while run[0] <= num_steps:
        print("run {}:".format(run))

        # определяем лосс-функция
        def closure():
            with torch.no_grad():
                input_img.clamp_(0, 1)
            optimizer.zero_grad()
            model(input_img)
            style_score = 0
            content_score = 0
            for style_loss in style_losses:
                style_score += style_loss.loss
            for content_loss in content_losses:
                content_score += content_loss.loss
            style_score *= style_weight
            content_score *= content_weight

            loss = style_score + content_score
            loss.backward()

            run[0] += 1
            return style_score + content_score

        optimizer.step(closure)

    with torch.no_grad():
        input_img.clamp_(0, 1)

    return input_img


