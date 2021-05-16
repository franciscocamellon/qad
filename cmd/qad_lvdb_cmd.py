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
from qgis.core import Qgis, QgsProject, QgsWkbTypes


from .qad_generic_cmd import QadCommandClass
from ..qad_textwindow import QadInputModeEnum, QadInputTypeEnum
from .. import qad_layer
from ..qad_msg import QadMsg
from ..qad_layer import getLayersByName


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

   def verifyLoadedLayer(self):
      msgType = QadMsg.translate("Command_LVDB", "Error")
      msgText = QadMsg.translate(
         "Command_LVDB", "The LVDB-FP layer does not loaded!")
      layer = getLayersByName('LVDB-FP')
      if layer:
         selectedFeature = [feature for feature in layer[0].getSelectedFeatures()]
         if len(selectedFeature) > 0:
            pass
         else:
            # self.waitForPoint()
            
            iface.messageBar().pushMessage(msgType,
                                          'Selecione uma feicao',
                                          level=Qgis.Critical,
                                          duration=5)
            return None, self.showMsg(QadMsg.translate("QAD", '\nSelecione uma feicao\n'))
      else:
         iface.messageBar().pushMessage(msgType,
                                          msgText,
                                          level=Qgis.Critical,
                                          duration=5)

   def getCurrLayerEditable(canvas, layer, geomType = None):
      """
      Ritorna il layer corrente se é aggiornabile e compatibile con il tipo geomType +
      eventuale messaggio di errore.
      Se <geomType> é una lista allora verifica che sia compatibile con almeno un tipo nella lista <geomType>
      altrimenti se <> None verifica che sia compatibile con il tipo <geomType>
      """
      vLayer = canvas.currentLayer()
      if vLayer is None:
         return None, QadMsg.translate("QAD", "\nNo current layer.\n")
      
      if (vLayer.type() != QgsMapLayer.VectorLayer):
         return None, QadMsg.translate("QAD", "\nThe current layer is not a vector layer.\n")

      if geomType is not None:
         if (type(geomType) == list or type(geomType) == tuple): # se lista di tipi
            if vLayer.geometryType() not in geomType:
               errMsg = QadMsg.translate("QAD", "\nThe geometry type of the current layer is {0} and it is not valid.\n")
               errMsg = errMsg + QadMsg.translate("QAD", "Admitted {1} layer type only.\n")
               errMsg.format(qad_layer.layerGeometryTypeToStr(vLayer.geometryType()), qad_layer.layerGeometryTypeToStr(geomType))
               return None, errMsg.format(qad_layer.layerGeometryTypeToStr(vLayer.geometryType()), qad_layer.layerGeometryTypeToStr(geomType))
         else:
            if vLayer.geometryType() != geomType:
               errMsg = QadMsg.translate("QAD", "\nThe geometry type of the current layer is {0} and it is not valid.\n")
               errMsg = errMsg + QadMsg.translate("QAD", "Admitted {1} layer type only.\n")
               errMsg.format(qad_layer.layerGeometryTypeToStr(vLayer.geometryType()), qad_layer.layerGeometryTypeToStr(geomType))
               return None, errMsg.format(qad_layer.layerGeometryTypeToStr(vLayer.geometryType()), qad_layer.layerGeometryTypeToStr(geomType))

      provider = vLayer.dataProvider()
      if not (provider.capabilities() & QgsVectorDataProvider.EditingCapabilities):
         return None, QadMsg.translate("QAD", "\nThe current layer is not editable.\n")
      
      if not vLayer.isEditable():
         return None, QadMsg.translate("QAD", "\nThe current layer is not editable.\n")

      return vLayer, None

   def run(self):
      self.verifyLoadedLayer()
      if self.plugIn.canvas.mapSettings().destinationCrs().isGeographic():
         self.showMsg(QadMsg.translate("QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
         return True # fine comando

      # il layer corrente deve essere editabile e di tipo linea o poligono
      currLayer, errMsg = qad_layer.getCurrLayerEditable(self.plugIn.canvas, [QgsWkbTypes.PointGeometry])
      if currLayer is None:
         self.showErr(errMsg)
         return True # fine comando
