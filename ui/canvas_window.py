import os
import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QDialog, QPushButton, QVBoxLayout, QLineEdit, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem, QMessageBox,
    QMenuBar, QMenu, QAction
)
from PyQt5.QtGui import QPixmap, QImage, QColor, QPainter, QTransform
from PyQt5.QtCore import pyqtSignal, Qt, QRectF, QPointF


class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.zoom_step = 1.1
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setFocusPolicy(Qt.StrongFocus)  # 确保视图可以接收焦点

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        # 修改为无需按下 Alt 键即可缩放视图
        if modifiers == Qt.NoModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                factor = self.zoom_step
            else:
                factor = 1 / self.zoom_step
            self.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)


class CanvasWindow(QDialog):
    save_signal = pyqtSignal()
    close_signal = pyqtSignal()

    def __init__(self, input_image, canvas_width=512, canvas_height=512):
        super().__init__()

        self.setWindowTitle("Snap Canvas")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.input_image = input_image
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.modified_image = None

        self.top_left_x = 0
        self.top_left_y = 0
        self.scale_factor = 1.0  # 初始缩放倍数

        self.scene = QGraphicsScene()
        # 使用自定义的视图
        self.view = CustomGraphicsView(self.scene)
        self.view.setStyleSheet("border: 1px solid black; background-color: #404040;")  # 设置深灰色背景区分画布

        # 设置滚动条策略为需要时显示
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 启用拖动画布
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)

        # 创建白色画布
        self.canvas = QImage(self.canvas_width, self.canvas_height, QImage.Format_RGB888)
        self.canvas.fill(QColor('white'))

        # 添加画布到场景
        self.canvas_pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(self.canvas))
        self.scene.addItem(self.canvas_pixmap_item)

        # 添加可调整大小和可旋转的输入图像
        original_pixmap = QPixmap.fromImage(self.input_image)
        self.input_pixmap_item = ResizablePixmapItem(original_pixmap)
        self.input_pixmap_item.setPos(self.canvas_width / 2, self.canvas_height / 2)  # 将图像放置在画布中央
        self.scene.addItem(self.input_pixmap_item)

        # 设置旋转锚点为图像中心
        self.input_pixmap_item.setTransformOriginPoint(self.input_pixmap_item.boundingRect().center())

        # 创建菜单栏
        self.menu_bar = QMenuBar(self)
        help_menu = QMenu("使用说明(Help)", self)
        self.menu_bar.addMenu(help_menu)

        # 创建“使用方法”动作
        usage_action = QAction("使用方法", self)
        usage_action.triggered.connect(self.show_usage)
        help_menu.addAction(usage_action)

        # 创建按钮和输入框
        save_button = QPushButton("保存并关闭", self)
        save_button.clicked.connect(self.save_and_close)

        rotate_label = QLineEdit(self)
        rotate_label.setPlaceholderText("旋转角度 (°)")
        rotate_label.setFixedWidth(100)
        self.rotate_input = rotate_label

        rotate_button = QPushButton("旋转", self)
        rotate_button.clicked.connect(self.rotate_image)

        scale_label = QLineEdit(self)
        scale_label.setPlaceholderText("缩放倍数")
        scale_label.setFixedWidth(100)
        self.scale_input = scale_label

        scale_button = QPushButton("缩放", self)
        scale_button.clicked.connect(self.scale_image)

        self.canvas_width_input = QLineEdit(self)
        self.canvas_width_input.setPlaceholderText("画布宽度")
        self.canvas_width_input.setText(str(self.canvas_width))
        self.canvas_height_input = QLineEdit(self)
        self.canvas_height_input.setPlaceholderText("画布高度")
        self.canvas_height_input.setText(str(self.canvas_height))

        size_button = QPushButton("设置画布大小", self)
        size_button.clicked.connect(self.set_canvas_size)

        # 布局设置
        hbox = QHBoxLayout()
        hbox.addWidget(self.canvas_width_input)
        hbox.addWidget(self.canvas_height_input)
        hbox.addWidget(size_button)
        hbox.addWidget(self.rotate_input)
        hbox.addWidget(rotate_button)
        hbox.addWidget(self.scale_input)
        hbox.addWidget(scale_button)

        vbox = QVBoxLayout()
        vbox.setMenuBar(self.menu_bar)  # 将菜单栏添加到布局中
        vbox.addWidget(self.view)
        vbox.addLayout(hbox)
        vbox.addWidget(save_button)

        self.setLayout(vbox)

        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)
        self.view.setSceneRect(0, 0, self.canvas_width, self.canvas_height)

        # 设置窗口最小大小
        self.setMinimumSize(600, 400)

    def show_usage(self):
        usage_text = (
            "使用方法：\n"
            "1. 滚动鼠标滚轮可缩放视图。\n"
            "2. 按住 Ctrl 键并滚动鼠标滚轮可缩放图像。\n"
            "3. 在输入框中输入旋转角度（度数），点击“旋转”按钮可旋转图像。\n"
            "4. 在输入框中输入缩放倍数，点击“缩放”按钮可缩放图像。\n"
            "5. 拖动图像可移动其位置。\n"
            "6. 使用上方输入框可调整画布大小。\n"
            "7. 点击“保存并关闭”按钮可保存当前图像。\n"
        )
        QMessageBox.information(self, "使用方法", usage_text)

    def save_and_close(self):
        self.save_image()
        self.accept()

    def save_image(self):
        # 创建一个与画布大小相同的图像
        image = QImage(self.canvas_width, self.canvas_height, QImage.Format_RGB888)
        image.fill(QColor('white'))

        painter = QPainter(image)
        target_rect = QRectF(0, 0, self.canvas_width, self.canvas_height)

        # 渲染场景
        self.scene.render(painter, target_rect, self.scene.sceneRect(), Qt.IgnoreAspectRatio)

        painter.end()

        self.modified_image = image

        # 获取图像左上角的坐标
        top_left_point = self.input_pixmap_item.mapToScene(0, 0)
        self.top_left_x = int(top_left_point.x())
        self.top_left_y = int(top_left_point.y())

        # 获取缩放倍数
        self.scale_factor = self.input_pixmap_item.current_scale

    def closeEvent(self, event):
        self.close_signal.emit()
        event.accept()

    def set_canvas_size(self):
        try:
            width = int(self.canvas_width_input.text())
            height = int(self.canvas_height_input.text())
        except ValueError:
            QMessageBox.warning(self, "输入错误", "画布宽度和高度必须是整数。")
            return

        # 更新画布宽度和高度
        self.canvas_width = width
        self.canvas_height = height

        # 更新场景和视图的画布大小
        self.canvas = QImage(self.canvas_width, self.canvas_height, QImage.Format_RGB888)
        self.canvas.fill(QColor('white'))
        self.canvas_pixmap_item.setPixmap(QPixmap.fromImage(self.canvas))

        self.scene.setSceneRect(0, 0, self.canvas_width, self.canvas_height)
        self.view.setSceneRect(0, 0, self.canvas_width, self.canvas_height)

    def rotate_image(self):
        try:
            angle = float(self.rotate_input.text())
        except ValueError:
            QMessageBox.warning(self, "输入错误", "旋转角度必须是数字。")
            return
        self.input_pixmap_item.rotate_pixmap(angle)

    def scale_image(self):
        try:
            scale_factor = float(self.scale_input.text())
            if scale_factor <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "输入错误", "缩放倍数必须是正数。")
            return
        self.input_pixmap_item.scale_pixmap(scale_factor)

    def get_modified_image(self):
        return self.modified_image

    def get_top_left_x(self):
        return self.top_left_x

    def get_top_left_y(self):
        return self.top_left_y

    def get_scale_factor(self):
        return self.scale_factor


class ResizablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable
        )
        self.setTransformationMode(Qt.SmoothTransformation)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(False)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.current_scale = 1.0
        self.current_rotation = 0.0
        self.min_scale = 0.1
        self.max_scale = 10.0

    def scale_pixmap(self, scale_factor):
        if self.min_scale <= scale_factor <= self.max_scale:
            self.current_scale = scale_factor
            self.update_transform()
        else:
            QMessageBox.warning(None, "无效的缩放", f"缩放倍数必须在 {self.min_scale} 和 {self.max_scale} 之间。")

    def rotate_pixmap(self, angle):
        self.current_rotation = angle % 360
        self.update_transform()

    def update_transform(self):
        transform = QTransform()
        center = self.boundingRect().center()
        transform.translate(center.x(), center.y())
        transform.rotate(self.current_rotation)
        transform.scale(self.current_scale, self.current_scale)
        transform.translate(-center.x(), -center.y())
        self.setTransform(transform)

    def wheelEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            delta = event.delta()  # 修改这里，使用 delta()
            if delta > 0:
                factor = 1.1
            else:
                factor = 0.9
            new_scale = self.current_scale * factor
            self.scale_pixmap(new_scale)
            event.accept()
        else:
            event.ignore()  # 确保事件能够传递给视图进行缩放


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 示例输入图像，可以替换为您自己的图像路径
    input_image_path = "your_image.png"
    if not os.path.exists(input_image_path):
        # 创建一个示例图像
        input_image = QImage(200, 200, QImage.Format_RGB888)
        input_image.fill(QColor('blue'))
    else:
        input_image = QImage(input_image_path)

    window = CanvasWindow(input_image)
    window.show()
    sys.exit(app.exec_())
