from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QRadioButton,
    QCheckBox,
    QButtonGroup
)

from .custom_combo_box import CustomComboBox


class DataTypeFilterWidget(CustomComboBox):
    """
    Custom widget for data type filtering
    """

    changed = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.set_show_clear_button(True)

        self._block_geometry_type_constraint_update = 0

        indent_margin = self.fontMetrics().width('xx')

        self.drop_down_widget = QWidget()
        vl = QVBoxLayout()

        self.layers_radio = QRadioButton('Layers')
        vl.addWidget(self.layers_radio)

        self.layers_widget = QWidget()
        layers_widget_layout = QVBoxLayout()
        layers_widget_layout.setContentsMargins(indent_margin, 0, 0, 0)

        self.vector_radio = QRadioButton('Vectors')
        layers_widget_layout.addWidget(self.vector_radio)

        self.vector_frame = QWidget()
        vector_frame_layout = QVBoxLayout()
        vector_frame_layout.setContentsMargins(indent_margin, 0, 0, 0)

        self.point_checkbox = QCheckBox('Point')
        vector_frame_layout.addWidget(self.point_checkbox)
        self.line_checkbox = QCheckBox('Line')
        vector_frame_layout.addWidget(self.line_checkbox)
        self.polygon_checkbox = QCheckBox('Polygon')
        vector_frame_layout.addWidget(self.polygon_checkbox)

        self.point_checkbox.toggled.connect(self._enforce_geometry_type_constraints)
        self.line_checkbox.toggled.connect(self._enforce_geometry_type_constraints)
        self.polygon_checkbox.toggled.connect(self._enforce_geometry_type_constraints)

        self.has_z_elevation_checkbox = QCheckBox('Has Z elevation')
        vector_frame_layout.addWidget(self.has_z_elevation_checkbox)
        self.vector_has_primary_key_checkbox = QCheckBox('Has primary key')
        vector_frame_layout.addWidget(self.vector_has_primary_key_checkbox)
        self.vector_frame.setLayout(vector_frame_layout)
        layers_widget_layout.addWidget(self.vector_frame)

        self.vector_frame.setVisible(False)

        self.raster_radio = QRadioButton('Rasters')
        layers_widget_layout.addWidget(self.raster_radio)

        self.raster_frame = QWidget()
        raster_frame_layout = QVBoxLayout()
        raster_frame_layout.setContentsMargins(indent_margin, 0, 0, 0)

        self.aerial_radio = QRadioButton('Aerial && satellite photos')
        raster_frame_layout.addWidget(self.aerial_radio)
        self.not_aerial_radio = QRadioButton('Not aerial && satellite photos')
        raster_frame_layout.addWidget(self.not_aerial_radio)
        self.band_radio = QRadioButton('By band')
        raster_frame_layout.addWidget(self.band_radio)

        self.raster_band_frame = QWidget()
        raster_band_frame_layout = QVBoxLayout()
        raster_band_frame_layout.setContentsMargins(indent_margin, 0, 0, 0)

        self.rgb_radio = QRadioButton('RGB')
        raster_band_frame_layout.addWidget(self.rgb_radio)
        self.grayscale_radio = QRadioButton('Grayscale')
        raster_band_frame_layout.addWidget(self.grayscale_radio)

        self.raster_band_frame.setLayout(raster_band_frame_layout)
        raster_frame_layout.addWidget(self.raster_band_frame)

        self.raster_band_frame.setVisible(False)
        self.band_radio.toggled.connect(self._update_visible_frames)

        self.alpha_channel_checkbox = QCheckBox('Only with alpha channel')
        raster_frame_layout.addWidget(self.alpha_channel_checkbox)

        self.raster_frame.setLayout(raster_frame_layout)

        layers_widget_layout.addWidget(self.raster_frame)

        self.raster_frame.setVisible(False)

        self.grid_radio = QRadioButton('Grids')
        layers_widget_layout.addWidget(self.grid_radio)

        self.grid_frame = QWidget()
        grid_frame_layout = QVBoxLayout()
        grid_frame_layout.setContentsMargins(indent_margin, 0, 0, 0)
        self.multi_attribute_grids_only_checkbox = QCheckBox('Multi-attribute grids only (RAT\'s)')
        grid_frame_layout.addWidget(self.multi_attribute_grids_only_checkbox)

        self.grid_frame.setLayout(grid_frame_layout)
        layers_widget_layout.addWidget(self.grid_frame)

        self.grid_frame.setVisible(False)

        self.layers_widget.setLayout(layers_widget_layout)
        vl.addWidget(self.layers_widget)

        self.table_radio = QRadioButton('Tables')
        vl.addWidget(self.table_radio)

        self.table_frame = QWidget()
        table_frame_layout = QVBoxLayout()
        table_frame_layout.setContentsMargins(indent_margin, 0, 0, 0)
        self.table_has_pk_checkbox = QCheckBox('Has primary key')
        table_frame_layout.addWidget(self.table_has_pk_checkbox)
        self.table_frame.setLayout(table_frame_layout)

        self.table_frame.setVisible(False)

        vl.addWidget(self.table_frame)

        self.set_radio = QRadioButton('Sets')
        vl.addWidget(self.set_radio)
        self.data_repository_radio = QRadioButton('Data Repositories')
        vl.addWidget(self.data_repository_radio)
        self.document_radio = QRadioButton('Documents')
        vl.addWidget(self.document_radio)

        self.drop_down_widget.setLayout(vl)

        self.set_contents_widget(self.drop_down_widget)

        self.data_type_group = QButtonGroup(self)
        self.data_type_group.addButton(self.layers_radio)
        self.data_type_group.addButton(self.vector_radio)
        self.data_type_group.addButton(self.raster_radio)
        self.data_type_group.addButton(self.aerial_radio)
        self.data_type_group.addButton(self.not_aerial_radio)
        self.data_type_group.addButton(self.band_radio)
        self.data_type_group.addButton(self.grid_radio)
        self.data_type_group.addButton(self.table_radio)
        self.data_type_group.addButton(self.set_radio)
        self.data_type_group.addButton(self.data_repository_radio)
        self.data_type_group.addButton(self.document_radio)

        self.band_group = QButtonGroup(self)
        self.band_group.addButton(self.rgb_radio)
        self.band_group.addButton(self.grayscale_radio)

        self.data_type_group.buttonClicked.connect(self._update_visible_frames)
        self._enforce_geometry_type_constraints()
        self.rgb_radio.setChecked(True)
        self.layers_radio.setChecked(True)

        self.data_type_group.buttonClicked.connect(self._update_value)
        self.band_radio.toggled.connect(self._update_value)
        self.alpha_channel_checkbox.toggled.connect(self._update_value)
        self.multi_attribute_grids_only_checkbox.toggled.connect(self._update_value)
        self.band_group.buttonClicked.connect(self._update_value)
        self.table_has_pk_checkbox.toggled.connect(self._update_value)
        self.point_checkbox.toggled.connect(self._update_value)
        self.line_checkbox.toggled.connect(self._update_value)
        self.polygon_checkbox.toggled.connect(self._update_value)
        self.has_z_elevation_checkbox.toggled.connect(self._update_value)
        self.vector_has_primary_key_checkbox.toggled.connect(self._update_value)

        self.clear()

    def _update_visible_frames(self):
        self.vector_frame.setVisible(self.vector_radio.isChecked())
        self.raster_band_frame.setVisible(self.band_radio.isChecked())

        should_show_raster_group = self.raster_radio.isChecked() or \
                                   self.aerial_radio.isChecked() or self.not_aerial_radio.isChecked() or \
                                   self.band_radio.isChecked()

        self.raster_frame.setVisible(should_show_raster_group)

        self.grid_frame.setVisible(self.grid_radio.isChecked())
        self.table_frame.setVisible(self.table_radio.isChecked())

        self.raster_frame.adjustSize()
        self.layers_widget.adjustSize()
        self.drop_down_widget.adjustSize()
        self._floating_widget.reflow()

    def _enforce_geometry_type_constraints(self):
        if self._block_geometry_type_constraint_update:
            return

        none_selected = not (self.point_checkbox.isChecked() or self.line_checkbox.isChecked()
                             or self.polygon_checkbox.isChecked())
        if none_selected:
            self._block_geometry_type_constraint_update += 1
            self.point_checkbox.setChecked(True)
            self.line_checkbox.setChecked(True)
            self.polygon_checkbox.setChecked(True)
            self._block_geometry_type_constraint_update -= 1

    def clear(self):
        self.layers_radio.setChecked(True)
        self._update_visible_frames()
        self._update_value()

    def should_show_clear(self):
        if self.layers_radio.isChecked():
            return False

        return super().should_show_clear()

    def _update_value(self):
        text = ''
        if self.layers_radio.isChecked():
            text = 'Data type'
        elif self.vector_radio.isChecked():
            options = []
            if self.point_checkbox.isChecked() and self.line_checkbox.isChecked() and self.polygon_checkbox.isChecked():
                text = 'Vectors'
            else:
                if self.point_checkbox.isChecked():
                    options.append('Point')
                if self.line_checkbox.isChecked():
                    options.append('Line')
                if self.polygon_checkbox.isChecked():
                    options.append('Polygon')
                text = 'Vector'

            if self.has_z_elevation_checkbox.isChecked():
                options.append('Has Z')
            if self.vector_has_primary_key_checkbox.isChecked():
                options.append('Primary key')

            if options:
                text = '{}: {}'.format(text, ', '.join(options))

        elif self.raster_radio.isChecked():
            if self.alpha_channel_checkbox.isChecked():
                text = 'Raster: Alpha'
            else:
                text = 'Rasters'
        elif self.aerial_radio.isChecked():
            if self.alpha_channel_checkbox.isChecked():
                text = 'Raster: Aerial & satellite photos, Alpha'
            else:
                text = 'Raster: Aerial & satellite photos'
        elif self.not_aerial_radio.isChecked():
            if self.alpha_channel_checkbox.isChecked():
                text = 'Raster: Not aerial & satellite photos, Alpha'
            else:
                text = 'Raster: Not aerial & satellite photos'
        elif self.band_radio.isChecked():
            if self.rgb_radio.isChecked():
                if self.alpha_channel_checkbox.isChecked():
                    text = 'Raster: RGB, Alpha'
                else:
                    text = 'Raster: RGB'
            elif self.grayscale_radio.isChecked():
                if self.alpha_channel_checkbox.isChecked():
                    text = 'Raster: Grayscale, Alpha'
                else:
                    text = 'Raster: Grayscale'
        elif self.grid_radio.isChecked():
            if self.multi_attribute_grids_only_checkbox.isChecked():
                text = 'Multi-attribute grids'
            else:
                text = 'Grids'
        elif self.table_radio.isChecked():
            if self.table_has_pk_checkbox.isChecked():
                text = 'Tables: Primary key'
            else:
                text = 'Tables'
        elif self.set_radio.isChecked():
            text = 'Sets'
        elif self.data_repository_radio.isChecked():
            text = 'Data repositories'
        elif self.document_radio.isChecked():
            text = 'Documents'

        self.set_current_text(text)