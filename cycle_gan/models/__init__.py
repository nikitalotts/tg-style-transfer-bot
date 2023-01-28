import importlib
from cycle_gan.models.base_model import BaseModel


def find_model_using_name(model_name):
    """Функция поиска модели по названию"""
    model_filename = "cycle_gan.models." + model_name + "_model"
    modellib = importlib.import_module(model_filename)
    model = None
    target_model_name = model_name.replace('_', '') + 'model'
    for name, cls in modellib.__dict__.items():
        if name.lower() == target_model_name.lower() \
           and issubclass(cls, BaseModel):
            model = cls

    if model is None:
        raise FileNotFoundError('No model with such name')

    return model


def get_option_setter(model_name):
    """Функция получения опций"""
    model_class = find_model_using_name(model_name)
    return model_class.modify_commandline_options


def create_model(opt):
    """Функция инициализации модели"""
    model = find_model_using_name(opt.model)
    instance = model(opt)
    return instance
