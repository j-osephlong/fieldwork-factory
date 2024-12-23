from __future__ import annotations

import math
import random
from typing import Callable
from uuid import uuid4

from PyQt5.QtCore import pyqtSignal
from qgis.core import QgsGeometry, QgsPointXY, QgsProject, QgsVectorLayer, QgsVectorLayerUtils
from qgis.gui import QgisInterface, QgsMapTool, QgsMapToolEmitPoint
from qgis.PyQt.QtCore import QCoreApplication, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QWidget
from qgis.utils import iface as _iface

from fieldworkbakery.qgis_plugin_tools.tools.custom_logging import setup_logger, teardown_logger
from fieldworkbakery.qgis_plugin_tools.tools.i18n import setup_translation
from fieldworkbakery.qgis_plugin_tools.tools.resources import plugin_name

CODES = [
    "BROOK",
    "DCLB",
    "DCLTB",
    "AES",
    "AECL",
    "SHCL",
    "FCT",
    "SWB",
    "",
    "",
    "FH",
    "WV",
    "WVC",
    "WVMH",
    "WL",
    "SAMH",
    "SA",
    "STMH",
    "CBR",
    "CBSQ",
    "CBP",
    "TEMPSTE",
    "TEMPSTS",
    "ST",
    "CLV",
    "UP",
    "TWR",
    "GUY",
    "CLN",
    "GLN",
    "PLN",
    "LS",
    "HML",
    "CMH",
    "PMH",
    "UGPL",
    "UGGL",
    "UGCL",
    "GB",
    "PJB",
    "URD",
    "CJB",
    "SMFD",
    "IPFD",
    "IBFD",
    "SQIB",
    "SIG",
    "DHFD",
    "RPFD",
    "STMD",
    "CCFD",
    "WS",
    "BLN",
    "SMPL",
    "MON",
    "CP",
    "BM",
    "BLDC",
    "BLDF",
    "BLDS",
    "STEP",
    "DE",
    "OHNG",
    "COL",
    "FLE",
    "EC",
    "CE",
    "AE",
    "GRE",
    "BRE",
    "WDE",
    "RKE",
    "STNE",
    "RIPE",
    "RRAP",
    "GRS",
    "FLRE",
    "EW",
    "EM",
    "TS",
    "BS",
    "DCL",
    "MBL",
    "EL",
    "TR",
    "BR",
    "TWL",
    "BWL",
    "CL",
    "CLG",
    "LN",
    "SH",
    "FC",
    "TBC",
    "SW",
    "CUT",
    "TRL",
    "ANC",
    "RR",
    "RRS",
    "VE",
    "OHWM",
    "BRCL",
    "BRED",
    "WET",
    "SWE",
    "TP",
    "BH",
    "MW",
    "BO",
    "CCB",
    "GRDR",
    "SIGN",
    "VP",
    "WELL",
    "PIC",
    "FNC",
    "FPO",
    "SHB",
    "TREE",
    "HE",
    "PLT",
    "TRHW",
    "TRSW",
    "GCP",
]


# First a generic Map Tool
class NewMapTool(QgsMapToolEmitPoint):
    # Define the custom signal this map tool will have
    # Always needs to be implemented as a class attributes like this
    canvasClicked = pyqtSignal(QgsPointXY)

    def __init__(self, canvas):
        super(QgsMapTool, self).__init__(canvas)
        # ... and so on

    # This is the event triggered when the mouse button is released over the map canvas
    # Then the captured point will be emitted by the custom signal
    def canvasReleaseEvent(self, event):
        point_canvas_crs = event.mapPoint()

        self.canvasClicked.emit(point_canvas_crs)


def get_layer_by_table_name(schema: str, table_name: str) -> QgsVectorLayer:
    layers_dict: dict[str, QgsVectorLayer] = QgsProject.instance().mapLayers()
    layers_list = layers_dict.values()

    src_snippet = f'table="{schema}"."{table_name}"'

    for layer in layers_list:
        src_str = layer.source()
        if src_snippet in src_str:
            return layer
    msg = f"Could not find layer with {src_snippet}."
    raise ValueError(msg)


def translate_geometry_by_meters(geom: QgsGeometry, dx: float, dy: float) -> None:
    """Math borrowed from https://stackoverflow.com/a/50506609/5721675."""
    new_latitude = (180 / math.pi) * (dy / 6378137)
    new_longitude = (180 / math.pi) * (dx / 6378137) / math.cos(geom.asPoint().y())
    geom.translate(new_longitude, new_latitude)


