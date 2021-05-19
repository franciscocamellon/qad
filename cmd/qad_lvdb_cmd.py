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
from qgis.core import Qgis, QgsProject, QgsWkbTypes, QgsPointXY

from .qad_lvdb_maptool import Qad_lvdb_maptool, Qad_lvdb_maptool_ModeEnum
from .qad_generic_cmd import QadCommandClass
from ..qad_msg import QadMsg
from ..qad_getpoint import QadGetPointDrawModeEnum
from ..qad_textwindow import QadInputModeEnum, QadInputTypeEnum
from .qad_ssget_cmd import QadSSGetClass
from ..qad_entity import QadCacheEntitySet, QadEntityTypeEnum, QadCacheEntitySetIterator
from ..qad_variables import QadVariables

from .. import qad_utils
from .. import qad_layer
from ..qad_dim import QadDimStyles, QadDimEntity, appendDimEntityIfNotExisting
from ..qad_multi_geom import fromQadGeomToQgsGeom
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
        self.maxNumberFuses = QadVariables.get(QadMsg.translate("Environment variables", "MAXNUMBEROFFUSES"))
        self.SSGetClass = QadSSGetClass(plugIn)
        self.SSGetClass.onlyEditableLayers = True
        self.cacheEntitySet = QadCacheEntitySet()
        self.basePt = QgsPointXY()

    def __del__(self):
        QadCommandClass.__del__(self)
        del self.SSGetClass

    def getPointMapTool(self, drawMode = QadGetPointDrawModeEnum.NONE):
      if self.step == 0: # quando si é in fase di selezione entità
         return self.SSGetClass.getPointMapTool()
      else:
         if (self.plugIn is not None):
            if self.PointMapTool is None:
               self.PointMapTool = Qad_lvdb_maptool(self.plugIn)
            return self.PointMapTool
         else:
            return None

    def getCurrentContextualMenu(self):
        if self.step == 0: # quando si é in fase di selezione entità
            return None # return self.SSGetClass.getCurrentContextualMenu()
        else:
            return self.contextualMenu

    #============================================================================
    # FUNCTIONS
    #============================================================================
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
            
            return False, self.showErr(errMsg)
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
                return False

    def getClosedLvQuantity(self):
        selectedFeature = self.isFeatureSelected()
        if selectedFeature:
            fields = selectedFeature[0].fields()
            for field in fields:
                closed = self.getClosedLV(selectedFeature[0][field.name()])
                if closed == 'CLOSED:':
                    self.lvFuse += 1
            return '0', self.lvFuse

    def getClosedLV(self, attribute):
        try:
            if attribute:
                regex = re.compile(r'\bclosed:\b', re.IGNORECASE)
                closedLV = regex.findall(attribute)
            return closedLV[0]
        except:
            pass

    def run(self, msgMapTool = False, msg = None):
        if self.plugIn.canvas.mapSettings().destinationCrs().isGeographic():
            self.showMsg(QadMsg.translate(
                "QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
            return True  # fine comando

        currLayer, errMsg = getCurrLayerEditable(
            self.plugIn.canvas, [QgsWkbTypes.PointGeometry])
        if currLayer is None:
            self.showErr(errMsg)
            return True 

        #=========================================================================
        # RICHIESTA SELEZIONE OGGETTI
        if self.step == 0: # inizio del comando
            if self.SSGetClass.run(msgMapTool, msg) == True:
            # selezione terminata
                self.step = 1
                self.getPointMapTool().refreshSnapType() # aggiorno lo snapType che può essere variato dal maptool di selezione entità                    
                return self.run(msgMapTool, msg)

        #=========================================================================
        # SPOSTA OGGETTI
        elif self.step == 1: # VERIFICAR POR SELEÇÃO MAIOR QUE UM
            if self.SSGetClass.entitySet.count() == 0:
                return True # fine comando
            self.cacheEntitySet.appendEntitySet(self.SSGetClass.entitySet)
            a = self.cacheEntitySet.count()
            print(a)

            # imposto il map tool
            self.getPointMapTool().cacheEntitySet = self.cacheEntitySet
            self.getPointMapTool().setMode(Qad_lvdb_maptool_ModeEnum.ASK_FOR_LV_FUSE_NUMBER)
            min, max = self.getClosedLvQuantity()                                

            keyWords = QadMsg.translate("Command_LVDB", str(min))  + "/" + QadMsg.translate("Command_LVDB", str(max))
            default = QadMsg.translate("Command_LVDB", "All")
            prompt = QadMsg.translate("Command_LVDB", "Specify number of fuses to draw [{0}] <{1}>: ").format(keyWords, default)
            
            englishKeyWords = str(min) + "/" + str(max)
            keyWords += "_" + englishKeyWords
            # si appresta ad attendere un punto o enter o una parola chiave         
            # msg, inputType, default, keyWords, nessun controllo
            self.waitFor(prompt, \
                        QadInputTypeEnum.INT | QadInputTypeEnum.KEYWORDS, \
                        default, \
                        keyWords, \
                        QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)      
            self.step = 2      
            return False

        #=========================================================================
        # RISPOSTA ALLA RICHIESTA PUNTO BASE (da step = 1)
        elif self.step == 2:
            if msgMapTool == True:
                if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
                    if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                        pass # opzione di default "spostamento"
                    else:
                        self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                        return False

                value = self.getPointMapTool().point
            else: # il punto arriva come parametro della funzione
                value = msg

            if value is None or type(value) == unicode:
                self.basePt.set(0, 0)
                self.getPointMapTool().basePt = self.basePt
                self.getPointMapTool().setMode(Qad_lvdb_maptool_ModeEnum.FUSE_NUMBER_KNOWN_ASK_FOR_LVDBFP_ANGLE)                                
                keyWords = QadMsg.translate("Command_LVDB", "Yes")  + "/" + QadMsg.translate("Command_LVDB", "Fill")
                default = QadMsg.translate("Command_OFFSET", "Fill")
                prompt = QadMsg.translate("Command_LVDB", "Insert the angle of lvdb-fp or auto fill [{0}] <{1}>: ").format(keyWords, default)
                
                englishKeyWords = "Yes" + "/" + "Fill"
                keyWords += "_" + englishKeyWords                               
                
                # si appresta ad attendere un punto o enter o una parola chiave         
                # msg, inputType, default, keyWords, nessun controllo
                self.waitFor(prompt, \
                            QadInputTypeEnum.STRING | QadInputTypeEnum.KEYWORDS, \
                            default, \
                            keyWords, \
                            QadInputModeEnum.NOT_NULL)
                self.step = 3

            elif type(value) == QgsPointXY: # se é stato inserito il punto base
                self.basePt.set(value.x(), value.y())

                # imposto il map tool
                self.getPointMapTool().basePt = self.basePt
                self.getPointMapTool().setMode(Qad_lvdb_maptool_ModeEnum.FUSE_NUMBER_KNOWN_ASK_FOR_LVDBFP_ANGLE)

                keyWords = QadMsg.translate("Command_LVDB", "Yes")  + "/" + QadMsg.translate("Command_LVDB", "Fill")
                default = QadMsg.translate("Command_OFFSET", "Fill")
                prompt = QadMsg.translate("Command_LVDB", "Insert the angle of lvdb-fp or auto fill [{0}] <{1}>: ").format(keyWords, default)
                
                englishKeyWords = "Yes" + "/" + "Fill"
                keyWords += "_" + englishKeyWords                               
                
                # si appresta ad attendere un punto o enter o una parola chiave         
                # msg, inputType, default, keyWords, nessun controllo
                self.waitFor(prompt, \
                            QadInputTypeEnum.KEYWORDS, \
                            default, \
                            keyWords, \
                            QadInputModeEnum.NOT_NULL)      
                self.step = 3      
            
            return False