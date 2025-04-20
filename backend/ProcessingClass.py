import cv2
import matplotlib.pyplot as plt
import os
import tensorflow as tf  
from ultralytics import YOLO
# from tensorflow.keras.preprocessing import image
import numpy as np
import pywt
from skimage.restoration import (denoise_wavelet, estimate_sigma)
from itertools import product
from pathlib import Path
import tempfile
import shutil

class ProcessingClass:
    # def __init__(self, input_path, model_path, yolo_raw_path, yolo_best_path, output_path):
    def __init__(self, model_path, yolo_raw_path, yolo_best_path, output_path):
        # self.input_path = input_path
        self.model_path = model_path
        self.yolo_raw_path = yolo_raw_path
        self.yolo_best_path = yolo_best_path
        self.output_path = output_path
        # self.processing_mode = processing_mode

        self.model = tf.keras.models.load_model(self.model_path)
        self.yolo_raw_model = YOLO(self.yolo_raw_path)
        self.yolo_best_model = YOLO(self.yolo_best_path)

        self.__auto_methods = {
            'blur': {
                'defect_name': 'Размытие',
                'methods': {
                    'no_process': {
                        'method_name': 'Не исправлять',
                        'link': None,
                        'checked': True,
                        'params': None
                    }
                }
            },
            'contrast': {
                'defect_name': 'Контрастность',
                'methods': {
                    'hist_equalization': {
                        'method_name': 'Гистограммное выравнивание',
                        'link': self.hist_equalization,
                        'checked': True,
                        'params': {
                            'color_space_hist': 'hsv'
                        }
                    }
                }
            },
            'glares': {
                'defect_name': 'Блики',
                'methods': {
                    'no_process': {
                        'method_name': 'Не исправлять',
                        'link': None,
                        'checked': True,
                        'params': None
                    }
                }
            },
            'noise': {
                'defect_name': 'Шум',
                'methods': {
                    'adaptive_average_filter': {
                        'method_name': 'Фильтр среднего значения',
                        'link': self.adaptive_average_filter,
                        'checked': True,
                        'params': {
                            'estimate_noise': 'gaussian',
                            'sigma': 5
                        }
                    }
                }
            }
        }

        self.__manual_methods = {
            'blur': {
                'defect_name': 'Размытие',
                'methods': {
                    'no_process': {
                        'method_name': 'Не исправлять',
                        'link': None,
                        'checked': False,
                        'params': None
                    },
                    'unsharp_masking': {
                        'method_name': 'Повышение резкости',
                        'link': self.unsharp_masking,
                        'checked': True,
                        'params': {
                            'sigma': 3, 
                            'alpha': 5.5, 
                            'betta': -4.5
                        }
                    },
                    'laplacian_sharpening': {
                        'method_name': 'Фильтр Лапласа',
                        'link': self.laplacian_sharpening,
                        'checked': False,
                        'params': {
                            'coeff': 6
                        }
                    }
                }
            },
            'contrast': {
                'defect_name': 'Контрастность',
                'methods': {
                    'no_process': {
                        'method_name': 'Не исправлять',
                        'link': None,
                        'checked': False,
                        'params': None
                    },
                    'hist_equalization': {
                        'method_name': 'Гистограммное выравнивание',
                        'link': self.hist_equalization,
                        'checked': True,
                        'params': {
                            'color_space_hist': 'hsv'
                        }
                    },
                    'clahe_algorithm': {
                        'method_name': 'Алгоритм CLAHE',
                        'link': self.clahe_algorithm,
                        'checked': False,
                        'params': {
                            'color_space_hist': 'hsv',
                            'clip_limit': 6.5,
                            'tile_grid_size': (12, 12)
                        }
                    }
                }
            },
            'glares': {
                'defect_name': 'Блики',
                'methods': {
                    'no_process': {
                        'method_name': 'Не исправлять',
                        'link': None,
                        'checked': False,
                        'params': None
                    },
                    'glares_inpaint': {
                        'method_name': 'Простое восстановление',
                        'link': self.glares_inpaint,
                        'checked': True,
                        'params': {
                            'mask_mode': 'brightness',
                            'color_space_mask': 'hsv',
                            'color_space': 'yuv',
                            'threshold': 160,
                            'inpaint_radius': 3,
                            'flags': 'inpaint_ns',
                            'gradient_method': 'sobel',
                            'gradient_threshold': 100
                        }
                    },
                    'adaptive_glares_inpaint': {
                        'method_name': 'Адаптивное восстановление',
                        'link': self.adaptive_glares_inpaint,
                        'checked': False,
                        'params': {
                            'mask_mode': 'brightness',
                            'color_space_mask': 'hsv',
                            'color_space': 'yuv',
                            'adaptive_method': 'gaussian',
                            'block_size': 7,
                            'C': 5,
                            'inpaint_radius': 3,
                            'flags': 'inpaint_ns',
                            'gradient_method': 'sobel',
                            'gradient_threshold': 100
                        }
                    }
                }
            },
            'noise': {
                'defect_name': 'Шум',
                'methods': {
                    'no_process': {
                        'method_name': 'Не исправлять',
                        'link': None,
                        'checked': False,
                        'params': None
                    },
                    'adaptive_average_filter': {
                        'method_name': 'Фильтр среднего значения',
                        'link': self.adaptive_average_filter,
                        'checked': True,
                        'params': {
                            'estimate_noise': 'gaussian',
                            'sigma': 5
                        }
                    },
                    'adaptive_median_filter': {
                        'method_name': 'Медианный фильтр',
                        'link': self.adaptive_median_filter,
                        'checked': False,
                        'params': {
                            'estimate_noise': 'gaussian',
                            'sigma': 5
                        }
                    },
                    'adaptive_gaussian_filter': {
                        'method_name': 'Фильтр Гаусса',
                        'link': self.adaptive_gaussian_filter,
                        'checked': False,
                        'params': {
                            'estimate_noise': 'gaussian',
                            'sigma': 5
                        }
                    },
                    'wavelet_processing_color': {
                        'method_name': 'Вейвлет-обработка',
                        'link': self.wavelet_processing_color,
                        'checked': False,
                        'params': {
                            'wavelet_type': 'haar',
                            'wavelet_mode': 'hard',
                            'number_of_levels': 3,
                            'wavelet_estimate_noise': 'function',
                            'sigma': 3
                        }
                    },
                    'non_local_means': {
                        'method_name': 'Нелокальное среднее',
                        'link': self.non_local_means,
                        'checked': False,
                        'params': {
                            'h': 10,
                            'template_window_size': 7,
                            'search_window_size': 21
                        }
                    },
                }
            }
        }

        self.__allowed_params_values = {
            'color_space_hist': ['hsv', 'yuv'],
            'color_space': ['hsv', 'rgb', 'yuv'],
            'mask_mode': ['brightness', 'gradient', 'combine'],
            'color_space_mask': ['hsv', 'gray', 'yuv'],
            'flags': ['inpaint_ns', 'inpaint_telea'],
            'gradient_method': ['sobel', 'scharr', 'laplacian'],
            'adaptive_method': ['gaussian', 'mean'],
            'estimate_noise': ['function', 'gaussian'], 
            'wavelet_type': ['haar', 'db2', 'db4', 'sym2', 'bior1.3'],
            'wavelet_mode': ['hard', 'soft'],
            'wavelet_estimate_noise': ['function', 'gaussian', 'wavelet'],
        }

    def set_input_path(self, input_path):
        self.input_path = input_path

    def get_input_path(self):
        return self.input_path
    
    def cleanup(self):
        """
        Явное освобождение ресурсов.
        """
        if hasattr(self, 'model'):
            del self.model

    def get_allowed_params(self):
        return self.__allowed_params_values
    
    def get_auto_methods(self):
        return self.__auto_methods
    
    def get_manual_methods(self):
        return self.__manual_methods
    
    def set_manual_methods(self, manual_methods):
        self.__manual_methods = manual_methods

    # ================================================================================
    # ФУНКЦИИ ДЛЯ ИСПРАВЛЕНИЯ РАЗМЫТЫХ ИЗОБРАЖЕНИЙ
    # ================================================================================

    def unsharp_masking(self, image, sigma=3, alpha=2.5, betta=-1.5):
        """
        Восстановление путем вычитания размытого из исходного.
        На вход подается исходное, которое размыто,
        оно размывается еще больше, и разность между размытым и совсем размытым сохраняется.
        Затем разность прибавляется к исходному размытому - для увеличения резкости.
        Принимает коэффициенты: положительный и отрицательный. Их сумма должна быть равна 1.
        """
        print('unsharp_masking')
        blurred_image = cv2.GaussianBlur(image, (0, 0), sigmaX=sigma)
        sharpened_image = cv2.addWeighted(image, alpha, blurred_image, betta, 0)
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

    def hist_equalization(self, image, color_space_hist):
        """
        Выполняет гистограммное выравнивание - сначала преобразует картинку в нужное цветовое пространство, 
        а затем применяет преобразование лишь к каналу яркости.
        """
        if color_space_hist == 'yuv':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            channels = list(cv2.split(converted_image))
            index = 0  # Y-канал (яркость)
        elif color_space_hist == 'hsv':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            channels = list(cv2.split(converted_image))
            index = 2  # V-канал (яркость)

        channels[index] = cv2.equalizeHist(channels[index])
        image_hist = cv2.merge(channels)
        if color_space_hist == 'yuv':
            image_hist = cv2.cvtColor(image_hist, cv2.COLOR_YUV2BGR)
        elif color_space_hist == 'hsv':
            image_hist = cv2.cvtColor(image_hist, cv2.COLOR_HSV2BGR)

        return image_hist
    
    def clahe_algorithm(self, image, color_space_hist, clip_limit, tile_grid_size):
        """
        Разбивает изображение на квадраты, и выполняет гистограммное выравнивание внутри каждого
        а перед этим еще в соответствии с clip_limit выбросы гистограммы обрезаются и раскидываются 
        по остальным столбикам.
        """
        print('clahe')
        if color_space_hist == 'yuv':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            channels = list(cv2.split(converted_image))
            index = 0  # Y-канал (яркость)
        elif color_space_hist == 'hsv':
            converted_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            channels = list(cv2.split(converted_image))
            index = 2  # V-канал (яркость)

        clahe = cv2.createCLAHE(clip_limit, tile_grid_size)
        channels[index] = clahe.apply(channels[index])

        image_clahe = cv2.merge(channels)
        if color_space_hist == 'yuv':
            image_clahe = cv2.cvtColor(image_clahe, cv2.COLOR_YUV2BGR)
        elif color_space_hist == 'hsv':
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
        flags='inpaint_ns', #cv2.INPAINT_NS,
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

        print('color_space_mask', color_space_mask, 'color_space', color_space, 'threshold', threshold, 'inpaint_radius',
              inpaint_radius, 'flags', flags, 'mask_mode', mask_mode, 'gradient_method', gradient_method, 'gradient_threshold',
              gradient_threshold)

        if flags == 'inpaint_ns': inpaint_mode = cv2.INPAINT_NS
        elif flags == 'inpaint_telea': inpaint_mode = cv2.INPAINT_TELEA

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
            inpaint_image = cv2.inpaint(image, mask, inpaintRadius=inpaint_radius, flags=inpaint_mode)
        else:
            if color_space == 'yuv':
                img_converted = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
                img_channels = list(cv2.split(img_converted))
            elif color_space == 'hsv':
                img_converted = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                img_channels = list(cv2.split(img_converted))
            elif color_space == 'gray':
                img_channels = [cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)]
                
            bright_channel_idx = 0 if color_space == 'yuv' else 2 if color_space == 'hsv' else 0
            img_channels[bright_channel_idx] = cv2.inpaint(
                img_channels[bright_channel_idx], 
                mask, 
                inpaintRadius=inpaint_radius, 
                flags=inpaint_mode
            )

            # Собираем обратно
            inpaint_image = cv2.merge(img_channels)
            if color_space == 'yuv':
                inpaint_image = cv2.cvtColor(inpaint_image, cv2.COLOR_YUV2BGR)
            elif color_space == 'hsv':
                inpaint_image = cv2.cvtColor(inpaint_image, cv2.COLOR_HSV2BGR)
            elif color_space == 'gray':
                inpaint_image = cv2.cvtColor(inpaint_image, cv2.COLOR_GRAY2BGR)

        return inpaint_image
    
    def adaptive_glares_inpaint(
        self,
        image, 
        color_space_mask='gray', 
        color_space='rgb', 
        adaptive_method='gaussian', #cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        block_size=11, 
        C=2, 
        inpaint_radius=3, 
        flags='inpaint_ns', #cv2.INPAINT_NS,
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

        if flags == 'inpaint_ns': inpaint_mode = cv2.INPAINT_NS
        elif flags == 'inpaint_telea': inpaint_mode = cv2.INPAINT_TELEA

        if adaptive_method == 'gaussian': adaptive_mode = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        elif adaptive_method == 'mean': adaptive_mode = cv2.ADAPTIVE_THRESH_MEAN_C

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
                adaptive_mode, 
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
            inpaint_image = cv2.inpaint(image, mask, inpaintRadius=inpaint_radius, flags=inpaint_mode)
        else:
            if color_space == 'yuv':
                img_converted = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
                img_channels = list(cv2.split(img_converted))
            elif color_space == 'hsv':
                img_converted = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                img_channels = list(cv2.split(img_converted))
            elif color_space == 'gray':
                img_channels = [cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)]

            bright_channel_idx = 0 if color_space == 'yuv' else 2 if color_space == 'hsv' else 0
            img_channels[bright_channel_idx] = cv2.inpaint(
                img_channels[bright_channel_idx], 
                mask, 
                inpaintRadius=inpaint_radius, 
                flags=inpaint_mode
            )

            inpaint_image = cv2.merge(img_channels)
            if color_space == 'yuv':
                inpaint_image = cv2.cvtColor(inpaint_image, cv2.COLOR_YUV2BGR)
            elif color_space == 'hsv':
                inpaint_image = cv2.cvtColor(inpaint_image, cv2.COLOR_HSV2BGR)
            elif color_space == 'gray':
                inpaint_image = cv2.cvtColor(inpaint_image, cv2.COLOR_GRAY2BGR)

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
    
    def wavelet_processing_color(self, image, wavelet_type, wavelet_mode, number_of_levels, wavelet_estimate_noise, sigma=None):
        """
        Подходит для цветных изображений.
        """
        channels = cv2.split(image)
        denoised_channels = []
        
        for channel in channels:
            denoised_channel = self.wavelet_processing(channel, wavelet_type, wavelet_mode, number_of_levels, wavelet_estimate_noise, sigma)
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

    def recovery(self, input_image, processing_mode, defect_mode):
        print('recovery')

        # словарь с результатами
        results = {
            'blur': [0, 0],
            'contrast': [0, 0],
            'glares': [0, 0],
            'noise': [0, 0]
        }

        # применение методов
        def apply_methods(predicted_class):
            print('apply_methods')
            print(predicted_class)
            # определяем, каким словарем будем пользоваться
            if processing_mode == 'automatic':
                methods = self.__auto_methods
            elif processing_mode == 'manual':
                methods = self.__manual_methods
            
            # все методы по данному дефекту
            defect_methods = methods[predicted_class]['methods']
            # находим метод, который выбран и применяем его
            for defect_method_key, defect_method_content in defect_methods.items():
                if defect_method_content['checked']:
                    print(defect_method_content)
                    if defect_method_key == 'no_process':
                        return input_image.copy()
                    defect_method_link = defect_method_content['link']
                    params = defect_method_content['params']
                    print(params)
                    processed_image = defect_method_link(input_image, **params)

            return processed_image

        if defect_mode == 'one_defect':
            print(1)
            predicted_class = self.determine_class(input_image)[0]
            print(2)
            if predicted_class != 'good': 
                results[predicted_class][0] += 1
                processed_image = apply_methods(predicted_class)
                processed_predicted_class = self.determine_class(processed_image)[0]
                if processed_predicted_class == 'good': results[predicted_class][1] += 1
            else: processed_image = input_image.copy()

        elif defect_mode == 'all_defects':
            defects_in_image = [] # список дефектов на картинке
            processed_image = input_image.copy()
            
            while True:
                uncorrected_defect = ''
                predicted_class = self.determine_class(processed_image)[0]
                if predicted_class in defects_in_image:
                    uncorrected_defect = predicted_class
                    break

                if predicted_class == 'good':
                    break
                else:
                    defects_in_image.append(predicted_class)
                    results[predicted_class][0] += 1

                processed_image = apply_methods(predicted_class)

            # все дефекты на картинке, которые есть в списке дефектов, исправлены,
            # кроме того дефекта, который возник еще раз (uncorrected_defect)
            for defect in defects_in_image:
                if defect != uncorrected_defect:
                    results[defect][1] += 1
        
        return (processed_image, results)
    
    def recovery_image(self, processing_mode, defect_mode, methods=None):
        """
        Восстановление изображения.
        """
        try:
            print('recovery_image')
            
            input_image = self.__cv2_imread_unicode(self.input_path)
            if input_image is None: return None, None

            processed_image, result = self.recovery(input_image, processing_mode, defect_mode)

            # формируем необходимое название для сохранения
            original_filename = os.path.basename(self.input_path)
            name, ext = os.path.splitext(original_filename)
            processed_filename = f"processed_{name}{ext}"
            self.processed_path = os.path.join(self.output_path, processed_filename)

            if self.__cv2_imwrite_unicode(self.processed_path, processed_image):
                return self.processed_path, result
        except:
            return None, None
        
    def recovery_video(self, processing_mode, defect_mode, methods=None):
        """
        Восстановление видео.
        """
        try:
            # словарь с результатами
            main_results = {
                'blur': [0, 0],
                'contrast': [0, 0],
                'glares': [0, 0],
                'noise': [0, 0]
            }

            print(1)
            # формируем необходимое название для сохранения
            video_name = Path(self.input_path).stem
            processed_name = f"processed_{video_name}.mp4"
            self.processed_path = str(Path(self.output_path) / processed_name)
            
            print(2)
            # открываем видео
            cap = cv2.VideoCapture(self.input_path)
            if not cap.isOpened():
                return None, None
            
            print(3)
            # получаем параметры видео
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(4)
            # создаем VideoWriter для сохранения результата
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.processed_path, fourcc, fps, (width, height))
            
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
                processed_frame, results = self.recovery(rgb_frame, processing_mode, defect_mode)
                
                # обновляем словарь с результатами
                main_results = {
                    key: [
                        main_results[key][0] + results[key][0], 
                        main_results[key][1] + results[key][1]
                    ] 
                    for key in main_results
                }
                
                # конвертируем обратно в BGR для сохранения
                bgr_frame = cv2.cvtColor(processed_frame, cv2.COLOR_RGB2BGR)
                out.write(bgr_frame)

                print('main_results', main_results)
            
            print(7)
            # освобождаем ресурсы
            cap.release()
            out.release()

            print('main_results', main_results)
            
            print(8)
            return (self.processed_path, main_results)
        
        except Exception as e:
            return None, None
    
    def recovery_dataset(self, processing_mode, defect_mode, methods=None):
        """
        Восстановление датасета.
        """
        try:
            # словарь с результатами
            main_results = {
                'blur': [0, 0],
                'contrast': [0, 0],
                'glares': [0, 0],
                'noise': [0, 0]
            }

            # создаем папку для сохранения датасета по указанному пути
            input_folder_name = Path(self.input_path).name
            processed_folder_name = f"processed_{input_folder_name}"
            self.processed_path = Path(self.output_path) / processed_folder_name
            self.processed_path.mkdir(parents=True, exist_ok=True)
            self.processed_path = str(self.processed_path)

            # получаем список имен изображений
            images = os.listdir(self.input_path)
            for image_name in images:
                input_image_path = os.path.join(self.input_path, image_name)
                output_image_path = os.path.join(self.processed_path, image_name)

                # загружаем изображение
                input_image = self.__cv2_imread_unicode(input_image_path)
                if input_image is None: return None, None

                # обрабатываем каждое изображение
                processed_image, results = self.recovery(input_image, processing_mode, defect_mode)

                # обновляем словарь с результатами
                main_results = {
                    key: [
                        main_results[key][0] + results[key][0], 
                        main_results[key][1] + results[key][1]
                    ] 
                    for key in main_results
                }

                # if not self.__cv2_imwrite_unicode(output_image_path, processed_image):
                #     return None
                if self.__cv2_imwrite_unicode(output_image_path, processed_image):
                    print('save')
                else:
                    return None, None
            
            print(self.processed_path, main_results)
            return (self.processed_path, main_results)
        except:
            return None, None
        
    
    # ================================================================================
    # ФУНКЦИИ ДЛЯ ДЕТЕКЦИИ ОБЪЕКТОВ
    # ================================================================================

    def detect_objects(self, image, detect_type, confidence_threshold):
        print('detect_objects')
        if detect_type == 'raw':
            model = self.yolo_raw_model
        elif detect_type == 'best':
            model = self.yolo_best_model

        print(11)

        result_image = image.copy()
        results = model(image)
        class_colors = [
            (255, 0, 0),    # Красный (класс 0)
            (0, 255, 255),    # Зеленый (класс 1)
            (0, 0, 255),    # Желтый (класс 2)
            (255, 255, 0),  # Голубой (класс 3)
            (255, 0, 255),  # Фиолетовый (класс 4)
            (0, 255, 0),  # Зеленый (класс 5)
            (128, 0, 0),    # Темно-красный (класс 6)
            (0, 128, 0),    # Темно-зеленый (класс 7)
            (0, 0, 128),    # Темно-синий (класс 8)
            (128, 128, 0),  # Оливковый (класс 9)
            (128, 0, 128),  # Пурпурный (класс 10)
            (0, 128, 128)   # Бирюзовый (класс 11)
        ]

        for result in results:
            print(12)
            boxes = result.boxes
            for box in boxes:
                print(13)
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                confidence = box.conf[0].item()
                class_id = box.cls[0].item()
                class_name = model.names[int(class_id)]
                print(14)

                if confidence >= confidence_threshold:
                    # рисуем прямоугольник
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    color = class_colors[int(class_id)]
                    thickness = 1
                    cv2.rectangle(result_image, (x1, y1), (x2, y2), color, thickness)
                    
                    # создаем подпись
                    label = f"{class_name}: {confidence:.2f}"
                    
                    # устанавливаем шрифт
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.3
                    text_thickness = 1
                    (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, text_thickness)
                    
                    # рисуем подложку для текста
                    cv2.rectangle(result_image, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)
                    
                    # рисуем текст
                    cv2.putText(result_image, label, (x1, y1 - 5), font, font_scale, (0, 0, 0), text_thickness)

                    print(15)        
        
        return result_image
    
    def detect_image(self, detect_type, confidence_threshold=0.55):
        """\
        Нахождение объектов на изображении.
        detect_type - тип изображения (модели): исходный или обработанный (raw, best).
        """
        print('detect_image')
        try:
            # определяем, какое изображение нужно размечать: исходное или исправленное
            if detect_type == 'raw':
                image = self.__cv2_imread_unicode(self.input_path)
            elif detect_type == 'best':
                image = self.__cv2_imread_unicode(self.processed_path) 
            if image is None: return None

            print(1)

            # распознаем объекты
            detected_image = self.detect_objects(image=image, detect_type=detect_type, confidence_threshold=confidence_threshold)

            print(2)

            # формируем необходимое название для сохранения
            original_filename = os.path.basename(self.input_path)
            name, ext = os.path.splitext(original_filename)
            if detect_type == 'raw': 
                processed_filename = f"detected_{name}{ext}"
            elif detect_type == 'best': 
                processed_filename = f"detected_processed_{name}{ext}"
            detected_path = os.path.join(self.output_path, processed_filename)

            print(3)

            if self.__cv2_imwrite_unicode(detected_path, detected_image):
                return detected_path
        except:
            return None
        
    def detect_video(self, detect_type, confidence_threshold=0.55):
        """
        Нахождение объектов на видео.
        detect_type - тип видео (модели): исходный или обработанный (raw, best).
        """
        try:
            print(1)
            # формируем необходимое название для сохранения
            video_name = Path(self.input_path).stem
            if detect_type == 'raw':
                detected_video_name = f"detected_{video_name}.mp4"
            elif detect_type == 'best':
                detected_video_name = f"detected_processed_{video_name}.mp4"
            detected_path = str(Path(self.output_path) / detected_video_name)
            
            print(2)
            # определяем, какое видео нужно размечать: исходное или исправленное
            if detect_type == 'raw':
                cap = cv2.VideoCapture(self.input_path)
            elif detect_type == 'best':
                cap = cv2.VideoCapture(self.processed_path)
            if not cap.isOpened(): return None
            
            print(3)
            # получаем параметры видео
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(4)
            # создаем VideoWriter для сохранения результата
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(detected_path, fourcc, fps, (width, height))
            
            print(5)
            # обрабатываем каждый кадр
            while True:
                print(6)
                ret, frame = cap.read()
                if not ret:
                    break
                
                # конвертируем BGR (OpenCV) в RGB (для методов обработки)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # распознаем объекты
                detected_frame = self.detect_objects(image=rgb_frame, detect_type=detect_type, confidence_threshold=confidence_threshold)
                
                # конвертируем обратно в BGR для сохранения
                bgr_frame = cv2.cvtColor(detected_frame, cv2.COLOR_RGB2BGR)
                out.write(bgr_frame)
            
            print(7)
            # освобождаем ресурсы
            cap.release()
            out.release()
            
            print(8)
            return detected_path
        
        except Exception as e:
            return None
        
    def detect_dataset(self, detect_type, confidence_threshold=0.55):
        """
        Поиск объектов на изображениях датасета.
        """
        try:
            # создаем папку для сохранения датасета по указанному пути
            if detect_type == 'raw':
                input_folder_path = self.input_path
                input_folder_name = Path(input_folder_path).name
                detected_folder_name = f"detected_{input_folder_name}"
            elif detect_type == 'best':
                input_folder_path = self.processed_path
                input_folder_name = Path(input_folder_path).name
                detected_folder_name = f"detected_processed_{input_folder_name}"
            detected_path = Path(self.output_path) / detected_folder_name
            detected_path.mkdir(parents=True, exist_ok=True)

            # получаем список имен изображений
            images = os.listdir(input_folder_path)
            for image_name in images:
                input_image_path = os.path.join(input_folder_path, image_name)
                output_image_path = os.path.join(detected_path, image_name)

                # загружаем изображение
                input_image = self.__cv2_imread_unicode(input_image_path)
                if input_image is None: return None

                # распознаем объекты
                detected_image = self.detect_objects(image=input_image, detect_type=detect_type, confidence_threshold=confidence_threshold)

                if not self.__cv2_imwrite_unicode(output_image_path, detected_image):
                    return None
            
            return detected_path
        except:
            return None
    