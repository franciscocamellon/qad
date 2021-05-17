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
import re

# Import the PyQt and QGIS libraries
from qgis.PyQt.QtGui import *
from qgis.utils import iface
from qgis.core import Qgis, QgsProject, QgsWkbTypes

from .qad_lvdb_maptool import Qad_lvdb_maptool, Qad_lvdb_maptool_ModeEnum
from .qad_generic_cmd import QadCommandClass
from ..qad_textwindow import QadInputModeEnum, QadInputTypeEnum
from ..qad_getpoint import QadGetPointDrawModeEnum
from .. import qad_layer
from ..qad_msg import QadMsg
from ..qad_layer import getLayersByName, getCurrLayerEditable


# Classe che gestisce il comando VSETUP
class QadLVDBCommandClass(QadCommandClass):

    def instantiateNewCmd(self):
        """ istanzia un nuovo comando dello stesso tipo """
        return QadLVDBCommandClass(self.plugIn)

    def getName(self):
        return QadMsg.translate("Command_list", "LVDB")

    def getEnglishName(self):
        return "LVDB"

    def connectQAction(self, action):
        action.triggered.connect(self.plugIn.runLVDBCommand)

    def getIcon(self):
        return QIcon(":/plugins/qad/icons/lvdb.png")

    def getNote(self):
        # impostare le note esplicative del comando
        return QadMsg.translate("Command_LVDB", "Configures the value map from the attributes")

    def __init__(self, plugIn):
        QadCommandClass.__init__(self, plugIn)
        self.iface = self.plugIn.iface
        self.targetLayer = 'LVDB-FP'
        self.lvFuse = 0

    def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if (self.plugIn is not None):
         if self.PointMapTool is None:
            self.PointMapTool = Qad_lvdb_maptool(self.plugIn)
         return self.PointMapTool
      else:
         return None

    def isLoadedLayer(self):
        layer = getLayersByName(self.targetLayer)
        msgType = QadMsg.translate("Command_LVDB", "Error")
        msgText = '\nThe {} layer is not loaded!\n'.format(self.targetLayer)
        if layer:
            self.iface.setActiveLayer(layer[0])
        else:
            iface.messageBar().pushMessage(msgType,
                                           msgText,
                                           level=Qgis.Critical,
                                           duration=5)
            return None, self.showMsg(QadMsg.translate("QAD", msgText))

    def isEditable(self):
        currLayer, errMsg = getCurrLayerEditable(
            self.plugIn.canvas, [QgsWkbTypes.PointGeometry])
        if currLayer is None:
            self.showErr(errMsg)
            return False, currLayer
        else:
            return True, currLayer

    def isFeatureSelected(self):
        editable, layer = self.isEditable()
        if editable:
            selectedFeature = [
                feature for feature in layer.getSelectedFeatures()]
            featLen = len(selectedFeature)
            if featLen == 1:
                return selectedFeature
            elif featLen == 0 or featLen > 1:
                self.showMsg(QadMsg.translate(
                    "QAD", '\nPlease select one feature from {}.\n'.format(layer.name())))

    def getClosedLvQuantity(self):
        selectedFeature = self.isFeatureSelected()
        if selectedFeature:
            fields = selectedFeature[0].fields()
            for field in fields:
                closed = self.getClosedLV(selectedFeature[0][field.name()])
                if closed == 'CLOSED:':
                    self.lvFuse += 1
            return self.lvFuse

    def getClosedLV(self, attribute):
        try:
            if attribute:
                regex = re.compile(r'\bclosed:\b', re.IGNORECASE)
                closedLV = regex.findall(attribute)
            return closedLV[0]
        except:
            pass

    # ============================================================================
    # waitForNumOfLvFuse
    # ============================================================================
    def waitForNumOfLvFuse(self):      
        # imposto il map tool
        self.getPointMapTool().setMode(Qad_lvdb_maptool_ModeEnum.ASK_FOR_LV_FUSE_NUMBER)
        self.getPointMapTool().gapType = self.gapType                        

        keyWords = QadMsg.translate("Command_OFFSET", "All") + "/" + \
                    QadMsg.translate("Command_OFFSET", "None")                
        default = QadMsg.translate("Command_OFFSET", "None")
        prompt = QadMsg.translate("Command_OFFSET", "Specify the number of LV fuse to draw [{0}] <{1}>: ").format(keyWords, unicode(default))

        englishKeyWords = "All" + "/" + "None"
        keyWords += "_" + englishKeyWords
        # si appresta ad attendere un punto o enter o una parola chiave o un numero reale     
        # msg, inputType, default, keyWords, nessun controllo
        self.waitFor(prompt, \
                    QadInputTypeEnum.POINT2D | QadInputTypeEnum.FLOAT | QadInputTypeEnum.KEYWORDS, \
                    default, \
                    keyWords, \
                    QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)      
        self.step = 1 



    def run(self):
        self.isLoadedLayer()
        self.getClosedLvQuantity()
        if self.plugIn.canvas.mapSettings().destinationCrs().isGeographic():
            self.showMsg(QadMsg.translate(
                "QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
            return True  # fine comando

        # il layer corrente deve essere editabile e di tipo linea o poligono
