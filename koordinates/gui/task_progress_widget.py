from typing import Optional

from qgis.PyQt.QtCore import (
    QModelIndex
)
from qgis.PyQt.QtWidgets import (
    QPushButton,
    QProgressBar,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableView,
    QDialog
)

from qgis.gui import QgsGui

from ..core import (
    KartOperationManager
)


class TaskDetailsWidget(QWidget):
    """
    A widget for showing task details in a list, where all properties
    are retrieved via the KartOperationManager model implementation
    """

    def __init__(self,
                 index: QModelIndex,
                 operations_manager: KartOperationManager,
                 parent=None):
        super().__init__(parent)

        self.index = index
        self.operations_manager = operations_manager

        vl = QVBoxLayout()
        hl = QHBoxLayout()
        self.title_label = QLabel()
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)

        hl.addWidget(self.title_label)
        self.operation_label = QLabel()
        hl.addWidget(self.operation_label, 1)
        vl.addLayout(hl)

        hl = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        hl.addWidget(self.progress_bar, 1)
        self.cancel_button = QPushButton(self.tr('Cancel'))
        hl.addWidget(self.cancel_button)
        self.cancel_button.clicked.connect(self._cancel)
        vl.addLayout(hl)

        self.setLayout(vl)

        self.setMinimumHeight(self.sizeHint().height())
        self.update_from_model()

    def update_from_model(self):
        """
        Updates the widget from the current model data
        """
        self.title_label.setText(self.operations_manager.data(
            self.index, KartOperationManager.DescriptionRole
        ))
        self.progress_bar.setValue(
            int(self.operations_manager.data(
                self.index, KartOperationManager.ProgressRole
            )))

    def _cancel(self):
        """
        Triggers cancelation of the corresponding task
        """
        self.operations_manager.cancel_task(self.index)


class TaskDetailsTable(QTableView):
    """
    A table view showing current task details
    """

    def __init__(self,
                 operations_manager: KartOperationManager,
                 parent=None):
        super().__init__(parent)
        self._manager = operations_manager
        self.setModel(self._manager)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)

        self._manager.rowsInserted.connect(self._rows_inserted)
        self._manager.dataChanged.connect(self._data_changed)
        row_count = self._manager.rowCount()
        if row_count:
            self._rows_inserted(QModelIndex(), 0, row_count - 1)

    def _rows_inserted(self,
                       parent: QModelIndex,  # pylint: disable=unused-argument
                       first: int,
                       last: int):
        """
        Called when rows are inserted into the model
        """
        for row in range(first, last + 1):
            index = self._manager.index(row, 0)
            widget = TaskDetailsWidget(index, self._manager)
            self.setIndexWidget(index, widget)
            self.setRowHeight(row, widget.minimumHeight())

    def _data_changed(self,
                      top_left: QModelIndex,
                      bottom_right: QModelIndex,
                      roles=[]):  # pylint: disable=unused-argument
        """
        Called when model data is changed for a range of indexes
        """
        for row in range(top_left.row(), bottom_right.row() + 1):
            index = self._manager.index(row, 0)
            widget = self.indexWidget(index)
            if not widget:
                continue

            widget.update_from_model()


class TaskDetailsDialog(QDialog):
    """
    A dialog for showing task details
    """

    def __init__(self,
                 operations_manager: KartOperationManager,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setObjectName('TaskDetailsDialog')
        QgsGui.enableAutoGeometryRestore(self)

        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)
        self.widget = TaskDetailsTable(operations_manager)
        vl.addWidget(self.widget)
        self.setLayout(vl)
