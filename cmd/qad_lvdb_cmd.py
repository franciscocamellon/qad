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
from qgis.core import Qgis, QgsProject, QgsWkbTypes, QgsPointXY, QgsGeometry, QgsFeature

from .qad_lvdb_maptool import Qad_lvdb_maptool, Qad_lvdb_maptool_ModeEnum
from .qad_generic_cmd import QadCommandClass
from ..qad_msg import QadMsg
from ..qad_getpoint import QadGetPointDrawModeEnum
from ..qad_textwindow import QadInputModeEnum, QadInputTypeEnum
from .qad_ssget_cmd import QadSSGetClass
from ..qad_entity import QadCacheEntitySet, QadEntityTypeEnum, QadCacheEntitySetIterator, QadEntity
from ..qad_variables import QadVariables

from .. import qad_lvdb_fun
from .. import qad_utils
from .. import qad_layer
from ..qad_dim import QadDimStyles, QadDimEntity, appendDimEntityIfNotExisting
from ..qad_multi_geom import fromQadGeomToQgsGeom
from ..qad_layer import getLayersByName, getCurrLayerEditable
from ..qad_rubberband import createRubberBand


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
        self.entity = QadEntity()
        self.targetLayer = 'LVDB-FP'
        self.lvFuseCount = 0
        self.parameters = dict()
        self.maxNumberFuses = QadVariables.get(
            QadMsg.translate("Environment variables", "MAXNUMBEROFFUSES"))
        self.SSGetClass = QadSSGetClass(plugIn)
        self.SSGetClass.onlyEditableLayers = True
        self.cacheEntitySet = QadCacheEntitySet()
        self.basePt = QgsPointXY()
        self.featureCache = []
        self.undoFeatureCacheIndexes = []
        self.rubberBand = createRubberBand(self.plugIn.canvas, QgsWkbTypes.LineGeometry)

    def __del__(self):
        QadCommandClass.__del__(self)
        del self.SSGetClass

    def getPointMapTool(self, drawMode=QadGetPointDrawModeEnum.NONE):
        if self.step == 0:  # quando si é in fase di selezione entità
            return self.SSGetClass.getPointMapTool()
        else:
            if (self.plugIn is not None):
                if self.PointMapTool is None:
                    self.PointMapTool = Qad_lvdb_maptool(self.plugIn)
                return self.PointMapTool
            else:
                return None

    def getCurrentContextualMenu(self):
        if self.step == 0:  # quando si é in fase di selezione entità
            return None  # return self.SSGetClass.getCurrentContextualMenu()
        else:
            return self.contextualMenu

    # ============================================================================
    # FUNCTIONS
    # ============================================================================
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

    def getClosedLvRange(self):
        selectedFeature = self.isFeatureSelected()
        if selectedFeature:
            fields = selectedFeature[0].fields()
            for field in fields:
                lvFuse = self.getClosedLV(selectedFeature[0][field.name()])
                if lvFuse == 'CLOSED:':
                    self.lvFuseCount += 1
            self.lvFuseCount += 1
            return range(1,self.lvFuseCount)

    def getClosedLV(self, attribute):
        try:
            if attribute:
                regex = re.compile(r'\bclosed:\b', re.IGNORECASE)
                closedLV = regex.findall(attribute)
            return closedLV[0]
        except:
            pass

    def getLvdbAngle(self):
        selectedFeature = self.isFeatureSelected()
        if selectedFeature:
            angleField = selectedFeature[0]["lvdb_angle"]
        return int(angleField)

    # ============================================================================
    # END FUNCTIONS
    # ============================================================================


    #============================================================================
    # addFeatureCache
    #============================================================================
    def addFeatureCache(self, entity, lineType):
        featureCacheLen = len(self.featureCache)
        layer = getLayersByName('LV_UG_Conductor')
        layer[0].startEditing()
        f = entity.getFeature()
        angle = self.getLvdbAngle()

        if lineType == 'ref':
            refLineList = qad_lvdb_fun.drawReferenceLines(entity, angle)
        elif lineType == 'in':
            refLineList = qad_lvdb_fun.drawInConductor(self.basePoint, self.parameters["lvdbAngle"])
        elif lineType == 'out':
            refLineList = qad_lvdb_fun.drawOutConductor(self.basePoint, self.parameters["lvFuseToDraw"], angle)
            # refLineList = qad_lvdb_fun.drawRefOutConductor(self.basePoint, angle)
            

        added = False
        for line in refLineList:
            refLineGeom = QgsGeometry.fromPolylineXY(line)

            if refLineGeom.type() == QgsWkbTypes.LineGeometry:
                refLineFeat = QgsFeature()
                # trasformo la geometria nel crs del layer
                refLineFeat.setGeometry(self.mapToLayerCoordinates(layer[0], refLineGeom))
                self.featureCache.append([layer[0], refLineFeat])
                self.addFeatureToRubberBand(layer[0], refLineFeat)            
                added = True           

        if added:      
            self.undoFeatureCacheIndexes.append(featureCacheLen)


    #============================================================================
    # undoGeomsInCache
    #============================================================================
    def undoGeomsInCache(self):
        tot = len(self.featureCache)
        if tot > 0:
            iEnd = self.undoFeatureCacheIndexes[-1]
            i = tot - 1
            
            del self.undoFeatureCacheIndexes[-1] # cancello ultimo undo
            while i >= iEnd:
                del self.featureCache[-1] # cancello feature
                i = i - 1
            self.refreshRubberBand()

                
    #============================================================================
    # addFeatureToRubberBand
    #============================================================================
    def addFeatureToRubberBand(self, layer, feature):
        if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            if feature.geometry().type() == QgsWkbTypes.PolygonGeometry:
                self.rubberBandPolygon.addGeometry(feature.geometry(), layer)
            else:
                self.rubberBand.addGeometry(feature.geometry(), layer)
        else:
            self.rubberBand.addGeometry(feature.geometry(), layer)
        
        
    #============================================================================
    # refreshRubberBand
    #============================================================================
    def refreshRubberBand(self):
        self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        for f in self.featureCache:
            layer = f[0]
            feature = f[1]
            if layer.geometryType() == QgsWkbTypes.LineGeometry:
                if feature.geometry().type() == QgsWkbTypes.LineGeometry:
                    self.rubberBand.addGeometry(feature.geometry(), layer)
            
    def addFromRubberbandToLayer(self):
        layer = getLayersByName('LV_UG_Conductor')[0]
        provider = layer.dataProvider()
        line = QgsFeature()
        lista = list()
        for f in self.featureCache:
            lista.append(f[1])
            # layer = f[0]
            # feature = f[1]
        provider.addFeatures(lista)
        
        layer.triggerRepaint()
        self.undoGeomsInCache()





    def run(self, msgMapTool=False, msg=None):
        if self.plugIn.canvas.mapSettings().destinationCrs().isGeographic():
            self.showMsg(QadMsg.translate(
                "QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
            return True  # fine comando

        currLayer, errMsg = getCurrLayerEditable(
            self.plugIn.canvas, [QgsWkbTypes.PointGeometry])
        if currLayer is None:
            self.showErr(errMsg)
            return True

        # =========================================================================
        # RICHIESTA SELEZIONE OGGETTI
        if self.step == 0:  # inizio del comando
            if self.SSGetClass.run(msgMapTool, msg) == True:
                # selezione terminata
                self.step = 1
                # aggiorno lo snapType che può essere variato dal maptool di selezione entità
                self.getPointMapTool().refreshSnapType()
                return self.run(msgMapTool, msg)

        # =========================================================================
        # SPOSTA OGGETTI
        elif self.step == 1:  # VERIFICAR POR SELEÇÃO MAIOR QUE UM
            if self.SSGetClass.entitySet.count() == 0:
                return True  # fine comando
            self.cacheEntitySet.appendEntitySet(self.SSGetClass.entitySet)

            entityIterator = QadCacheEntitySetIterator(self.cacheEntitySet)
            for entity in entityIterator:
                self.basePoint = entity
                self.addFeatureCache(entity, 'ref')
            #     qad_layer.addLineToLayer(self.plugIn, conductor[0], a)
            # print(self.parameters)

            # imposto il map tool
            self.getPointMapTool().cacheEntitySet = self.cacheEntitySet
            self.getPointMapTool().setMode(Qad_lvdb_maptool_ModeEnum.ASK_FOR_LV_FUSE_NUMBER)
            lvFuseRange = self.getClosedLvRange()

            keyWords = QadMsg.translate("Command_LVDB", "None") + "/" 
            for lvFuse in lvFuseRange:
                keyWords += QadMsg.translate("Command_LVDB", str(lvFuse)) + "/" 
            keyWords += QadMsg.translate("Command_LVDB", "All")
            print(keyWords)
           
            # keyWords = QadMsg.translate("Command_LVDB", str(
            #     min)) + "/" + QadMsg.translate("Command_LVDB", str(max))
            default = QadMsg.translate("Command_LVDB", "All")
            prompt = QadMsg.translate(
                "Command_LVDB", "Specify number of fuses to draw [{0}] <{1}>: ").format(keyWords, default)

            englishKeyWords = "All"
            # englishKeyWords = str(min) + "/" + str(max)
            keyWords += "_" + englishKeyWords
            # si appresta ad attendere un punto o enter o una parola chiave
            # msg, inputType, default, keyWords, nessun controllo
            self.waitFor(prompt,
                         QadInputTypeEnum.INT | QadInputTypeEnum.KEYWORDS,
                         default,
                         keyWords,
                         QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
            self.step = 2
            return False

        # =========================================================================
        # RISPOSTA ALLA RICHIESTA PUNTO BASE (da step = 1)
        elif self.step == 2:
            if msgMapTool == True:
                if self.getPointMapTool().point is None:  # il maptool é stato attivato senza un punto
                    if self.getPointMapTool().rightButton == True:  # se usato il tasto destro del mouse
                        pass  # opzione di default "spostamento"
                    else:
                        # riattivo il maptool
                        self.setMapTool(self.getPointMapTool())
                        return False

                value = self.getPointMapTool().point
            else:  # il punto arriva come parametro della funzione
                value = msg
                self.parameters["lvFuseToDraw"] = int(value)
                self.undoGeomsInCache()
                self.addFeatureCache(self.entity, 'out')
                self.addFromRubberbandToLayer()
                self.undoGeomsInCache()


                

            if value is None or type(value) == unicode:
                
                self.basePt.set(0, 0)
                self.getPointMapTool().basePt = self.basePt
                self.getPointMapTool().setMode(
                    Qad_lvdb_maptool_ModeEnum.FUSE_NUMBER_KNOWN_ASK_FOR_LVDBFP_ANGLE)

                lvdbAngleStr = str(self.getLvdbAngle())
                keyWords = QadMsg.translate(
                    "Command_LVDB", lvdbAngleStr) + "/" + QadMsg.translate("Command_LVDB", "Insert")
                default = QadMsg.translate("Command_OFFSET", lvdbAngleStr)
                prompt = QadMsg.translate(
                    "Command_LVDB", "Insert the angle of lvdb-fp or auto fill [{0}] <{1}>: ").format(keyWords, default)

                englishKeyWords = "Insert"
                keyWords += "_" + englishKeyWords

                self.waitFor(prompt,
                             QadInputTypeEnum.INT | QadInputTypeEnum.KEYWORDS,
                             default,
                             keyWords,
                             QadInputModeEnum.NOT_NULL)
                self.step = 3

            elif type(value) == QgsPointXY:  
                print('self.step == 2 - elif: ', value)# se é stato inserito il punto base
                self.basePt.set(value.x(), value.y())
                print('self.basePt: ', value)

                # imposto il map tool
                self.getPointMapTool().basePt = self.basePt
                self.getPointMapTool().setMode(
                    Qad_lvdb_maptool_ModeEnum.FUSE_NUMBER_KNOWN_ASK_FOR_LVDBFP_ANGLE)

                keyWords = QadMsg.translate(
                    "Command_LVDB", "Yes") + "/" + QadMsg.translate("Command_LVDB", "Fill")
                default = QadMsg.translate("Command_OFFSET", "Fill")
                prompt = QadMsg.translate(
                    "Command_LVDB", "Insert the angle of lvdb-fp or auto fill [{0}] <{1}>: ").format(keyWords, default)

                englishKeyWords = "Yes" + "/" + "Fill"
                keyWords += "_" + englishKeyWords

                # si appresta ad attendere un punto o enter o una parola chiave
                # msg, inputType, default, keyWords, nessun controllo
                self.waitFor(prompt,
                             QadInputTypeEnum.KEYWORDS,
                             default,
                             keyWords,
                             QadInputModeEnum.NOT_NULL)
                self.step = 3

            return False

        # =========================================================================
        # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER SPOSTAMENTO (da step = 2)
        elif self.step == 3:
            if msgMapTool == True:
                if self.getPointMapTool().point is None:
                    if self.getPointMapTool().rightButton == True:
                        return True  # fine comando
                else:
                    self.setMapTool(self.getPointMapTool())
                    return False
                value = self.getPointMapTool().point
            else:
                value = msg
                self.parameters["lvdbAngle"] = int(value)
                print(self.parameters)

            if value is None or type(value) == unicode:
                print('self.step == 3 - if: ', value)
                self.basePt.set(0, 0)
                self.getPointMapTool().basePt = self.basePt
                self.getPointMapTool().setMode(
                    Qad_lvdb_maptool_ModeEnum.LVDBFP_ANGLE_KNOWN_ASK_FOR_DRAW_CONDUCTOR)
                keyWords = QadMsg.translate(
                    "Command_LVDB", "Yes") + "/" + QadMsg.translate("Command_LVDB", "No")
                default = QadMsg.translate("Command_OFFSET", "No")
                prompt = QadMsg.translate(
                    "Command_LVDB", "Draw incoming conductor? [{0}] <{1}>: ").format(keyWords, default)

                englishKeyWords = "Yes" + "/" + "No"
                keyWords += "_" + englishKeyWords

                self.waitFor(prompt,
                             QadInputTypeEnum.STRING | QadInputTypeEnum.KEYWORDS,
                             default,
                             keyWords,
                             QadInputModeEnum.NOT_NULL)
                self.step = 4

            elif type(value) == QgsPointXY:  # se é stato inserito il punto base
                self.basePt.set(value.x(), value.y())

                # imposto il map tool
                self.getPointMapTool().basePt = self.basePt
                self.getPointMapTool().setMode(
                    Qad_lvdb_maptool_ModeEnum.LVDBFP_ANGLE_KNOWN_ASK_FOR_DRAW_CONDUCTOR)

                keyWords = QadMsg.translate(
                    "Command_LVDB", "Yes") + "/" + QadMsg.translate("Command_LVDB", "No")
                default = QadMsg.translate("Command_OFFSET", "No")
                prompt = QadMsg.translate(
                    "Command_LVDB", "Draw incoming conductor? [{0}] <{1}>: ").format(keyWords, default)

                englishKeyWords = "Yes" + "/" + "No"
                keyWords += "_" + englishKeyWords

                self.waitFor(prompt,
                             QadInputTypeEnum.STRING | QadInputTypeEnum.KEYWORDS,
                             default,
                             keyWords,
                             QadInputModeEnum.NOT_NULL)
                self.step = 4

            return False


        #=========================================================================
        # RISPOSTA ALLA RICHIESTA DEL PUNTO DI SPOSTAMENTO (da step = 2)
        elif self.step == 4: # dopo aver atteso un punto o un numero reale si riavvia il comando
            if msgMapTool == True:            
                if self.getPointMapTool().point is None: # il maptool é stato attivato senza un punto
                    if self.getPointMapTool().rightButton == True: # se usato il tasto destro del mouse
                        return True # fine comando
                else:
                    self.setMapTool(self.getPointMapTool()) # riattivo il maptool
                    return False

                value = self.getPointMapTool().point
            else: # il punto arriva come parametro della funzione
                value = msg
                self.parameters["drawIncoming"] = value
            if value == 'Yes':
                self.undoGeomsInCache()
                self.addFeatureCache(self.entity, 'in')
                self.addFromRubberbandToLayer()
                self.undoGeomsInCache()
            if value == 'No':
                self.undoGeomsInCache()
            
            return True