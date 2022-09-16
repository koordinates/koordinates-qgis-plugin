from qgis.PyQt.QtCore import pyqtSignal

from .custom_combo_box import CustomComboBox
from ..api import DataBrowserQuery

class FilterWidgetComboBase(CustomComboBox):
    """
    Base class for filtering combo widgets
    """

    changed = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.set_show_clear_button(True)

        self._indent_margin = self.fontMetrics().width('xx')

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        """
        Applies current widget constraints to a query

        Must be implemented by subclasses
        """
        assert False
