from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QRadioButton,
    QButtonGroup
)

from .filter_widget_combo_base import FilterWidgetComboBase
from ..api import (
    DataBrowserQuery
)


class CategoryFilterWidget(FilterWidgetComboBase):
    """
    Custom widget for category based filtering
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.drop_down_widget = QWidget()
        vl = QVBoxLayout()

        self.all_categories_radio = QRadioButton('All categories')
        self.category_radios = []
        self.category_group = QButtonGroup()
        self.category_group.addButton(self.all_categories_radio)
        vl.addWidget(self.all_categories_radio)

        self.drop_down_widget.setLayout(vl)

        self.set_contents_widget(self.drop_down_widget)

        self.category_group.buttonClicked.connect(self._update_value)
        self.category_group.buttonClicked.connect(self._update_visible_frames)

        self.current_categories = set()
        self.clear()

    def set_facets(self, facets: dict):
        new_categories = set(c['key'] for c in facets.get('category'))
        if new_categories == self.current_categories:
            # no change, do nothing
            return

        self.current_categories = new_categories

        prev_key, prev_name = self._get_current_category()

        for w in self.category_radios:
            if hasattr(w, '_child_frame') and w._child_frame is not None:
                w._child_frame.deleteLater()

            w.deleteLater()

        self.category_radios = []

        categories = []
        for c in facets.get('category', []):
            key = c['key']
            if '/' in key:
                continue  # child category
            else:
                c['children'] = []
                categories.append(c)
        for c in facets.get('category', []):
            key = c['key']
            if '/' not in key:
                continue  # parent category
            else:
                parent_key = key.split('/')[0]
                parent = [p for p in categories if p['key'] == parent_key]
                if not parent:
                    continue  # something bad!
                parent[0]['children'].append(c)

        for c in categories:
            name = c['name']
            label = name.replace('&', '&&')
            r = QRadioButton(label)
            r._key = c['key']
            r._name = name
            r._child_frame = None
            r._child_group = None

            self.drop_down_widget.layout().addWidget(r)
            self.category_group.addButton(r)

            if prev_key == r._key:
                r.setChecked(True)

            children = c.get("children", [])
            if children:
                child_group = QButtonGroup()
                child_frame = QWidget()
                child_frame_layout = QVBoxLayout()
                child_frame_layout.setContentsMargins(self._indent_margin, 0, 0, 0)
                for child in children:
                    name = child['name']
                    label = name.replace('&', '&&')
                    r_child = QRadioButton(label)
                    r_child._key = child['key']
                    r_child._name = name
                    r_child._parent_radio = r

                    child_frame_layout.addWidget(r_child)
                    child_group.addButton(r_child)
                    self.category_radios.append(r_child)

                    if prev_key == r_child._key:
                        r_child.setChecked(True)
                        r.setChecked(True)

                child_frame.setLayout(child_frame_layout)
                r._child_frame = child_frame
                r._child_group = child_group

                child_group.buttonClicked.connect(self._update_value)
                child_group.buttonClicked.connect(self._update_visible_frames)

                if not r.isChecked():
                    child_frame.hide()
                self.drop_down_widget.layout().addWidget(child_frame)

            self.category_radios.append(r)

        self._block_changes = True

        if not prev_key:
            self.all_categories_radio.setChecked(True)
        else:
            found = False
            for r in self.category_radios:
                if prev_key == r._key:
                    found = True
                    r.setChecked(True)
                    if hasattr(r, '_parent_radio') and r._parent_radio is not None:
                        r._parent_radio.setChecked(True)
                    break
            if not found:
                self.all_categories_radio.setChecked(True)
                self.changed.emit()

        self._update_value()
        QCoreApplication.processEvents()
        self._update_visible_frames()
        self._block_changes = False

    def _update_visible_frames(self):
        for r in self.category_radios:
            if hasattr(r, '_child_frame') and r._child_frame is not None:
                r._child_frame.setVisible(r.isChecked())
                r._child_frame.adjustSize()

        self.drop_down_widget.adjustSize()
        self._floating_widget.reflow()

    def clear(self):
        self.all_categories_radio.setChecked(True)
        self._update_visible_frames()
        self._update_value()

    def should_show_clear(self):
        if self.all_categories_radio.isChecked():
            return False

        for r in self.category_radios:
            if r.isChecked():
                return True

        return super().should_show_clear()

    def _get_current_category(self):
        if not self.all_categories_radio.isChecked():
            for r in self.category_radios:
                if not r.isChecked():
                    continue

                if hasattr(r, '_parent_radio') and r._parent_radio is not None:
                    if r._parent_radio.isChecked():
                        return r._key, r._name
                    else:
                        continue
                else:
                    if hasattr(r, '_child_frame') and r._child_frame is not None:
                        found_checked_child = False
                        for b in r._child_group.buttons():
                            if b.isChecked():
                                found_checked_child = True
                                break

                        if found_checked_child:
                            continue

                    return r._key, r._name

        return None, None

    def _update_value(self):
        text = 'Category'

        key, name = self._get_current_category()
        if name:
            text = name

        self.set_current_text(text)
        if not self._block_changes:
            self.changed.emit()

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        if not self.all_categories_radio.isChecked():
            key, name = self._get_current_category()
            if key:
                query.category = key

    def set_from_query(self, query: DataBrowserQuery):
        self._block_changes = True

        if not query.category:
            self.all_categories_radio.setChecked(True)
        else:
            for r in self.category_radios:
                if query.category == r._key:
                    r.setChecked(True)
                    if hasattr(r, '_parent_radio') and r._parent_radio is not None:
                        r._parent_radio.setChecked(True)
                    break

        self._update_value()
        self._update_visible_frames()
        self._block_changes = False
