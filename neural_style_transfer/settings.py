import torch

# устройство, на котором будут выполняться подсчёты
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# название модели сверточной нейросети(пока доступно только vgg19)
model_type = 'vgg19'

# путь до файла сохранненой модели
model_path = './neural_style_transfer/models_store/vgg19/vgg19.pth'

# размеры выходного изображения:
# 1.если заданы оба размера, то выходное изображение будет точно такого размера
# 2. если указан только один параметр, то второй будет подсчитан автоматически,
#    с сохранением соотношения сторон(ratio) картинки
# 3. Если не задан ни один параметр, то выходное изображение будет размера картинки контента(content image)
x_size = 512
y_size = None

# число шагов оптимизатора
num_steps = 150

# вес пикселей картинки стиля
style_weight = 750000

# вес пикселей картинки контента
content_weight = 1

