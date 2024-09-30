import os
import time
from PyQt5.QtWidgets import (
    QDialog, QPushButton, QVBoxLayout, QLineEdit, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem
)
from PyQt5.QtGui import QPixmap, QImage, QColor, QPainter
from PyQt5.QtCore import pyqtSignal, Qt, QRectF


class CanvasWindow(QDialog):
    save_signal = pyqtSignal()
    close_signal = pyqtSignal()

    def __init__(self, input_image):
        super().__init__()

        self.setWindowTitle("PyQt5 Image Canvas")
        self.input_image = input_image
        self.canvas_width = 512
        self.canvas_height = 512
        self.modified_image = None

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("border: 1px solid black;")
        self.view.setFixedSize(self.canvas_width + 2, self.canvas_height + 2)

        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.canvas = QImage(self.canvas_width, self.canvas_height, QImage.Format_RGB888)
        self.canvas.fill(QColor('white'))

        self.canvas_pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(self.canvas))
        self.scene.addItem(self.canvas_pixmap_item)

        scaled_pixmap = QPixmap.fromImage(self.input_image).scaled(
            self.canvas_width, self.canvas_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.input_pixmap_item = ResizablePixmapItem(scaled_pixmap, self.canvas_width, self.canvas_height)
        self.scene.addItem(self.input_pixmap_item)

        save_button = QPushButton("Save and Close", self)
        save_button.clicked.connect(self.save_and_close)

        self.canvas_width_input = QLineEdit(self)
        self.canvas_width_input.setPlaceholderText("Canvas Width")
        self.canvas_width_input.setText(str(self.canvas_width))
        self.canvas_height_input = QLineEdit(self)
        self.canvas_height_input.setPlaceholderText("Canvas Height")
        self.canvas_height_input.setText(str(self.canvas_height))

        size_button = QPushButton("Set Canvas Size", self)
        size_button.clicked.connect(self.set_canvas_size)

        hbox = QHBoxLayout()
        hbox.addWidget(self.canvas_width_input)
        hbox.addWidget(self.canvas_height_input)
        hbox.addWidget(size_button)

        vbox = QVBoxLayout()
        vbox.addWidget(self.view)
        vbox.addLayout(hbox)
        vbox.addWidget(save_button)

        self.setLayout(vbox)

        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)
        self.view.setSceneRect(0, 0, self.canvas_width, self.canvas_height)

    def save_and_close(self):
        self.save_image()
        self.accept()

    def save_image(self):
        image = QImage(self.canvas_width, self.canvas_height, QImage.Format_RGB888)
        image.fill(QColor('white'))

        painter = QPainter(image)
        target_rect = QRectF(0, 0, self.canvas_width, self.canvas_height)
        source_rect = self.scene.sceneRect()
        self.scene.render(painter, target_rect, source_rect)
        painter.end()

        self.modified_image = image

        save_directory = os.path.join(os.getcwd(), "ComfyUI", "custom_nodes", "Comfyui_Snap-Processing", "save")
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        timestamp = int(time.time() * 1000)
        save_path = os.path.join(save_directory, "output.png")
        image.save(save_path)
        self.save_signal.emit()

    def closeEvent(self, event):
        self.close_signal.emit()
        event.accept()

    def set_canvas_size(self):
        try:
            width = int(self.canvas_width_input.text())
            height = int(self.canvas_height_input.text())
        except ValueError:
            return

        self.canvas_width = width
        self.canvas_height = height

        self.canvas = QImage(self.canvas_width, self.canvas_height, QImage.Format_RGB888)
        self.canvas.fill(QColor('white'))
        self.canvas_pixmap_item.setPixmap(QPixmap.fromImage(self.canvas))

        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)
        self.view.setSceneRect(0, 0, self.canvas_width, self.canvas_height)
        self.view.setFixedSize(self.canvas_width + 2, self.canvas_height + 2)

    def get_modified_image(self):
        return self.modified_image


class ResizablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, canvas_width, canvas_height):
        super().__init__(pixmap)
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.original_pixmap = pixmap
        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.is_resizing = False
        self.resize_handle_size = 10
        self.aspect_ratio = pixmap.width() / pixmap.height()
        self.setCursor(Qt.ArrowCursor)
        self.min_scale = 0.1
        self.max_scale = 10

    def hoverMoveEvent(self, event):
        if self.is_in_resize_area(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_in_resize_area(event.pos()):
            self.is_resizing = True
            self.resize_start_pos = event.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_resizing:
            offset = event.pos() - self.resize_start_pos
            self.resize_image(offset)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_resizing:
            self.is_resizing = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def boundingRect(self):
        return QRectF(0, 0, self.pixmap().width(), self.pixmap().height())

    def resize_image(self, offset):
        scale_factor = 0.1
        new_width = self.boundingRect().width() + offset.x() * scale_factor
        new_height = new_width / self.aspect_ratio

        self.prepareGeometryChange()

        if 10 < new_width <= self.canvas_width * 2 and 10 < new_height <= self.canvas_height * 2:
            scaled_pixmap = self.original_pixmap.scaled(
                int(new_width), int(new_height),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)

            self.update()

        self.prepareGeometryChange()

    def is_in_resize_area(self, pos):
        rect = self.boundingRect()
        resize_rect = QRectF(
            rect.right() - self.resize_handle_size,
            rect.bottom() - self.resize_handle_size,
            self.resize_handle_size,
            self.resize_handle_size
        )
        return resize_rect.contains(pos)

    def wheelEvent(self, event):
        try:
            if hasattr(event, 'angleDelta'):
                delta = event.angleDelta().y()
            elif hasattr(event, 'delta'):
                delta = event.delta()
            else:
                delta = 0

            factor = 1.1 if delta > 0 else 0.9

            self.resize_with_factor(factor)
        except AttributeError:
            pass

    def resize_with_factor(self, factor):
        new_width = self.boundingRect().width() * factor
        new_height = new_width / self.aspect_ratio

        if self.min_scale * self.canvas_width <= new_width <= self.max_scale * self.canvas_width and \
           self.min_scale * self.canvas_height <= new_height <= self.max_scale * self.canvas_height:
            scaled_pixmap = self.original_pixmap.scaled(
                int(new_width), int(new_height), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
