import cv2
import matplotlib.pyplot as plt
import os
import tensorflow as tf  
# from tensorflow.keras.preprocessing import image
import numpy as np
import pywt
from skimage.restoration import (denoise_wavelet, estimate_sigma)
from itertools import product
from pathlib import Path
import tempfile
import shutil

class ProcessingClass:
    def __init__(self, input_path, model_path, output_path):
        self.input_path = input_path
        self.model_path = model_path
        self.output_path = output_path
        # self.processing_mode = processing_mode

        self.model = tf.keras.models.load_model(self.model_path)

    def cleanup(self):
        """
        Явное освобождение ресурсов.
        """
        if hasattr(self, 'model'):
            del self.model

    # ================================================================================
    # ФУНКЦИИ ДЛЯ ИСПРАВЛЕНИЯ РАЗМЫТЫХ ИЗОБРАЖЕНИЙ
    # ================================================================================

    def unsharp_masking(self, image, sigma=3, coeffs=(2.5, -1.5)):
        """
        Восстановление путем вычитания размытого из исходного.
        На вход подается исходное, которое размыто,
        оно размывается еще больше, и разность между размытым и совсем размытым сохраняется.
        Затем разность прибавляется к исходному размытому - для увеличения резкости.
        Принимает коэффициенты: положительный и отрицательный. Их сумма должна быть равна 1.
        """
        blurred_image = cv2.GaussianBlur(image, (0, 0), sigmaX=sigma)
        sharpened_image = cv2.addWeighted(image, coeffs[0], blurred_image, coeffs[1], 0)
        return sharpened_image
    
    def laplacian_sharpening(self, image, coeff=3):
        """
        Использует фильтр Лапласа.
        """
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        sharpened_image = image - coeff * laplacian
        sharpened_image = np.clip(sharpened_image, 0, 255).astype(np.uint8)
        return sharpened_image
    
    
    # ================================================================================
    # ФУНКЦИИ ДЛЯ ИСПРАВЛЕНИЯ НИЗКОКОНТРАСТНЫХ ИЗОБРАЖЕНИЙ
    # ================================================================================

    def hist_equalization(self, image, color_space):
        """
        Выполняет гистограммное выравнивание - сначала преобразует картинку в нужное цветовое пространство, 
        а затем применяет преобразование лишь к каналу яркости.
        """
        if color_space == 'yuv':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            channels = list(cv2.split(converted_image))
            index = 0  # Y-канал (яркость)
        elif color_space == 'hsv':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            channels = list(cv2.split(converted_image))
            index = 2  # V-канал (яркость)

        channels[index] = cv2.equalizeHist(channels[index])
        image_hist = cv2.merge(channels)
        if color_space == 'yuv':
            image_hist = cv2.cvtColor(image_hist, cv2.COLOR_YUV2BGR)
        elif color_space == 'hsv':
            image_hist = cv2.cvtColor(image_hist, cv2.COLOR_HSV2BGR)

        return image_hist
    
    def clahe_algorithm(self, image, color_space, clip_limit, tile_grid_size):
        """
        Разбивает изображение на квадраты, и выполняет гистограммное выравнивание внутри каждого
        а перед этим еще в соответствии с clip_limit выбросы гистограммы обрезаются и раскидываются 
        по остальным столбикам.
        """
        if color_space == 'yuv':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            channels = list(cv2.split(converted_image))
            index = 0  # Y-канал (яркость)
        elif color_space == 'hsv':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            channels = list(cv2.split(converted_image))
            index = 2  # V-канал (яркость)

        clahe = cv2.createCLAHE(clip_limit, tile_grid_size)
        channels[index] = clahe.apply(channels[index])

        image_clahe = cv2.merge(channels)
        if color_space == 'yuv':
            image_clahe = cv2.cvtColor(image_clahe, cv2.COLOR_YUV2BGR)
        elif color_space == 'hsv':
            image_clahe = cv2.cvtColor(image_clahe, cv2.COLOR_HSV2BGR)

        return image_clahe
    
    
    # ================================================================================
    # ФУНКЦИИ ДЛЯ ИСПРАВЛЕНИЯ ИЗОБРАЖЕНИЙ С БЛИКАМИ
    # ================================================================================

    def glares_inpaint(
        self,
        image, 
        color_space_mask='gray', 
        color_space='rgb', 
        threshold=200, 
        inpaint_radius=3, 
        flags=cv2.INPAINT_NS,
        mask_mode='brightness',
        gradient_method='sobel',
        gradient_threshold=50,
    ):
        """
        Исправляет блики на изображении с использованием маски на основе яркости, градиента или их комбинации.
        Принимает следующие параметры:

        image: исходное изображение;
        color_space_mask: цветовое пространство для создания маски ('yuv', 'hsv', 'gray');
        color_space: цветовое пространство для восстановления ('rgb', 'yuv', 'hsv', 'gray');
        threshold: порог для создания маски на основе яркости;
        inpaint_radius: радиус восстановления;
        flags: способ заполнения бликов новыми пикселями (cv2.INPAINT_NS или cv2.INPAINT_TELEA).
        gradient_method: способ вычисления градиента ('sobel', 'scharr', 'laplacian').
        gradient_threshold: порог для создания маски на основе градиента.
        mask_mode: режим создания маски ('brightness', 'gradient', 'combine').
        """
        # преобразование изображения в нужное цветовое пространство для маски
        if color_space_mask == 'yuv':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            channels = list(cv2.split(converted_image))
            index = 0  # Y-канал (яркость)
        elif color_space_mask == 'hsv':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            channels = list(cv2.split(converted_image))
            index = 2  # V-канал (яркость)
        elif color_space_mask == 'gray':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            channels = [converted_image]
            index = 0

        # создание маски на основе яркости
        if mask_mode in ['brightness', 'combine']:
            _, brightness_mask = cv2.threshold(channels[index], threshold, 255, cv2.THRESH_BINARY)
        else:
            brightness_mask = None

        # создание маски на основе градиента
        if mask_mode in ['gradient', 'combine']:
            if gradient_method == 'sobel':
                grad_x = cv2.Sobel(channels[index], cv2.CV_64F, 1, 0, ksize=3)
                grad_y = cv2.Sobel(channels[index], cv2.CV_64F, 0, 1, ksize=3)
                gradient = np.sqrt(grad_x**2 + grad_y**2)
            elif gradient_method == 'scharr':
                grad_x = cv2.Scharr(channels[index], cv2.CV_64F, 1, 0)
                grad_y = cv2.Scharr(channels[index], cv2.CV_64F, 0, 1)
                gradient = np.sqrt(grad_x**2 + grad_y**2)
            elif gradient_method == 'laplacian':
                gradient = cv2.Laplacian(channels[index], cv2.CV_64F)

            # нормализация градиента и создание маски
            gradient = cv2.normalize(gradient, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
            _, gradient_mask = cv2.threshold(gradient, gradient_threshold, 255, cv2.THRESH_BINARY)
        else:
            gradient_mask = None

        # комбинирование масок (если требуется)
        if mask_mode == 'combine':
            if brightness_mask is not None and gradient_mask is not None:
                mask = cv2.bitwise_or(brightness_mask, gradient_mask)  # Объединение масок
        elif mask_mode == 'brightness':
            mask = brightness_mask
        elif mask_mode == 'gradient':
            mask = gradient_mask

        # восстановление изображения
        if color_space == 'rgb':
            inpaint_image = cv2.inpaint(image, mask, inpaintRadius=inpaint_radius, flags=flags)
        else:
            channels[index] = cv2.inpaint(channels[index], mask, inpaintRadius=inpaint_radius, flags=flags)
            if color_space == 'gray':
                inpaint_image = cv2.cvtColor(channels[index], cv2.COLOR_GRAY2BGR)
            else:
                inpaint_image = cv2.merge(channels)
                if color_space == 'yuv':
                    inpaint_image = cv2.cvtColor(inpaint_image, cv2.COLOR_YUV2BGR)
                elif color_space == 'hsv':
                    inpaint_image = cv2.cvtColor(inpaint_image, cv2.COLOR_HSV2BGR)
        
        return inpaint_image
    
    def adaptive_glares_inpaint(
        self,
        image, 
        color_space_mask='gray', 
        color_space='rgb', 
        adaptive_method=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        block_size=11, 
        C=2, 
        inpaint_radius=3, 
        flags=cv2.INPAINT_NS,
        mask_mode='brightness',
        gradient_threshold=50,
        gradient_method='sobel'
    ):
        """
        Адаптивно исправляет блики на изображении с использованием маски на основе яркости, градиента или их комбинации.
        Изображение разбивается на блоки, в каждом из них вычисляется порог - как среднее (или взвешенное 
        минус заданная константа).
        Принимает следующие параметры:

        image: исходное изображение;
        color_space_mask: цветовое пространство для создания маски ('yuv', 'hsv', 'gray');
        color_space: цветовое пространство для восстановления ('rgb', 'yuv', 'hsv', 'gray');
        threshold: порог для создания маски на основе яркости;
        adaptive_method: метод адаптивного порога (cv2.ADAPTIVE_THRESH_GAUSSIAN_C или cv2.ADAPTIVE_THRESH_MEAN_C);
        blockSize: размер блоков, на которые разбивать;
        C - константа, которую вычитать из среднего или взвешенного;
        inpaint_radius: радиус восстановления;
        flags: способ заполнения бликов новыми пикселями (cv2.INPAINT_NS или cv2.INPAINT_TELEA).
        gradient_method: способ вычисления градиента ('sobel', 'scharr', 'laplacian').
        gradient_threshold: порог для создания маски на основе градиента.
        mask_mode: режим создания маски ('brightness', 'gradient', 'combine').
        """
        # преобразование изображения в нужное цветовое пространство для маски
        if color_space_mask == 'yuv':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            channels = list(cv2.split(converted_image))
            index = 0  # Y-канал (яркость)
        elif color_space_mask == 'hsv':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            channels = list(cv2.split(converted_image))
            index = 2  # V-канал (яркость)
        elif color_space_mask == 'gray':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            channels = [converted_image]
            index = 0

        # создание маски на основе яркости
        if mask_mode in ['brightness', 'combine']:
            brightness_mask = cv2.adaptiveThreshold(
                channels[index], 
                255, 
                adaptive_method, 
                cv2.THRESH_BINARY, 
                block_size, 
                C
            )
        else:
            brightness_mask = None

        # создание маски на основе градиента
        if mask_mode in ['gradient', 'combine']:
            if gradient_method == 'sobel':
                grad_x = cv2.Sobel(channels[index], cv2.CV_64F, 1, 0, ksize=3)
                grad_y = cv2.Sobel(channels[index], cv2.CV_64F, 0, 1, ksize=3)
                gradient = np.sqrt(grad_x**2 + grad_y**2)
            elif gradient_method == 'scharr':
                grad_x = cv2.Scharr(channels[index], cv2.CV_64F, 1, 0)
                grad_y = cv2.Scharr(channels[index], cv2.CV_64F, 0, 1)
                gradient = np.sqrt(grad_x**2 + grad_y**2)
            elif gradient_method == 'laplacian':
                gradient = cv2.Laplacian(channels[index], cv2.CV_64F)

            # нормализация градиента и создание маски
            gradient = cv2.normalize(gradient, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
            _, gradient_mask = cv2.threshold(gradient, gradient_threshold, 255, cv2.THRESH_BINARY)
        else:
            gradient_mask = None

        # комбинирование масок (если требуется)
        if mask_mode == 'combine':
            if brightness_mask is not None and gradient_mask is not None:
                mask = cv2.bitwise_or(brightness_mask, gradient_mask)
        elif mask_mode == 'brightness':
            mask = brightness_mask
        elif mask_mode == 'gradient':
            mask = gradient_mask

        # восстановление изображения
        if color_space == 'rgb':
            inpaint_image = cv2.inpaint(image, mask, inpaintRadius=inpaint_radius, flags=flags)
        else:
            channels[index] = cv2.inpaint(channels[index], mask, inpaintRadius=inpaint_radius, flags=flags)
            if color_space == 'gray':
                inpaint_image = cv2.cvtColor(channels[index], cv2.COLOR_GRAY2BGR)
            else:
                inpaint_image = cv2.merge(channels)
                if color_space == 'yuv':
                    inpaint_image = cv2.cvtColor(inpaint_image, cv2.COLOR_YUV2BGR)
                elif color_space == 'hsv':
                    inpaint_image = cv2.cvtColor(inpaint_image, cv2.COLOR_HSV2BGR)

        return inpaint_image
    

    # ================================================================================
    # ФУНКЦИИ ДЛЯ ИСПРАВЛЕНИЯ ИЗОБРАЖЕНИЙ С ШУМАМИ
    # ================================================================================

    def adaptive_median_filter(self, image, estimate_noise='gaussian', sigma=3):
        """
        Фильтр медианного значения с модификациями: сначала оценивается уровень шума выбранным способом,
        в зависимости от него выбирается размер ядра.
        """
        if estimate_noise == 'gaussian':
            blurred = cv2.GaussianBlur(image, (0, 0), sigma)
            diff = image - blurred
            noise_level = np.std(diff)
        elif estimate_noise == 'function':
            noise_level = estimate_sigma(image, average_sigmas=True, channel_axis=-1)
        
        if noise_level < 10:
            kernel_size = 3
        elif noise_level < 30:
            kernel_size = 5
        else:
            kernel_size = 7
        
        median_image = cv2.medianBlur(image, kernel_size)
        return median_image
    
    def adaptive_average_filter(self, image, estimate_noise, sigma=3):
        """
        Фильтр среднего значения с модификациями: сначала оценивается уровень шума выбранным способом,
        в зависимости от него выбирается размер ядра.
        """
        if estimate_noise == 'gaussian':
            blurred = cv2.GaussianBlur(image, (0, 0), sigma)
            diff = image - blurred
            noise_level = np.std(diff)
        elif estimate_noise == 'function':
            noise_level = estimate_sigma(image, average_sigmas=True, channel_axis=-1)
        if noise_level < 10:
            kernel_size = 3
        elif noise_level < 30:
            kernel_size = 5
        else:
            kernel_size = 7
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size ** 2)
        average_image = cv2.filter2D(image, -1, kernel)
        return average_image
    
    def adaptive_gaussian_filter(self, image, estimate_noise='gaussian', sigma=3):
        """
        Фильтр гаусса с модификациями: сначала оценивается уровень шума выбранным способом,
        в зависимости от него выбирается размер ядра.
        """
        if estimate_noise == 'gaussian':
            blurred = cv2.GaussianBlur(image, (0, 0), sigma)
            diff = image - blurred
            noise_level = np.std(diff)
        elif estimate_noise == 'function':
            noise_level = estimate_sigma(image, average_sigmas=True, channel_axis=-1)
        
        if noise_level < 10:
            sigma = 1
        elif noise_level < 30:
            sigma = 3
        else:
            sigma = 5
        
        gaussian_image = cv2.GaussianBlur(image, (0, 0), sigma)
        return gaussian_image
    
    def wavelet_processing(self, image, type, mode, number_of_levels, estimate_noise, sigma=None):
        """
        Подходит только для одноканальных изображений.
        """
        coeffs = pywt.wavedec2(data=image, wavelet=type, level=number_of_levels)
        if estimate_noise == 'gaussian':
            blurred = cv2.GaussianBlur(image, (0, 0), sigma)
            diff = image - blurred
            noise_level = np.std(diff)
        elif estimate_noise == 'wavelet':
            detail_coeffs = coeffs[-1]
            noise_level = np.std(detail_coeffs)
        elif estimate_noise == 'function':
            noise_level = estimate_sigma(image, average_sigmas=True, channel_axis=-1)
        denoised_image = denoise_wavelet(image, sigma=noise_level, wavelet=type, rescale_sigma=True, mode=mode, wavelet_levels=number_of_levels)
        return denoised_image
    
    def wavelet_processing_color(self, image, type, mode, number_of_levels, estimate_noise, sigma=None):
        """
        Подходит для цветных изображений.
        """
        channels = cv2.split(image)
        denoised_channels = []
        
        for channel in channels:
            denoised_channel = self.wavelet_processing(channel, type, mode, number_of_levels, estimate_noise, sigma)
            denoised_channels.append(denoised_channel)
        
        denoised_image = cv2.merge(denoised_channels)
        if denoised_image.dtype != np.uint8:
            denoised_image = cv2.normalize(denoised_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        return denoised_image
    
    def non_local_means(self, image, h=10, template_window_size=7, search_window_size=21):
        denoised_image = cv2.fastNlMeansDenoisingColored(image, None, h, h, template_window_size, search_window_size)
        return denoised_image
    

    # ================================================================================
    # ФУНКЦИИ ДЛЯ ИСПРАВЛЕНИЯ В ЦЕЛОМ
    # ================================================================================

    def __cv2_imread_unicode(self, path):
        """
        Аналог cv2.imread() с поддержкой Unicode-путей.
        """
        # создаем временный файл с ASCII-именем (в папке C:\Users\ВАШ_ПОЛЬЗОВАТЕЛЬ\AppData\Local\Temp)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            temp_path = tmp.name
        # копируем оригинальный файл во временный
        shutil.copy2(path, temp_path)
        # читаем временный файл
        img = cv2.imread(temp_path)
        # удаляем временный файл
        os.unlink(temp_path)
        return img

    def __cv2_imwrite_unicode(self, path, img):
        """
        Аналог cv2.imwrite() с поддержкой Unicode-путей.
        """
        # создаем временный файл
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            temp_path = tmp.name
        # сохраняем во временный файл
        cv2.imwrite(temp_path, img)
        # перемещаем в конечный путь с Unicode-именем
        shutil.move(temp_path, path)
        return True


    def process_image(self, image, processing_method, output_path=None, *args, **kwargs):
        """
        Обработка изображения.
        """
        # применение нужного метода
        processed_image = processing_method(image, *args, **kwargs)
        # если нужно, сохраняем обработанное изображение
        if output_path: cv2.imwrite(output_path, processed_image)
        return processed_image

    def determine_class(self, img):
        """
        Классификация.
        """
        img_height, img_width = 224, 224
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (img_height, img_width))
        img = img.astype('float32') / 255.0
        img = np.expand_dims(img, axis=0)

        prediction = self.model.predict(img, verbose=0)
        class_names = ['blur', 'contrast', 'glares', 'good', 'noise']
        predicted_class_index = np.argmax(prediction, axis=1)[0]
        predicted_class = class_names[predicted_class_index]
        predicted_property = prediction[0][predicted_class_index]

        return [predicted_class, predicted_property]

    def get_paths(self, image_name):
        """
        Возвращает исходный и выходной путь к изображению или кадру.
        """
        input_path = os.path.join(self.input_path, image_name)
        input_image_name_with_extension = os.path.basename(input_path)
        input_image_name, input_image_extension = os.path.splitext(input_image_name_with_extension)
        processed_image_name = input_image_name + 'processed' + input_image_extension
        output_path = os.path.join(self.output_path, processed_image_name)

        return (input_path, output_path)
    
    def automatic_recovery_image(self, input_image, defect_mode):
        """
        Автоматическое исправление изображения. Использует строго определенные методы
        для исправления каждого из дефектов.
        defect_mode - режим исправления дефектов, может принимать 2 значения:
            1. 'all_defects' - исправляет все дефекты на изображении
            2. 'one_defect' - исправляет 1, самый значимый дефект на изображении
        """
        def apply_methods():
            if predicted_class == 'blur': 
                processed_image = self.unsharp_masking(input_image)
            elif predicted_class == 'contrast': 
                processed_image = self.hist_equalization(input_image, 'yuv')
            elif predicted_class == 'glares': 
                processed_image = self.glares_inpaint(input_image)
            elif predicted_class == 'noise': 
                processed_image = self.adaptive_average_filter(input_image, estimate_noise='function')
            elif predicted_class == 'good':
                processed_image = input_image.copy()
            return processed_image

        if defect_mode == 'one_defect':
            predicted_class = self.determine_class(input_image)[0]
            processed_image = apply_methods()
        elif defect_mode == 'all_defects':
            defects_in_image = [] # список дефектов на картинке
            processed_image = input_image.copy()
            while True:
                predicted_class = self.determine_class(processed_image)[0]
                if predicted_class in defects_in_image:
                    break

                if predicted_class == 'good':
                    break
                else:
                    defects_in_image.append(predicted_class)

                processed_image = apply_methods()

        return processed_image

        # return processed_image
    
    def manual_recovery_image(self, input_image, methods, defect_mode):
        """
        Ручное исправление изображения. Использует методы и параметры, определенные пользователем.
        Принимает их в виде словаря.

        methods = {
            'blur': {
                'method': blur_method
                'params': {
                    'param1': value1,
                    'param2': value2
                }
            }, 
            ...
        }
        """
        # input_path, output_path = self.get_paths(image_name)

        # input_image = cv2.imread(input_image_path)
        def apply_methods(predicted_class):
            method_data = methods.get(predicted_class)
            if method_data:
                method = method_data['method']
                params = method_data['params']
                processed_image = method(**params)
            return processed_image
        
        if defect_mode == 'one_defect':
            predicted_class = self.determine_class(input_image)[0]
            processed_image = apply_methods(predicted_class)
        elif defect_mode == 'all_defects':
            defects_in_image = [] # список дефектов на картинке
            processed_image = input_image.copy()
            while True:
                predicted_class = self.determine_class(processed_image)[0]
                if predicted_class in defects_in_image:
                    break

                if predicted_class == 'good':
                    break
                else:
                    defects_in_image.append(predicted_class)
                
                processed_image = apply_methods(predicted_class)

        # cv2.imwrite(output_image_path, processed_image)

        return processed_image
    
    def recovery_image(self, processing_mode, defect_mode, methods=None):
        """
        Восстановление изображения.
        """
        try:
            input_image = self.__cv2_imread_unicode(self.input_path)
            if input_image is None: return None

            if processing_mode == 'automatic':
                processed_image = self.automatic_recovery_image(input_image, defect_mode)
            elif processing_mode == 'manual':
                processed_image = self.manual_recovery_image(input_image, methods, defect_mode)

            # формируем необходимое название для сохранения
            original_filename = os.path.basename(self.input_path)
            name, ext = os.path.splitext(original_filename)
            processed_filename = f"processed_{name}{ext}"
            processed_path = os.path.join(self.output_path, processed_filename)

            if self.__cv2_imwrite_unicode(processed_path, processed_image):
                return processed_path
        except:
            return None
        
    def recovery_video(self, processing_mode, defect_mode, methods=None):
        """
        Восстановление видео.
        """
        try:
            print(1)
            # формируем необходимое название для сохранения
            video_name = Path(self.input_path).stem
            processed_video_name = f"processed_{video_name}.mp4"
            processed_video_path = str(Path(self.output_path) / processed_video_name)
            
            print(2)
            # открываем видео
            cap = cv2.VideoCapture(self.input_path)
            if not cap.isOpened():
                return None
            
            print(3)
            # получаем параметры видео
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(4)
            # создаем VideoWriter для сохранения результата
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height))
            
            print(5)
            # обрабатываем каждый кадр
            while True:
                print(6)
                ret, frame = cap.read()
                if not ret:
                    break
                
                # конвертируем BGR (OpenCV) в RGB (для методов обработки)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # применяем выбранный метод обработки
                if processing_mode == 'automatic':
                    processed_frame = self.automatic_recovery_image(rgb_frame, defect_mode)
                elif processing_mode == 'manual':
                    processed_frame = self.manual_recovery_image(rgb_frame, methods, defect_mode)
                
                # конвертируем обратно в BGR для сохранения
                bgr_frame = cv2.cvtColor(processed_frame, cv2.COLOR_RGB2BGR)
                out.write(bgr_frame)
            
            print(7)
            # освобождаем ресурсы
            cap.release()
            out.release()
            
            print(8)
            return processed_video_path
        
        except Exception as e:
            return None

    # def recovery_video(self, processing_mode, defect_mode, methods=None):
    #     """
    #     Восстановление видео с улучшенной обработкой ошибок и выводом прогресса.
    #     """
    #     try:
    #         print("[1/8] Подготовка путей...")
    #         video_name = Path(self.input_path).stem
    #         processed_video_name = f"processed_{video_name}.mp4"
    #         processed_video_path = str(Path(self.output_path) / processed_video_name)
            
    #         print("[2/8] Открытие видео...")
    #         cap = cv2.VideoCapture(self.input_path)
    #         if not cap.isOpened():
    #             print("Ошибка: не удалось открыть видео")
    #             return None
            
    #         print("[3/8] Получение параметров видео...")
    #         fps = cap.get(cv2.CAP_PROP_FPS)
    #         width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    #         height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    #         total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
    #         print(f"[4/8] Создание VideoWriter (FPS: {fps}, Размер: {width}x{height})...")
    #         fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    #         out = cv2.VideoWriter(processed_video_path, fourcc, fps, (width, height))
    #         if not out.isOpened():
    #             print("Ошибка: не удалось создать выходной файл")
    #             cap.release()
    #             return None
            
    #         print(f"[5/8] Начало обработки {total_frames} кадров...")
    #         frame_count = 0
    #         last_percent = -1
            
    #         while True:
    #             ret, frame = cap.read()
    #             if not ret:
    #                 break
                
    #             frame_count += 1
    #             percent = int((frame_count / total_frames) * 100)
                
    #             # Выводим прогресс только при изменении процента
    #             if percent != last_percent and percent % 5 == 0:
    #                 print(f"Обработка: {percent}% ({frame_count}/{total_frames})")
    #                 last_percent = percent
                
    #             try:
    #                 rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
    #                 if processing_mode == 'automatic':
    #                     processed_frame = self.automatic_recovery_image(rgb_frame, defect_mode)
    #                 elif processing_mode == 'manual':
    #                     processed_frame = self.manual_recovery_image(rgb_frame, methods, defect_mode)
    #                 else:
    #                     print("Неизвестный режим обработки")
    #                     break
                    
    #                 bgr_frame = cv2.cvtColor(processed_frame, cv2.COLOR_RGB2BGR)
    #                 out.write(bgr_frame)
                    
    #             except Exception as frame_error:
    #                 print(f"Ошибка при обработке кадра {frame_count}: {frame_error}")
    #                 continue
            
    #         print("[6/8] Завершение обработки...")
    #         cap.release()
    #         out.release()
            
    #         print("[7/8] Проверка результата...")
    #         if Path(processed_video_path).exists():
    #             print(f"[8/8] Видео успешно сохранено: {processed_video_path}")
    #             return processed_video_path
    #         else:
    #             print("Ошибка: выходной файл не создан")
    #             return None
                
    #     except Exception as e:
    #         print(f"Критическая ошибка: {e}")
    #         return None
    
    def recovery_dataset(self, processing_mode, defect_mode, methods=None):
        """
        Восстановление датасета.
        """
        try:
            # создаем папку для сохранения датасета по указанному пути
            input_folder_name = Path(self.input_path).name
            processed_folder_name = f"processed_{input_folder_name}"
            processed_folder_path = Path(self.output_path) / processed_folder_name
            processed_folder_path.mkdir(parents=True, exist_ok=True)

            images = os.listdir(self.input_path)
            for image_name in images:
                input_image_path = os.path.join(self.input_path, image_name)
                output_image_path = os.path.join(processed_folder_path, image_name)

                input_image = self.__cv2_imread_unicode(self.input_path)
                if input_image is None: return None

                if processing_mode == 'automatic':
                    processed_image = self.automatic_recovery_image(input_image, defect_mode)
                elif processing_mode == 'manual':
                    processed_image = self.manual_recovery_image(input_image, methods, defect_mode)

                # формируем необходимое название для сохранения
                original_filename = os.path.basename(input_image_path)
                name, ext = os.path.splitext(original_filename)
                processed_filename = f"processed_{name}{ext}"
                processed_path = os.path.join(output_image_path, processed_filename)

                if not self.__cv2_imwrite_unicode(processed_path, processed_image):
                    return None
            return processed_folder_path
        except:
            return None