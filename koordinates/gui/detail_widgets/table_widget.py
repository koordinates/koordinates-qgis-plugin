import platform
from typing import (
    Optional,
    List
)

from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel
)

from ..gui_utils import FONT_FAMILIES


class TableWidget(QWidget):
    """
    Displays a styled table of data
    """

    BACKGROUND_COLOR = "#ffffff"
    HEADING_BACKGROUND_COLOR = "#f5f5f7"
    BORDER_COLOR = "#eaeaea"

    def __init__(self,
                 headings: List[str],
                 contents: List[List[str]],
                 parent: Optional[QWidget] = None):
        super().__init__(parent)

        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)

        self.table_label = QLabel()

        base_font_size = 10
        if platform.system() == 'Darwin':
            base_font_size = 14

        padding = int(base_font_size * 0.75)

        html = f"""
        <table width="100%" style="font-family: {FONT_FAMILIES};
            font-size: {base_font_size}pt;
            border-collapse: collapse;
           ">
        """
        if headings:
            html += "<tr>"
            for cell in headings:
                html += f"""<th
                style="background-color: {self.HEADING_BACKGROUND_COLOR};
                text-align: left;
                border: 1px solid {self.BORDER_COLOR};
                padding: {padding} {padding} {padding} {padding}">{cell}</th>"""
            html += "</tr>"

        for row in contents:
            html += "<tr>"
            for cell in row:
                html += f"""<td
                style="background-color: {self.BACKGROUND_COLOR};
                border: 1px solid {self.BORDER_COLOR};
                padding: {padding} {padding} {padding} {padding}">{cell}</td>"""

            html += "</tr>"

        html += """
        </table>
        """
        self.table_label.setText(html)

        vl.addWidget(self.table_label)
        self.setLayout(vl)
