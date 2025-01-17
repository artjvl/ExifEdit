import logging
from typing import Optional, List, Tuple
from PySide6 import QtCore, QtWidgets, QtGui

from package.FileList import FileList
from package.FileTree import FileTree
from package.ImageViewer import ImageViewer
from package.FileEdit import FileEdit
from package.Image import Image
from package.FileModify import FileModify


class MainWindow(QtWidgets.QMainWindow):

    _SIZE: Tuple[int, int] = (920, 920)

    _file_tree: FileTree
    _file_list: FileList
    _image_viewer: ImageViewer
    _file_edit: FileEdit
    _file_modify: FileModify

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        """
        Signal flow:
        
        - FileTree
          - Action: user clicks on path from tree -> Signal: 'signal_path_changed'
            - FileList: loads directory
            - ImageViewer: saves image paths from directory and loads/renders first image
        
        - FileList:
          - Action: user loads directory -> Signal 'signal_load_directory'
            - ImageViewer: updates 'Next' and 'Previous' buttons based on number of loaded files
          - Action: user clicks (highlights) path(s) from list 
              -> Signal: 'signal_highlight_changed' with path of first highlighted item
            - ImageViewer: loads/renders highlighted image (if it is not already rendered)
          - Action: user selects (clicks checkboxes or uses 'Select highlighted' button) path(s) from list 
              -> Signal: 'signal_selection_changed'
            - FileModify: saves image paths
        
        - ImageViewer:
          - Action: user cycles through images with arrows keys -> Signal: 'signal_image_cycle'
            - FileList: returns the corresponding next/previous image path
        
        - FileModify:
          - Action: user modifies files according to FileEdit -> Signal: 'signal_done'
            - FileTree: enables/disables widget
            - FileList: enables/disables widget
            - FileEdit: enables/disables widget
        """

        logging.warning('MainWindow')
        super().__init__(parent)
        self.setWindowTitle("ExifEdit")
        self.setFixedSize(*self._SIZE)
        settings: QtCore.QSettings = QtCore.QSettings("ArtvL", "ExifEdit")

        # widgets - file-tree
        self._file_tree: FileTree = FileTree(settings, parent=self)

        # widgets - file-list
        self._file_list: FileList = FileList(parent=self)
        self._file_tree.signal_path_changed.connect(
            self._file_list.load_directory
        )  # dependency: file-list

        # widgets - image-viewer
        self._image_viewer: ImageViewer = ImageViewer(parent=self)
        self._file_list.signal_load_directory.connect(
            self.on_filelist_load_directory
        )
        self._file_list.signal_highlight_changed.connect(
            self.on_filelist_highlight_changed
        )  # dependency: image-viewer, file-edit
        self._image_viewer.signal_image_cycle_next.connect(
            self.on_imageviewer_image_cycle_next
        )

        # widgets - file-edit
        self._file_edit: FileEdit = FileEdit(settings, parent=self)

        # widgets - file-modify
        self._file_modify: FileModify = FileModify(self._file_edit, parent=self)
        self._file_modify.signal_done.connect(
            self.on_file_modify_done
        )  # dependencies: file-tree, file-list, file-edit
        self._file_list.signal_selection_changed.connect(
            self.on_filelist_selection_changed
        )  # dependency: image-viewer, file-modify

        # layouts
        widget: QtWidgets.QWidget = QtWidgets.QWidget()
        self.setCentralWidget(widget)

        layout: QtWidgets.QLayout = QtWidgets.QHBoxLayout()
        layout.addWidget(self._file_tree)
        layout.addWidget(self._file_list)

        action_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        action_layout.addWidget(self._image_viewer)
        frame: QtWidgets.QFrame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.HLine)
        frame.setFrameShadow(QtWidgets.QFrame.Sunken)
        action_layout.addWidget(frame)
        action_layout.addWidget(self._file_edit)
        action_layout.addStretch()
        action_layout.addWidget(self._file_modify)

        layout.addItem(action_layout)
        widget.setLayout(layout)

        # menus
        self._menu = self.menuBar()

        # menu - file
        self._file_menu = self._menu.addMenu("File")
        action_exit: QtGui.QAction = QtGui.QAction("Exit", self)
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.exit_app)
        self._file_menu.addAction(action_exit)
        action_reload: QtGui.QAction = QtGui.QAction("Reload file-tree", self)
        action_reload.triggered.connect(self._file_tree.load_tree)
        self._file_menu.addAction(action_reload)
        action_send2trash: QtGui.QAction = QtGui.QAction(
            "Move original file copies to trash", self
        )
        action_send2trash.setCheckable(True)
        action_send2trash.setChecked(True)
        action_send2trash.triggered.connect(self._file_modify.enable_send2trash)
        self._file_menu.addAction(action_send2trash)

        # menu - view
        self._view_menu = self._menu.addMenu("View")
        action_resize: QtGui.QAction = QtGui.QAction("Enable window resizing", self)
        action_resize.setCheckable(True)
        action_resize.setChecked(False)
        action_resize.triggered.connect(self.enable_resize)
        self._view_menu.addAction(action_resize)

    @QtCore.Slot()
    def exit_app(self, is_checked: bool) -> None:
        QtWidgets.QApplication.quit()

    @QtCore.Slot()
    def enable_resize(self, is_checked: bool) -> None:
        if is_checked:
            max_widget_size: int = (1 << 24) - 1
            self.setMaximumSize(max_widget_size, max_widget_size)
        else:
            self.resize(*self._SIZE)
            self.setFixedSize(*self._SIZE)

    @QtCore.Slot()
    def on_filelist_selection_changed(self) -> None:
        filepaths: List[str] = self._file_list.selected_paths()
        if filepaths:
            self._file_modify.set_images(filepaths)
        else:
            self._file_modify.clear_images()

    @QtCore.Slot()
    def on_filelist_load_directory(self, num_files: int) -> None:
        if num_files > 0:
            # enable next/previous buttons
            if num_files > 1:
                self._image_viewer.enable_buttons(True)
            else:
                self._image_viewer.enable_buttons(False)

            # load first highlighted image
            first_path: str = self._file_list.highlighted_paths()[0]
            self.on_filelist_highlight_changed(first_path)
            
            selected_paths: List[str] = self._file_list.selected_paths()
            if len(selected_paths) > 1:
                self._file_modify.set_images(selected_paths)

        elif self._image_viewer.has_image():
            # clear widgets
            self._image_viewer.clear()
            self._file_edit.clear()
            self._file_modify.clear_images()

    @QtCore.Slot()
    def on_filelist_highlight_changed(self, path: str) -> None:
        img: Image = self._image_viewer.load_image(path)
        self._file_edit.set_file(img)

    @QtCore.Slot()
    def on_imageviewer_image_cycle_next(self, is_next: bool) -> None:
        path: str
        if is_next:
            path = self._file_list.next_highlight()
        else:
            path = self._file_list.previous_highlight()
        self._image_viewer.load_image(path)

    @QtCore.Slot()
    def on_file_modify_done(self, is_done: bool) -> None:
        if not is_done:
            self._file_tree.setEnabled(False)
            self._file_list.setEnabled(False)
            self._file_edit.setEnabled(False)
        else:
            self._file_tree.setEnabled(True)
            self._file_edit.setEnabled(True)
            self._file_list.setEnabled(True)

            filepaths: List[str] = self._file_modify.new_filepaths()

            first_path: str = filepaths[0]
            self._file_list.reload(selected_filepaths=filepaths, highlighted_filepaths=[first_path])
