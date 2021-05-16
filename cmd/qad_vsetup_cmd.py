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
from ..qad_utils import findFile
from ..qad_msg import QadMsg


# Classe che gestisce il comando VSETUP
class QadVSETUPCommandClass(QadCommandClass):

   def instantiateNewCmd(self):
      """ istanzia un nuovo comando dello stesso tipo """
      return QadVSETUPCommandClass(self.plugIn)

   def getName(self):
      return QadMsg.translate("Command_list", "VSETUP")

   def getEnglishName(self):
      return "VSETUP"

   def connectQAction(self, action):
      action.triggered.connect(self.plugIn.runVSETUPCommand)

   def getIcon(self):
      return QIcon(":/plugins/qad/icons/variable.png")

   def getNote(self):
      # impostare le note esplicative del comando
      return QadMsg.translate("Command_VSETUP", "Configures the value map from the attributes")

   def __init__(self, plugIn):
      QadCommandClass.__init__(self, plugIn)

   def getAttrValueMap(self):
      """Docstring"""
      cwd = os.path.dirname(__file__)
      configFile = os.path.join(cwd, 'attrValueMap.json')
      with open(configFile, "r") as json_file:
         attrValueMap = json.load(json_file)
         json_file.close()
      return attrValueMap

   def getLoadedLayers(self):
      """Docstring"""
      loadedLayers = list()
      layers = QgsProject.instance().mapLayers().values()

      for layer in layers:
         if layer.type() == 0:
               loadedLayers.append(layer)
         else:
               pass
      return loadedLayers

   def setEditorWidgetSetup(self, layer, fieldName, mapConfig):
      """Docstring"""
      layerIdx = layer.fields().indexOf(fieldName)
      setup = QgsEditorWidgetSetup('ValueMap', mapConfig)
      layer.setEditorWidgetSetup(layerIdx, setup)

   def editorWidgetSetup(self):
      """Docstring"""
      layers = self.getLoadedLayers()
      attrValueMap = self.getAttrValueMap()

      for layer in layers:
         fields = layer.fields()
         for field in fields:
               if field.name() in attrValueMap[layer.name()]:
                  self.setEditorWidgetSetup(layer,
                                             field.name(),
                                             attrValueMap[layer.name()][field.name()])
      iface.messageBar().pushMessage("Info",
                                    "Value map configuration done",
                                    level=Qgis.Info,
                                    duration=3)
        
   def run(self, msgMapTool = False, msg = None):
      self.editorWidgetSetup()       
      return True
