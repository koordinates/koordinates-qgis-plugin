from typing import Set

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
    DataType,
    RasterFilter,
    RasterFilterOptions,
    RasterBandFilter,
    VectorFilter,
    GridFilterOptions,
)


class DataTypeFilterWidget(FilterWidgetComboBase):
    """
    Custom widget for data type filtering
    """

    def __init__(self, parent):
        super().__init__(parent)

        self._block_geometry_type_constraint_update = 0

        self.drop_down_widget = QWidget()
        vl = QVBoxLayout()

        self.layers_radio = QRadioButton('Layers')
        vl.addWidget(self.layers_radio)

        self.layers_widget = QWidget()
        layers_widget_layout = QVBoxLayout()
        layers_widget_layout.setContentsMargins(self._indent_margin, 0, 0, 0)

        self.vector_radio = QRadioButton('Vectors')
        layers_widget_layout.addWidget(self.vector_radio)

        self.vector_frame = QWidget()
        vector_frame_layout = QVBoxLayout()
        vector_frame_layout.setContentsMargins(self._indent_margin, 0, 0, 0)

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
        raster_frame_layout.setContentsMargins(self._indent_margin, 0, 0, 0)

        self.aerial_radio = QRadioButton('Aerial && satellite photos')
        raster_frame_layout.addWidget(self.aerial_radio)
        self.not_aerial_radio = QRadioButton('Not aerial && satellite photos')
        raster_frame_layout.addWidget(self.not_aerial_radio)
        self.band_radio = QRadioButton('By band')
        raster_frame_layout.addWidget(self.band_radio)

        self.raster_band_frame = QWidget()
        raster_band_frame_layout = QVBoxLayout()
        raster_band_frame_layout.setContentsMargins(self._indent_margin, 0, 0, 0)

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
        grid_frame_layout.setContentsMargins(self._indent_margin, 0, 0, 0)
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
        table_frame_layout.setContentsMargins(self._indent_margin, 0, 0, 0)
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

        self.type_radios = (
            self.layers_radio,
            self.vector_radio,
            self.raster_radio,
            self.aerial_radio,
            self.not_aerial_radio,
            self.band_radio,
            self.rgb_radio,
            self.grayscale_radio,
            self.grid_radio,
            self.table_radio,
            self.set_radio,
            self.data_repository_radio,
            self.document_radio
        )

        self.data_type_group = QButtonGroup(self)
        for radio in self.type_radios:
            self.data_type_group.addButton(radio)
        self.data_type_group.setExclusive(False)

        self.data_type_group.buttonClicked.connect(self._type_group_member_clicked)
        self._enforce_geometry_type_constraints()
        self.rgb_radio.setChecked(True)
        self.layers_radio.setChecked(True)

        self.band_radio.toggled.connect(self._update_value)
        self.alpha_channel_checkbox.toggled.connect(self._update_value)
        self.multi_attribute_grids_only_checkbox.toggled.connect(self._update_value)
        self.table_has_pk_checkbox.toggled.connect(self._update_value)
        self.point_checkbox.toggled.connect(self._update_value)
        self.line_checkbox.toggled.connect(self._update_value)
        self.polygon_checkbox.toggled.connect(self._update_value)
        self.has_z_elevation_checkbox.toggled.connect(self._update_value)
        self.vector_has_primary_key_checkbox.toggled.connect(self._update_value)

        self.clear()

    def _type_group_member_clicked(self, clicked_button):
        self._block_changes += 1
        for radio in self.type_radios:
            if radio.isChecked() and radio != clicked_button:
                radio.setChecked(False)

        if clicked_button in (self.aerial_radio,
                              self.not_aerial_radio,
                              self.band_radio,
                              self.rgb_radio,
                              self.grayscale_radio):
            self.raster_radio.setChecked(True)

        if clicked_button in (self.rgb_radio,
                              self.grayscale_radio):
            self.band_radio.setChecked(clicked_button.isChecked())

        if clicked_button == self.band_radio and \
                not self.grayscale_radio.isChecked() and \
                not self.rgb_radio.isChecked():
            self.rgb_radio.setChecked(True)

        if not any(radio.isChecked() for radio in self.type_radios):
            self.layers_radio.setChecked(True)

        self._block_changes -= 1
        self._update_visible_frames()
        self._update_value()

    def _update_visible_frames(self):
        self.vector_frame.setVisible(self.vector_radio.isChecked())
        self.raster_band_frame.setVisible(self.band_radio.isChecked())

        should_show_raster_group = self.raster_radio.isChecked() or \
            self.aerial_radio.isChecked() or \
            self.not_aerial_radio.isChecked() or \
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
        self._block_changes += 1
        self.layers_radio.setChecked(True)
        self.raster_radio.setChecked(False)
        self.aerial_radio.setChecked(False)
        self.not_aerial_radio.setChecked(False)
        self.rgb_radio.setChecked(False)
        self.band_radio.setChecked(False)
        self.grayscale_radio.setChecked(False)
        self.vector_radio.setChecked(False)
        self.grid_radio.setChecked(False)
        self._block_changes -= 1

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
            if self.point_checkbox.isChecked() and \
                    self.line_checkbox.isChecked() and \
                    self.polygon_checkbox.isChecked():
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

        elif self.raster_radio.isChecked() and not self.aerial_radio.isChecked() and \
                not self.not_aerial_radio.isChecked() and not self.band_radio.isChecked():
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
        if not self._block_changes:
            self.changed.emit()

    def data_types(self) -> Set[DataType]:
        """
        Returns the set of selected data types
        """
        types = set()
        if self.layers_radio.isChecked():
            types = {DataType.Vectors, DataType.Rasters, DataType.Grids}
        elif self.vector_radio.isChecked():
            types = {DataType.Vectors}
        elif any((self.raster_radio.isChecked(),
                  self.aerial_radio.isChecked(),
                  self.not_aerial_radio.isChecked(),
                  self.band_radio.isChecked())):
            types = {DataType.Rasters}
        elif self.grid_radio.isChecked():
            types = {DataType.Grids}
        elif self.table_radio.isChecked():
            types = {DataType.Tables}
        elif self.set_radio.isChecked():
            types = {DataType.Sets}
        elif self.data_repository_radio.isChecked():
            types = {DataType.Repositories}
        elif self.document_radio.isChecked():
            types = {DataType.Documents}

        return types

    def apply_constraints_to_query(self, query: DataBrowserQuery):
        if self.layers_radio.isChecked():
            query.data_types = {DataType.Vectors, DataType.Rasters, DataType.Grids}
        elif self.vector_radio.isChecked():
            query.data_types = {DataType.Vectors}
            if self.point_checkbox.isChecked() and \
                    self.line_checkbox.isChecked() and \
                    self.polygon_checkbox.isChecked():
                pass
            else:
                if self.point_checkbox.isChecked():
                    query.vector_filters.add(VectorFilter.Point)
                if self.line_checkbox.isChecked():
                    query.vector_filters.add(VectorFilter.Line)
                if self.polygon_checkbox.isChecked():
                    query.vector_filters.add(VectorFilter.Polygon)

            if self.has_z_elevation_checkbox.isChecked():
                query.vector_filters.add(VectorFilter.HasZ)
            if self.vector_has_primary_key_checkbox.isChecked():
                query.vector_filters.add(VectorFilter.HasPrimaryKey)

        elif self.raster_radio.isChecked() and not self.aerial_radio.isChecked() and \
                not self.not_aerial_radio.isChecked() and not self.band_radio.isChecked():
            query.data_types = {DataType.Rasters}
        elif self.aerial_radio.isChecked():
            query.data_types = {DataType.Rasters}
            query.raster_filters = {RasterFilter.AerialSatellitePhotos}
        elif self.not_aerial_radio.isChecked():
            query.data_types = {DataType.Rasters}
            query.raster_filters = {RasterFilter.NotAerialSatellitePhotos}
        elif self.band_radio.isChecked():
            query.data_types = {DataType.Rasters}
            query.raster_filters = {RasterFilter.ByBand}
            if self.rgb_radio.isChecked():
                query.raster_band_filters = {RasterBandFilter.RGB}
            elif self.grayscale_radio.isChecked():
                query.raster_band_filters = {RasterBandFilter.BlackAndWhite}
        elif self.grid_radio.isChecked():
            query.data_types = {DataType.Grids}
            if self.multi_attribute_grids_only_checkbox.isChecked():
                query.grid_filter_options.add(GridFilterOptions.MultiAttributeGridsOnly)
        elif self.table_radio.isChecked():
            query.data_types = {DataType.Tables}
            if self.table_has_pk_checkbox.isChecked():
                query.vector_filters.add(VectorFilter.HasPrimaryKey)
        elif self.set_radio.isChecked():
            query.data_types = {DataType.Sets}
        elif self.data_repository_radio.isChecked():
            query.data_types = {DataType.Repositories}
        elif self.document_radio.isChecked():
            query.data_types = {DataType.Documents}

        if DataType.Rasters in query.data_types and self.alpha_channel_checkbox.isChecked():
            query.raster_filter_options.add(RasterFilterOptions.WithAlphaChannel)

    def set_from_query(self, query: DataBrowserQuery):
        self._block_changes += 1

        type_radio = None
        if query.data_types == {DataType.Vectors, DataType.Rasters, DataType.Grids}:
            type_radio = self.layers_radio
        elif query.data_types == {DataType.Vectors}:
            type_radio = self.vector_radio
            if not query.vector_filters:
                self.point_checkbox.setChecked(True)
                self.line_checkbox.setChecked(True)
                self.polygon_checkbox.setChecked(True)
            else:
                self.point_checkbox.setChecked(VectorFilter.Point in query.vector_filters)
                self.line_checkbox.setChecked(VectorFilter.Line in query.vector_filters)
                self.polygon_checkbox.setChecked(VectorFilter.Polygon in query.vector_filters)

            self.has_z_elevation_checkbox.setChecked(VectorFilter.HasZ in query.vector_filters)
            self.vector_has_primary_key_checkbox.setChecked(
                VectorFilter.HasPrimaryKey in query.vector_filters
            )
        elif query.data_types == {DataType.Rasters}:
            type_radio = self.raster_radio
            if RasterFilter.AerialSatellitePhotos in query.raster_filters:
                self.aerial_radio.setChecked(True)
            if RasterFilter.NotAerialSatellitePhotos in query.raster_filters:
                self.not_aerial_radio.setChecked(True)
            if RasterFilter.ByBand in query.raster_filters:
                self.band_radio.setChecked(True)
                if RasterBandFilter.RGB in query.raster_band_filters:
                    self.rgb_radio.setChecked(True)
                if RasterBandFilter.BlackAndWhite in query.raster_band_filters:
                    self.grayscale_radio.setChecked(True)
        elif query.data_types == {DataType.Grids}:
            type_radio = self.grid_radio
            self.multi_attribute_grids_only_checkbox.setChecked(
                GridFilterOptions.MultiAttributeGridsOnly in query.grid_filter_options)
        elif query.data_types == {DataType.Tables}:
            type_radio = self.table_radio
            self.table_has_pk_checkbox.setChecked(
                VectorFilter.HasPrimaryKey in query.vector_filters
            )
        elif query.data_types == {DataType.Sets}:
            type_radio = self.set_radio
        elif query.data_types == {DataType.Repositories}:
            type_radio = self.data_repository_radio
        elif query.data_types == {DataType.Documents}:
            type_radio = self.document_radio

        if DataType.Rasters in query.data_types:
            self.alpha_channel_checkbox.setChecked(
                RasterFilterOptions.WithAlphaChannel in query.raster_filter_options
            )

        for radio in self.type_radios:
            radio.setChecked(radio == type_radio)

        self._update_visible_frames()
        self._update_value()
        self._block_changes -= 1
