from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QRadioButton,
    QCheckBox,
    QButtonGroup
)

from .filter_widget_combo_base import FilterWidgetComboBase
from ..api import (
    DataBrowserQuery,
    CreativeCommonLicenseVersions
)


class LicenseFilterWidget(FilterWidgetComboBase):
    """
    Custom widget for license filtering
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.drop_down_widget = QWidget()
        vl = QVBoxLayout()

        self.cc_4_checkbox = QCheckBox('CC Attribution 4.0')
        vl.addWidget(self.cc_4_checkbox)

        self.cc_3_checkbox = QCheckBox('CC Attribution 3.0')
        vl.addWidget(self.cc_3_checkbox)

        self.cc_options_widget = QWidget()
        cc_options_layout = QVBoxLayout()
        cc_options_layout.setContentsMargins(self._indent_margin, 0, 0, 0)

        cc_attribute_checkbox = QCheckBox('Must attribute licensor')
        cc_attribute_checkbox.setChecked(True)
        cc_attribute_checkbox.setEnabled(False)
        cc_options_layout.addWidget(cc_attribute_checkbox)

        self.derivatives_allowed_radio = QRadioButton('Derivatives allowed')
        cc_options_layout.addWidget(self.derivatives_allowed_radio)
        self.no_derivatives_allowed_radio = QRadioButton('No derivatives allowed')
        cc_options_layout.addWidget(self.no_derivatives_allowed_radio)
        self.derivatives_group = QButtonGroup()
        self.derivatives_group.addButton(self.derivatives_allowed_radio)
        self.derivatives_group.addButton(self.no_derivatives_allowed_radio)

        self.commercial_use_allowed_radio = QRadioButton('Commercial use allowed')
        cc_options_layout.addWidget(self.commercial_use_allowed_radio)
        self.no_commercial_use_allowed_radio = QRadioButton('No commerical use allowed')
        cc_options_layout.addWidget(self.no_commercial_use_allowed_radio)
        self.commercial_group = QButtonGroup()
        self.commercial_group.addButton(self.commercial_use_allowed_radio)
        self.commercial_group.addButton(self.no_commercial_use_allowed_radio)

        self.no_changes_need_to_be_shared_radio = QRadioButton('Changes don\'t need to be shared')
        cc_options_layout.addWidget(self.no_changes_need_to_be_shared_radio)
        self.changes_need_to_be_shared_radio = QRadioButton('Changes need to be shared')
        cc_options_layout.addWidget(self.changes_need_to_be_shared_radio)
        self.share_alike_group = QButtonGroup()
        self.share_alike_group.addButton(self.no_changes_need_to_be_shared_radio)
        self.share_alike_group.addButton(self.changes_need_to_be_shared_radio)

        self.cc_options_widget.setLayout(cc_options_layout)
        vl.addWidget(self.cc_options_widget)
        self.cc_options_widget.setVisible(False)

        self.drop_down_widget.setLayout(vl)

        self.set_contents_widget(self.drop_down_widget)

        self.cc_4_checkbox.toggled.connect(self._update_visible_frames)
        self.cc_3_checkbox.toggled.connect(self._update_visible_frames)

        self.derivatives_group.buttonClicked.connect(self._update_value)
        self.commercial_group.buttonClicked.connect(self._update_value)
        self.share_alike_group.buttonClicked.connect(self._update_value)
        self.cc_4_checkbox.toggled.connect(self._update_value)
        self.cc_3_checkbox.toggled.connect(self._update_value)

        self.clear()

    def _update_visible_frames(self):
        self.cc_options_widget.setVisible(self.cc_3_checkbox.isChecked()
                                          or self.cc_4_checkbox.isChecked())

        self.drop_down_widget.adjustSize()
        self._floating_widget.reflow()

    def clear(self):
        self.cc_4_checkbox.setChecked(False)
        self.cc_3_checkbox.setChecked(False)
        self.derivatives_allowed_radio.setChecked(True)
        self.commercial_use_allowed_radio.setChecked(True)
        self.no_changes_need_to_be_shared_radio.setChecked(True)
        self._update_visible_frames()
        self._update_value()

    def should_show_clear(self):
        if not self.cc_4_checkbox.isChecked() and not self.cc_3_checkbox.isChecked():
            return False

        return super().should_show_clear()

    def _update_value(self):
        text = 'License'

        options = ['BY']
        if self.changes_need_to_be_shared_radio.isChecked():
            options.append('SA')
        if self.no_commercial_use_allowed_radio.isChecked():
            options.append('NC')
        if self.no_derivatives_allowed_radio.isChecked():
            options.append('ND')

        cc_license_suffice = '-'.join(options)

        if self.cc_3_checkbox.isChecked() and self.cc_4_checkbox.isChecked():
            text = 'CC4 + CC3 {}'.format(cc_license_suffice)
        elif self.cc_3_checkbox.isChecked():
            text = 'CC3 {}'.format(cc_license_suffice)
        elif self.cc_4_checkbox.isChecked():
            text = 'CC4 {}'.format(cc_license_suffice)

        self.set_current_text(text)
        if not self._block_changes:
            self.changed.emit()

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        if self.cc_options_widget.isHidden():
            query.cc_license_changes_must_be_shared = None
            query.cc_license_allow_commercial = None
            query.cc_license_allow_derivates = None
        else:
            query.cc_license_changes_must_be_shared = \
                self.changes_need_to_be_shared_radio.isChecked()
            query.cc_license_allow_commercial = \
                self.commercial_use_allowed_radio.isChecked()
            query.cc_license_allow_derivates = \
                self.derivatives_allowed_radio.isChecked()

        if self.cc_3_checkbox.isChecked():
            query.cc_license_versions.add(CreativeCommonLicenseVersions.Version3)
        if self.cc_4_checkbox.isChecked():
            query.cc_license_versions.add(CreativeCommonLicenseVersions.Version4)

    def set_from_query(self, query: DataBrowserQuery):
        self._block_changes += 1

        if query.cc_license_changes_must_be_shared:
            self.changes_need_to_be_shared_radio.setChecked(True)
        else:
            self.no_changes_need_to_be_shared_radio.setChecked(True)
        if query.cc_license_allow_commercial:
            self.commercial_use_allowed_radio.setChecked(True)
        else:
            self.no_commercial_use_allowed_radio.setChecked(True)
        if query.cc_license_allow_derivates:
            self.derivatives_allowed_radio.setChecked(True)
        else:
            self.no_derivatives_allowed_radio.setChecked(True)

        self.cc_3_checkbox.setChecked(
            CreativeCommonLicenseVersions.Version3 in query.cc_license_versions
        )
        self.cc_4_checkbox.setChecked(
            CreativeCommonLicenseVersions.Version4 in query.cc_license_versions
        )

        self._update_value()
        self._update_visible_frames()
        self._block_changes -= 1
