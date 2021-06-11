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

import re

# Import the PyQt and QGIS libraries
from qgis.PyQt.QtGui import *
from qgis.utils import iface
from qgis.core import Qgis, QgsProject, QgsWkbTypes, QgsPointXY, QgsGeometry, QgsFeature


from .qad_generic_cmd import QadCommandClass
from .qad_ssget_cmd import QadSSGetClass
from ..qad_entity import QadCacheEntitySet, QadEntitySet, QadCacheEntitySetIterator, QadEntity
from ..qad_getpoint import QadGetPoint, QadGetPointDrawModeEnum
from .qad_lvdb_maptool import Qad_lvdb_maptool, Qad_lvdb_maptool_ModeEnum
from ..qad_textwindow import QadInputModeEnum, QadInputTypeEnum
from ..qad_variables import QadVariables
from ..qad_msg import QadMsg
from .. import qad_lvdb_fun
from .. import qad_layer
from ..qad_rubberband import createRubberBand


# Classe che gestisce il comando VSETUP
class QadLVOHCommandClass(QadCommandClass):

    def instantiateNewCmd(self):
        """ istanzia un nuovo comando dello stesso tipo """
        return QadLVOHCommandClass(self.plugIn)

    def getName(self):
        return QadMsg.translate("Command_list", "LVOH")

    def getEnglishName(self):
        return "LVOH"

    def connectQAction(self, action):
        action.triggered.connect(self.plugIn.runLVOHCommand)

    def getIcon(self):
        return QIcon(":/plugins/qad/icons/lvoh.png")

    def getNote(self):
        # impostare le note esplicative del comando
        return QadMsg.translate("Command_LVOH", "Configures the value map from the attributes")

    def __init__(self, plugIn):
        QadCommandClass.__init__(self, plugIn)
        self.iface = self.plugIn.iface
        self.entity = QadEntity()
        self.entitySet = QadEntitySet()
        self.cacheEntitySet = QadCacheEntitySet()
        self.SSGetClass = QadSSGetClass(plugIn)
        self.SSGetClass.onlyEditableLayers = True
        self.lvdbMode = QadVariables.get(
            QadMsg.translate("Environment variables", "LVDBMODE"))
        self.targetLayer = 'LVDB-FP'
        self.nOperationsToUndo = 0
        self.lvdbType = 0
        self.lvFuseCount = 0
        self.parameters = {"lvdbAngle": ""}
        self.basePoint = None
        self.featureCache = []
        self.undoFeatureCacheIndexes = []
        self.rubberBand = createRubberBand(
            self.plugIn.canvas, QgsWkbTypes.LineGeometry)

    def __del__(self):
        QadCommandClass.__del__(self)
        del self.SSGetClass
        # self.rubberBand.hide()
        # self.plugIn.canvas.scene().removeItem(self.rubberBand)

    def getPointMapTool(self, drawMode=QadGetPointDrawModeEnum.NONE):
        if self.step == 0:  # quando si é in fase di selezione entità
            return self.SSGetClass.getPointMapTool()
        else:
            # if (self.plugIn is not None):
            #     if self.PointMapTool is None:
            #         self.PointMapTool = Qad_lvdb_maptool(self.plugIn)
            #     return self.PointMapTool
            # else:
            return QadCommandClass.getPointMapTool(self, drawMode)

    def getCurrentContextualMenu(self):
        if self.step == 0:  # quando si é in fase di selezione entità
            return None  # return self.SSGetClass.getCurrentContextualMenu()
        else:
            return self.contextualMenu

    def isLoadedLayer(self):
        layer = qad_layer.getLayersByName(self.targetLayer)
        msgType = QadMsg.translate("Command_LVDB", "Error")
        msgText = '\nThe {} layer is not loaded!\n'.format(self.targetLayer)
        if layer:
            self.iface.setActiveLayer(layer[0])
            return True
        else:
            iface.messageBar().pushMessage(msgType,
                                           msgText,
                                           level=Qgis.Critical,
                                           duration=5)
            self.showMsg(QadMsg.translate("QAD", msgText))
            return False

    def isFeatureSelected(self):
        layer, errMsg = qad_layer.getCurrLayerEditable(
            self.plugIn.canvas, [QgsWkbTypes.PointGeometry])
        if layer:
            selectedFeature = [
                feature for feature in layer.getSelectedFeatures()]
            featLen = len(selectedFeature)
            if featLen == 1:
                return selectedFeature
            elif featLen == 0 or featLen > 1:
                self.showMsg(QadMsg.translate(
                    "QAD", '\nPlease select one feature from {}.\n'.format(layer.name())))
                return False

    def getClosedLvRange(self, searchedStr):
        selectedFeature = self.isFeatureSelected()
        listOfInterestFields = ["lvf_1", "lvf_2", "lvf_3", "lvf_4",
                                "lvf_5", "lvf_6", "lvf_7", "lvf_8", "lvf_9", "lvf_10"]
        if selectedFeature:
            fields = selectedFeature[0].fields()
            for field in fields:
                if field.name() in listOfInterestFields:
                    lvFuse = self.getClosedLV(selectedFeature[0][field.name()], searchedStr)
                    if lvFuse == searchedStr:
                        self.lvFuseCount += 1
            self.lvFuseCount += 1
            if self.lvFuseCount > 1:
                return range(1, self.lvFuseCount)
            else:
                return range(self.lvFuseCount)


    def getClosedLV(self, attribute, strRegex):
        try:
            if attribute:
                regex = re.compile(r'\b{0}\b'.format(strRegex), re.IGNORECASE)
                closedLV = regex.findall(attribute)
            return closedLV[0]
        except:
            pass

    def getLvdbAngle(self):
        selectedFeature = self.isFeatureSelected()
        if selectedFeature:
            angleField = selectedFeature[0]["lvdb_angle"]
            self.parameters["lvdbAngle"] = selectedFeature[0]["lvdb_angle"]
        return int(angleField)

    # ============================================================================
    # addFeatureCache
    # ============================================================================

    def addFeatureCache(self, entity, lineType):
        featureCacheLen = len(self.featureCache)
        layer = qad_layer.getLayersByName('LV_OH_Conductor')
        angle = self.getLvdbAngle()

        if lineType == 'ref':
            refLineList = qad_lvdb_fun.drawReferenceLines(entity, angle)
        elif lineType == 'in':
            # refLineList = qad_lvdb_fun.drawOutConductor(
            #     self.basePoint, 2, angle)
            refLineList = qad_lvdb_fun.drawInConductor(
                self.basePoint, self.parameters["lvdbAngle"])
        elif lineType == 'out':
            refLineList = qad_lvdb_fun.drawOutConductor(
                self.basePoint, self.parameters["lvFuseToDraw"], angle)

        added = False
        for line in refLineList:
            refLineGeom = QgsGeometry.fromPolylineXY(line)

            if refLineGeom.type() == QgsWkbTypes.LineGeometry:
                refLineFeat = QgsFeature()
                # trasformo la geometria nel crs del layer
                refLineFeat.setGeometry(
                    self.mapToLayerCoordinates(layer[0], refLineGeom))
                # refLineFeat.setGeometry(refLineGeom)

                self.featureCache.append([layer[0], refLineFeat])
                self.addFeatureToRubberBand(layer[0], refLineFeat)
                added = True

        if added:
            self.undoFeatureCacheIndexes.append(featureCacheLen)

    # ============================================================================
    # undoGeomsInCache
    # ============================================================================

    def undoGeomsInCache(self):
        tot = len(self.featureCache)
        if tot > 0:
            iEnd = self.undoFeatureCacheIndexes[-1]
            i = tot - 1

            del self.undoFeatureCacheIndexes[-1]  # cancello ultimo undo
            while i >= iEnd:
                del self.featureCache[-1]  # cancello feature
                i = i - 1
            self.refreshRubberBand()

    # ============================================================================
    # addFeatureToRubberBand
    # ============================================================================

    def addFeatureToRubberBand(self, layer, feature):
        if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            if feature.geometry().type() == QgsWkbTypes.PolygonGeometry:
                self.rubberBandPolygon.addGeometry(feature.geometry(), layer)
            else:
                self.rubberBand.addGeometry(feature.geometry(), layer)
        else:
            self.rubberBand.addGeometry(feature.geometry(), layer)

    # ============================================================================
    # refreshRubberBand
    # ============================================================================

    def refreshRubberBand(self):
        self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        for f in self.featureCache:
            layer = f[0]
            feature = f[1]
            if layer.geometryType() == QgsWkbTypes.LineGeometry:
                if feature.geometry().type() == QgsWkbTypes.LineGeometry:
                    self.rubberBand.addGeometry(feature.geometry(), layer)

    def addFromRubberbandToLayer(self):
        layer = qad_layer.getLayersByName('LV_UG_Conductor')[0]
        provider = layer.dataProvider()
        line = QgsFeature()
        lista = list()
        for f in self.featureCache:
            lista.append(f[1])
        provider.addFeatures(lista)
        layer.triggerRepaint()
        self.undoGeomsInCache()

    # ============================================================================
    # waitForLvdbAngle
    # ============================================================================
    def waitForLvdbAngle(self):

        keyWords = QadMsg.translate("Command_LVDB", "Autofill")
        if int(self.parameters["lvdbAngle"]) < 0:
            default = QadMsg.translate("Command_LVDB", "Autofill")
        else:
            default = "Insert"
        prompt = QadMsg.translate(
            "Command_OFFSET", "Specify the lvdb-fp angle or [{0}] <{1}>: ").format(keyWords, unicode(default))

        englishKeyWords = "Autofill"
        keyWords += "_" + englishKeyWords
        
        self.waitFor(prompt,
                     QadInputTypeEnum.INT | QadInputTypeEnum.KEYWORDS,
                     default,
                     keyWords,
                     QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
        self.step = 4

    def addFeature(self, point):
        layer = qad_layer.getLayersByName(self.targetLayer)[0]
        transformedPoint = self.mapToLayerCoordinates(layer, point)
        g = QgsGeometry.fromPointXY(transformedPoint)
        f = QgsFeature()
        f.setGeometry(g)
        fields = layer.fields()
        f.setFields(fields)
        layer.select(f.id())

        provider = layer.dataProvider()
        for field in fields.toList():
            i = fields.indexFromName(field.name())
            f[field.name()] = provider.defaultValue(i)

        self.iface.openFeatureForm(layer, f, False)

        return qad_layer.addFeatureToLayer(self.plugIn, layer, f)

    # =========================================================================
    # RUN
    def run(self, msgMapTool=False, msg=None):
        if self.plugIn.canvas.mapSettings().destinationCrs().isGeographic():
            self.showMsg(QadMsg.translate(
                "QAD", "\nThe coordinate reference system of the project must be a projected coordinate system.\n"))
            return True  # fine comando

        isLoaded = self.isLoadedLayer()

        if isLoaded:
            currLayer, errMsg = qad_layer.getCurrLayerEditable(
                self.plugIn.canvas, [QgsWkbTypes.PointGeometry])
            if currLayer is None:
                self.showErr(errMsg)
                return True

        # =========================================================================
        # RICHIESTA SELEZIONE OGGETTI LIMITI
        if self.step == 0:  # inizio del comando
            CurrSettingsMsg = QadMsg.translate("QAD", "\nCurrent settings: ")
            if self.lvdbMode == 0:  # 0 = nessuna estensione
                CurrSettingsMsg = CurrSettingsMsg + \
                    QadMsg.translate("Command_LVDB", "Create")
                self.showMsg(CurrSettingsMsg)
                self.showMsg(QadMsg.translate("Command_LVDB",
                                              "\nEnter a new LVDB-FP point..."))
            else:
                CurrSettingsMsg = CurrSettingsMsg + \
                    QadMsg.translate("Command_LVDB", "Select")
                self.showMsg(CurrSettingsMsg)
                self.showMsg(QadMsg.translate(
                    "Command_LVDB", "\nSelect a LVDB-FP point..."))
            self.step = 1
            return self.run(msgMapTool, msg)

        # =========================================================================
        # RISPOSTA ALLA SELEZIONE OGGETTI LIMITI
        elif self.step == 1:
            if self.lvdbMode == 0:
                self.waitForPoint()
                self.step += 1
                return False
            else:
                if self.SSGetClass.run(msgMapTool, msg) == True:
                    self.step = 2
                    self.getPointMapTool().refreshSnapType()
                    return self.run(msgMapTool, msg)

        # =========================================================================
        # RISPOSTA ALLA RICHIESTA PUNTO BASE (da step = 1)
        elif self.step == 2:
            if msgMapTool == True:
                if self.getPointMapTool().point is None:
                    if self.getPointMapTool().rightButton == True:
                        pass
                    else:
                        self.setMapTool(self.getPointMapTool())
                        return False

                value = self.getPointMapTool().point
            else:  # il punto arriva come parametro della funzione
                value = msg
                
            if type(value) == QgsPointXY:
                self.basePoint = QgsPointXY(value)
                self.addFeature(self.basePoint)
                self.plugIn.setLastPoint(self.basePoint)
                self.addFeatureCache(self.basePoint, 'ref')

            if value is None or type(value) == unicode:

                self.cacheEntitySet.appendEntitySet(self.SSGetClass.entitySet)
                entityIterator = QadCacheEntitySetIterator(self.cacheEntitySet)

                for entity in entityIterator:
                    self.basePoint = qad_lvdb_fun.returnPointFromEntityOrQGSPoint(entity)
                    self.addFeatureCache(self.basePoint, 'ref')

                lvFuseRange = self.getClosedLvRange('CLOSED:')

                keyWords = QadMsg.translate("Command_LVDB", "None") + "/"
                for lvFuse in lvFuseRange:
                    keyWords += QadMsg.translate("Command_LVDB", str(lvFuse)) + "/"
                keyWords += QadMsg.translate("Command_LVDB", "All")

                default = QadMsg.translate("Command_LVDB", "All")
                prompt = QadMsg.translate(
                    "Command_LVDB", "Specify number of fuses to draw [{0}] <{1}>: ").format(keyWords, default)

                englishKeyWords = "All"
                keyWords += "_" + englishKeyWords

                self.waitFor(prompt,
                            QadInputTypeEnum.INT | QadInputTypeEnum.KEYWORDS,
                            default,
                            keyWords,
                            QadInputModeEnum.NOT_ZERO | QadInputModeEnum.NOT_NEGATIVE)
                self.step = 3
                return False

        # =========================================================================
        # RISPOSTA ALLA RICHIESTA PUNTO BASE (da step = 1)
        elif self.step == 3:
            if msgMapTool == True:
                if self.getPointMapTool().point is None:  # il maptool é stato attivato senza un punto
                    if self.getPointMapTool().rightButton == True:
                        # se usato il tasto destro del mouse
                        pass  # opzione di default "spostamento"
                    else:
                        # riattivo il maptool
                        self.setMapTool(self.getPointMapTool())
                        return False

                value = self.getPointMapTool().point
                print("value-if: ", value)
            else:  # il punto arriva come parametro della funzione
                value = msg
                print("value-else: ", value)

                if value == "None":
                    self.undoGeomsInCache()
                    return True
                elif value == "All":
                    all = [count for count in range(1, self.lvFuseCount)]
                    self.parameters["lvFuseToDraw"] = max(all)
                else:
                    self.parameters["lvFuseToDraw"] = int(value)

                self.undoGeomsInCache()
                self.addFeatureCache(self.basePoint, 'out')
                self.addFromRubberbandToLayer()

            if value is None or type(value) == unicode:

                self.waitForLvdbAngle()
                value = msg
                self.step = 4
                
            return False

        # =========================================================================
        # RISPOSTA ALLA RICHIESTA SECONDO PUNTO PER SPOSTAMENTO (da step = 2)
        elif self.step == 4:
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
                print("step3", value)
                if value == "Autofill":
                    self.parameters["lvdbAngle"] = int(self.getLvdbAngle())
                elif isinstance(int(value), int):
                    self.parameters["lvdbAngle"] = int(value)
                else:
                    self.showMsg(QadMsg.translate(
                        "Command_LVDB", "Wrong input value! Please enter a integer value from 0-360"))
                    return True
                print(self.parameters)

            if value is None or type(value) == unicode:
                
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
                self.step = 5

            return False

        # =========================================================================
        # RISPOSTA ALLA RICHIESTA DEL PUNTO DI SPOSTAMENTO (da step = 2)
        elif self.step == 5:  # dopo aver atteso un punto o un numero reale si riavvia il comando
            if msgMapTool == True:
                if self.getPointMapTool().point is None:  # il maptool é stato attivato senza un punto
                    if self.getPointMapTool().rightButton == True:  # se usato il tasto destro del mouse
                        return True  # fine comando
                else:
                    # riattivo il maptool
                    self.setMapTool(self.getPointMapTool())
                    return False

                value = self.getPointMapTool().point
            else:  # il punto arriva come parametro della funzione
                value = msg
                self.parameters["drawIncoming"] = value
            if value == 'Yes':
                self.undoGeomsInCache()
                self.addFeatureCache(self.basePoint, 'in')
                self.addFromRubberbandToLayer()
                self.undoGeomsInCache()
            if value == 'No':
                self.undoGeomsInCache()

            return True
