from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtWidgets import QFileDialog, QGraphicsScene, QGraphicsPixmapItem
import cv2
import numpy as np
from add_noise import add_gaussian_noise, add_salt_pepper_noise, add_uniform_noise
from apply_filter import apply_average_filter, apply_gaussian_filter, apply_median_filter
from Histogram_Equalization import HistogramEqualization
from Thresholding import Thresholding
from RGB2GRAY import RGB2GRAY
from RGB_Hist import RGB_Hist
from Freq_filters import Freq_filters
from Hybrid import Hybrid
import matplotlib.pyplot as plt

# ui_names:
# - image1
# - output_image
# - apply_noise_btn
# - apply_filter_btn
# - noise_type_combo
# - filter_combo
# - kernel_size_slider
# - kernel_size_label
# - convert_to_grayscale_btn
# - equalize_image_btn
# - edge_detection_method_combo
# - detect_edges_btn
# - histogram_1
# - histogram_2
# - image1_mix
# - image2_mix
# - output_img_mix
# - mix_btn


class UIHandler:
    def __init__(self, main_window):
        self.main_window = main_window
        uic.loadUi(r'ui_2.ui', self.main_window)
        self.image_label = self.main_window.findChild(
            QtWidgets.QLabel, 'image1')
        self.output_image_view = self.main_window.findChild(
            QtWidgets.QGraphicsView, 'output_image')
        self.original_histogram = self.main_window.findChild(QtWidgets.QGraphicsView, 'histogram_1')
        self.equalized_histogram = self.main_window.findChild(QtWidgets.QGraphicsView, 'histogram_2')
        self.image_label.setAlignment(Qt.AlignCenter)

        self.image_label.mouseDoubleClickEvent = self.open_image
        self.main_window.apply_noise_btn.clicked.connect(self.apply_noise)
        self.main_window.apply_filter_btn.clicked.connect(self.apply_filter)
        self.main_window.kernel_size_slider.valueChanged.connect(
            self.update_kernel_size)
        self.main_window.kernel_size_slider.setValue(3)
        self.main_window.noise_intensity_slider.valueChanged.connect(lambda: self.main_window.noise_intensity_label.setText(
            f"{self.main_window.noise_intensity_slider.value()}"))
        self.image = None
        self.gray_image = None
        self.main_window.equalize_image_btn.clicked.connect(self.equalize_image)
        self.kernel_size = 3

    def open_image(self, event):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_window, "Select Image", "", "Image Files (*.png *.jpg *.bmp)", options=options)
        if file_name:
            pixmap = QPixmap(file_name)
            # Preserve aspect ratio in QLabel
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.image_label.setScaledContents(False)

            self.image = cv2.imread(file_name, cv2.IMREAD_COLOR)
            self.gray_image = cv2.imread(file_name, cv2.IMREAD_GRAYSCALE)

    def update_kernel_size(self):
        self.kernel_size = self.main_window.kernel_size_slider.value()
        self.main_window.kernel_size_label.setText(f"{self.kernel_size}")

    def apply_noise(self):
        # print('Applying noise')
        if self.image is None:
            return

        noise_type = self.main_window.noise_type_combo.currentText()
        noise_intensity = self.main_window.noise_intensity_slider.value()
        if noise_type == 'guassian noise':
            noisy_image = add_gaussian_noise(self.image, sigma=noise_intensity)
        elif noise_type == 'salt and pepper noise':
            noisy_image = add_salt_pepper_noise(self.image , salt_prob=noise_intensity/100, pepper_prob=noise_intensity/100)
        elif noise_type == 'uniform noise':
            noisy_image = add_uniform_noise(self.image , intensity=noise_intensity)
        else:
            return

        self.display_image(self.output_image_view, noisy_image)

    def apply_filter(self):
        if self.image is None:
            return
        filter_type = self.main_window.filter_combo.currentText()
        if filter_type == 'average filter':
            filtered_image = apply_average_filter(self.image, self.kernel_size)
        elif filter_type == 'gaussian filter':
            filtered_image = apply_gaussian_filter(
                self.image, self.kernel_size)
        elif filter_type == 'median filter':
            filtered_image = apply_median_filter(self.image, self.kernel_size)
        else:
            return
        self.display_image(self.output_image_view, filtered_image)

    def display_image(self, view, image):
        pixmap = self.convert_cv_to_pixmap(image)
        scene = QGraphicsScene()
        scene.addPixmap(pixmap)
        view.setScene(scene)
        view.fitInView(
            scene.itemsBoundingRect(), Qt.KeepAspectRatio)

        

    def plot_histogram(self, data):
        fig, ax = plt.subplots(figsize=(5, 4), dpi=150)
        ax.plot(data, color='blue')  # Black color for grayscale consistency
        ax.set_title('Histogram')
        ax.set_xlabel('Pixel Intensity')
        ax.set_ylabel('Frequency')
        fig.canvas.draw()
        width, height = fig.canvas.get_width_height()
        img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(height, width, 3)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # Convert to grayscale
        
        plt.close(fig)  # Close the figure to prevent memory leaks
        return img

    def convert_cv_to_pixmap(self, cv_img):
        """ Converts an OpenCV image to QPixmap (automatically detects grayscale or RGB) """
        if len(cv_img.shape) == 2:  # Grayscale
            height, width = cv_img.shape
            bytes_per_line = width
            q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        else:  # RGB
            height, width, channel = cv_img.shape
            bytes_per_line = 3 * width
            q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        
        return QPixmap.fromImage(q_img)

    def equalize_image(self):
        histogram, equalized_hist, new_image = HistogramEqualization.equalize(self.gray_image)
        # Plot histograms as images
        hist_pixmap = self.plot_histogram(histogram)
        equalized_hist_pixmap = self.plot_histogram(equalized_hist)

        # Display in respective QGraphicsView widgets
        self.display_image(self.original_histogram, hist_pixmap)
        self.display_image(self.equalized_histogram, equalized_hist_pixmap)
        self.display_image(self.output_image_view, new_image)

    def convert_to_grayscale(self, image):
        if len(image.shape) == 3:
            gray_image = RGB2GRAY.convert_to_grayscale(image)
        
        return gray_image
    
    def apply_thresholding(self, image, threshold_value, window_size, sensitivity, type):
        gray_image = self.convert_to_grayscale(image)

        if type == 'global':
            image = Thresholding.global_thresholding(gray_image, threshold_value)

        elif type == 'local':
            image = Thresholding.local_thresholding(gray_image, window_size, sensitivity)
        
        else:
            return

        # diplay the thresholded image

    def apply_frequency_filters(self, image, filter_type, D0):
        image = cv2.resize(image, (256, 256))

        # Convert image to float32 for FFT processing
        image = np.float32(image)

        # Center the image by multiplying with (-1)^(x+y)
        rows, cols = image.shape
        x = np.arange(rows)
        y = np.arange(cols)
        X, Y = np.meshgrid(y, x)
        centered_data = image * ((-1) ** (X + Y))

        # Apply 2D DFT
        F = Freq_filters.DFT_2D(centered_data)

        # Create a filter
        H = Freq_filters.create_filter(rows, cols, D0, filter_type)

        # Apply the filter
        G = Freq_filters.apply_filter(F, H)

        # Apply inverse DFT
        g = Freq_filters.IDFT_2D(G)

        # Re-center the image
        recentered_data = g * ((-1) ** (X + Y))

        # Normalize the image data
        normalized_image = Freq_filters.normalize_image(recentered_data)

        # Convert the normalized image to uint8
        image = np.array(normalized_image, dtype=np.uint8)

        # display the image

    def hybrid_image(self, image1, image2):
        # Resize images to the same dimensions
        image1 = cv2.resize(image1, (256, 256))
        image2 = cv2.resize(image2, (256, 256))

        image1 = np.float32(image1)
        image2 = np.float32(image2)

        # Extract frequency components
        low_frequencies = Hybrid.extract_low_frequencies(image1)
        high_frequencies = Hybrid.extract_high_frequencies(image2)

        # Combine frequencies
        hybrid_image = Hybrid.combine_frequencies(low_frequencies, high_frequencies)

        hybrid_image = np.array(hybrid_image, dtype=np.uint8)

        # display hybrid image