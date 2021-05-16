# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAD Quantum Aided Design plugin

 comando VSETUP che apre la guida di QAD

                              -------------------
        begin                : 2015-08-31
        copyright            : iiiii
        email                : hhhhh
        developers           : bbbbb aaaaa ggggg
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
import json

# Import the PyQt and QGIS libraries
from qgis.PyQt.QtGui import *
from qgis.utils import iface
from qgis.core import Qgis, QgsProject, QgsEditorWidgetSetup


from .qad_generic_cmd import QadCommandClass
from ..qad_msg import QadMsg
from ..qad_layer import getLayersByName


# Classe che gestisce il comando VSETUP
class QadLVUGCommandClass(QadCommandClass):

    def instantiateNewCmd(self):
        """ istanzia un nuovo comando dello stesso tipo """
        return QadLVUGCommandClass(self.plugIn)

    def getName(self):
        return QadMsg.translate("Command_list", "LVUG")

    def getEnglishName(self):
        return "LVUG"

    def connectQAction(self, action):
        action.triggered.connect(self.plugIn.runLVUGCommand)

    def getIcon(self):
        return QIcon(":/plugins/qad/icons/lvug.png")

    def getNote(self):
        # impostare le note esplicative del comando
        return QadMsg.translate("Command_LVUG", "Configures the value map from the attributes")

    def __init__(self, plugIn):
        QadCommandClass.__init__(self, plugIn)

    def identifyLVDBLayer(self):
        msgType = QadMsg.translate("Command_LVDB", "Error")
        msgText = QadMsg.translate(
            "Command_LVDB", "The LVDB-FP layer does not loaded!")
        layer = getLayersByName('LVDB-FP')
        if layer:
            pass
        else:
            iface.messageBar().pushMessage(msgType,
                                           msgText,
                                           level=Qgis.Critical,
                                           duration=5)

    def run(self):
        self.identifyLVDBLayer()
        return True
