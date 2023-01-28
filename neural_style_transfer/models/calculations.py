import torch


def gram(x):
    """Функция подсчета матрицы Грэма"""
    a, b, c, d = x.size()
    features = x.view(a * b, c * d)
    gram_prod = torch.mm(features, features.t())
    return gram_prod.div(a * b * c * d)