def create_fieldwork(center: QgsPointXY, code_set_offset: int, iface: QgisInterface):
    print("Create fieldwork with center", center)

    fieldwork_layer = get_layer_by_table_name("public", "sites_fieldwork")
    fieldwork_layer_fields = fieldwork_layer.fields()
    fieldwork_layer_id_index = fieldwork_layer_fields.indexFromName("id")
    fieldwork_layer_name_index = fieldwork_layer_fields.indexFromName("name")
    fieldwork_layer_note_index = fieldwork_layer_fields.indexFromName("note")
    fieldworkshot_layer = get_layer_by_table_name("public", "sites_fieldworkshot")
    fieldworkshot_layer_fields = fieldworkshot_layer.fields()
    fieldworkshot_layer_id_index = fieldworkshot_layer_fields.indexFromName("id")
    fieldworkshot_layer_name_index = fieldworkshot_layer_fields.indexFromName("name")
    fieldworkshot_layer_description_index = fieldworkshot_layer_fields.indexFromName("description")
    fieldworkshot_layer_code_index = fieldworkshot_layer_fields.indexFromName("code")
    fieldworkshot_layer_fieldwork_id_index = fieldworkshot_layer_fields.indexFromName("fieldwork_id")

    fieldwork_layer.startEditing()
    fieldworkshot_layer.startEditing()

    code_set = CODES[code_set_offset::5]
    fw_hash = random.getrandbits(24)
    fieldwork_id = str(uuid4())
    fieldwork_name = f"FW-{fw_hash}"
    fieldwork_note = "Generated from fieldwork-bakery plugin."

    try:
        new_fieldwork = QgsVectorLayerUtils.createFeature(fieldwork_layer)

        new_fieldwork[fieldwork_layer_id_index] = fieldwork_id
        new_fieldwork[fieldwork_layer_name_index] = fieldwork_name
        new_fieldwork[fieldwork_layer_note_index] = fieldwork_note

        fieldwork_layer.addFeature(new_fieldwork)
        fieldwork_layer.commitChanges()

        for code in code_set:
            for i in range(5):
                geom = QgsGeometry.fromPointXY(center)
                translate_geometry_by_meters(geom, random.randrange(-1000, 1000), random.randrange(-1000, 1000))  # noqa: S311

                new_fieldworkshot = QgsVectorLayerUtils.createFeature(fieldworkshot_layer)
                new_fieldworkshot[fieldworkshot_layer_id_index] = str(uuid4())
                new_fieldworkshot[fieldworkshot_layer_name_index] = f"FS-{code} #{i + 1} [{fw_hash}]"
                new_fieldworkshot[fieldworkshot_layer_description_index] = (
                    f"{code}/Generated from fieldwork-bakery plugin."
                )
                new_fieldworkshot[fieldworkshot_layer_code_index] = code
                new_fieldworkshot[fieldworkshot_layer_fieldwork_id_index] = fieldwork_id
                new_fieldworkshot.setGeometry(geom)

                fieldworkshot_layer.addFeature(new_fieldworkshot)

        fieldworkshot_layer.commitChanges()
    except:
        fieldwork_layer.rollBack()
        fieldworkshot_layer.rollBack()
        raise


class Plugin:
    """QGIS Plugin Implementation."""

    name = plugin_name()
    iface: QgisInterface
    code_set_offset: int

    def __init__(self) -> None:
        setup_logger(Plugin.name)
        self.code_set_offset = 0
        # initialize locale
        locale, file_path = setup_translation()
        if file_path:
            self.translator = QTranslator()
            self.translator.load(file_path)
            # noinspection PyCallByClass
            QCoreApplication.installTranslator(self.translator)
        else:
            pass

        self.actions: list[QAction] = []
        self.menu = Plugin.name
        self.iface = _iface
        print("Initialized.")  # noqa: T201

    def add_action(
        self,
        icon_path: str,
        text: str,
        callback: Callable,
        *,
        enabled_flag: bool = True,
        add_to_menu: bool = True,
        add_to_toolbar: bool = True,
        status_tip: str | None = None,
        whats_this: str | None = None,
        parent: QWidget | None = None,
    ) -> QAction:
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.

        :param text: Text that should be shown in menu items for this action.

        :param callback: Function to be called when the action is triggered.

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.

        :param parent: Parent widget for the new action. Defaults None.

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        # noinspection PyUnresolvedReferences
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self) -> None:  # noqa N802
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.add_action(
            "",
            text=Plugin.name,
            callback=self.run,
            parent=self.iface.mainWindow(),
            add_to_toolbar=False,
        )

    def onClosePlugin(self) -> None:  # noqa N802
        """Cleanup necessary items here when plugin dockwidget is closed"""

    def unload(self) -> None:
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(Plugin.name, action)
            self.iface.removeToolBarIcon(action)
        teardown_logger(Plugin.name)

    def run(self) -> None:
        """Run method that performs all the real work"""
        print("RUN!!!!")
        self.connect_tool()

    # when this method is called by the plugin it loads our NewMapTool
    # and connect its canvasClicked signal to our custom slot function
    def connect_tool(self):
        print("CONNECT!!!!")
        self.point_tool = NewMapTool(self.iface.mapCanvas())
        self.iface.mapCanvas().setMapTool(self.point_tool)
        self.point_tool.canvasClicked.connect(self.print_wkt)

    # our custom slot function needs to accept the QgsPointXY the signal emits
    def print_wkt(self, point: QgsPointXY):
        create_fieldwork(point, self.code_set_offset, self.iface)
        self.code_set_offset += 1
        if self.code_set_offset >= 5:  # noqa: PLR2004
            self.code_set_offset = 0
        self.iface.mapCanvas().unsetMapTool(self.point_tool)
