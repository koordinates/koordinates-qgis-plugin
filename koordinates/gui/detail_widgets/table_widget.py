import platform
from typing import (
    Optional,
    List
)

from qgis.PyQt.QtCore import (
    Qt,
    QUrl
)
from qgis.PyQt.QtGui import QDesktopServices
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

    INITIAL_VISIBLE_ROWS = 4

    def __init__(self,
                 headings: List[str],
                 contents: List[List[str]],
                 parent: Optional[QWidget] = None):
        super().__init__(parent)

        vl = QVBoxLayout()
        vl.setContentsMargins(0, 0, 0, 0)

        self.table_label = QLabel()
        self.headings = headings
        self.contents = contents

        self.rebuild_table()
        self.table_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.table_label.linkActivated.connect(self.link_clicked)

        vl.addWidget(self.table_label)
        self.setLayout(vl)

    def rebuild_table(self, expand=False):
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
        if self.headings:
            html += "<tr>"
            for cell in self.headings:
                html += f"""<th
                style="background-color: {self.HEADING_BACKGROUND_COLOR};
                text-align: left;
                border: 1px solid {self.BORDER_COLOR};
                padding: {padding} {padding} {padding} {padding}">{cell}</th>"""
            html += "</tr>"

        if not expand:
            visible_rows = self.contents[:self.INITIAL_VISIBLE_ROWS]
        else:
            visible_rows = self.contents[:]

        for row in visible_rows:
            html += "<tr>"
            for cell in row:
                html += f"""<td
                style="background-color: {self.BACKGROUND_COLOR};
                border: 1px solid {self.BORDER_COLOR};
                padding: {padding} {padding} {padding} {padding}">{cell}</td>"""

            html += "</tr>"

        if len(self.contents) > self.INITIAL_VISIBLE_ROWS and not expand:
            html += "<tr>"
            html += """<td colspan="2"><a href="more"><table><tr><td
                style="background-color: #ffffff; 
                border: 1px solid #a9a9a9;
                color: #868889;
                padding: 3px;
                text-decoration: none;
                border-radius: 3px;">Show more</td></tr></table></a></td>"""
            html += "</tr>"

        html += """
        </table>
        """
        self.table_label.setText(html)

    def link_clicked(self, link):
        if link == 'more':
            self.rebuild_table(True)
        else:
            QDesktopServices.openUrl(QUrl(link))
