# -*- coding: utf-8 -*-

"""
/***************************************************************************
 ProjetosEstagio5CGEO
                                 A QGIS plugin
 Solução dos Estagiarios do 5 CGEO
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-04-04
        copyright            : (C) 2023 by Estagiarios 5 CGEO
        emails               : e.tadeu.eb@ime.eb.br
                               joao.pereira@ime.eb.br
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

__author__ = 'Estagiarios do 5 CGEO'
__date__ = '2023-04-04'
__copyright__ = '(C) 2023 by Estagiarios 5 CGEO'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'
from itertools import chain
from PyQt5.QtCore import QCoreApplication
from qgis.PyQt.QtCore import QVariant
from DsgTools.core.GeometricTools.layerHandler import LayerHandler
from qgis.core import (
    QgsDataSourceUri,
    QgsProject,
    QgsProcessingContext,
    QgsProcessingUtils,
    QgsGeometry,
    QgsGeometryCollection,
    QgsFeature,
    QgsFeatureSink,
    QgsFeedback,
    QgsFeatureRequest,
    QgsField,
    QgsFields,
    QgsPointXY,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingMultiStepFeedback,
    QgsProcessingOutputVectorLayer,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDistance,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorLayer,
    QgsVectorLayer,
    QgsWkbTypes,
)

from .algRunner import AlgRunner
from math import atan2, degrees


class Projeto5Solucao(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    TOLERANCE = "TOLERANCE"
    MIN_LENGTH = "MIN_LENGTH"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config):
        """
        Parameter setting.
        """
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT, self.tr("Input layer"), [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.TOLERANCE,
                self.tr("Snap radius"),
                parentParameterName=self.INPUT,
                minValue=-1.0,
                defaultValue=1.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_LENGTH,
                self.tr("Minimum size"),
                minValue=0,
                type=QgsProcessingParameterNumber.Double,
                defaultValue=100,
            )
        )
        self.addOutput(
            QgsProcessingOutputVectorLayer(
                self.OUTPUT, self.tr("Original layer with overlayed lines")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        layerHandler = LayerHandler()
        algRunner = AlgRunner()
        inputLyr = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        onlySelected = True
        minLength = self.parameterAsDouble(parameters, self.MIN_LENGTH, context)
        tol = self.parameterAsDouble(parameters, self.TOLERANCE, context)

        multiStepFeedback = QgsProcessingMultiStepFeedback(4, feedback)
        multiStepFeedback.setCurrentStep(0)

        #SECCIONAMENTO DE LINHAS QUE SE CRUZAM
        if tol > 0:
            multiStepFeedback.pushInfo(
                self.tr("Identifying dangles on {layer}...").format(
                    layer=inputLyr.name()
                )
            )
            dangleLyr = AlgRunner().runIdentifyDangles(
                inputLayer=inputLyr,
                searchRadius=tol,
                context=context,
                onlySelected=onlySelected,
                ignoreDanglesOnUnsegmentedLines=True,
                inputIsBoundaryLayer=True,
                feedback=multiStepFeedback,
            )

            multiStepFeedback.setCurrentStep(1)
            layerHandler.filterDangles(dangleLyr, tol, feedback=multiStepFeedback)

            multiStepFeedback.setCurrentStep(2)
            multiStepFeedback.pushInfo(
                self.tr("Snapping layer {layer} to dangles...").format(
                    layer=inputLyr.name()
                )
            )
            algRunner.runSnapLayerOnLayer(
                inputLyr,
                dangleLyr,
                tol,
                context,
                feedback=multiStepFeedback,
                onlySelected=onlySelected,
            )

        multiStepFeedback.setCurrentStep(3)
        multiStepFeedback.pushInfo(
            self.tr("Cleanning layer {layer}...").format(layer=inputLyr.name())
        )
        algRunner.runDsgToolsClean(
            inputLyr,
            context,
            snap=tol,
            feedback=multiStepFeedback,
            onlySelected=onlySelected,
        )

        #IDENTIFICAÇÃO DE ARESTAS COM COMPRIMENTO MENOR QUE A TOLERÂNCIA
        if inputLyr is None:
            return {self.OUTPUT: inputLyr}

        nDangles = dangleLyr.featureCount()
        if nDangles == 0:
            return {self.OUTPUT: inputLyr}

        danglelayer = QgsVectorLayer(f"LineString?crs={inputLyr.crs().authid()}",
                                     "arestas_soltas",
                                     "memory"
                                     )
        danglelayer.dataProvider().addAttributes([QgsField("id", QVariant.Int)])

        currentTotal = 100 / nDangles
        cont = 1
        for current, feat in enumerate(dangleLyr.getFeatures()):
            if multiStepFeedback.isCanceled():
                break
            dangleGeom = feat.geometry()
            dangleBB = dangleGeom.boundingBox()
            request = QgsFeatureRequest().setNoAttributes().setFilterRect(dangleBB)
            lineGeometry = [
                i.geometry()
                for i in inputLyr.getFeatures(request)
                if i.geometry().intersects(dangleGeom)
            ][0]
            if lineGeometry.length() > minLength:
                continue

            feature = QgsFeature()
            feature.setGeometry(lineGeometry)
            feature.setAttributes([cont])
            danglelayer.dataProvider().addFeature(feature)
            danglelayer.updateExtents()
            cont += 1
            multiStepFeedback.setProgress(current * currentTotal)

        #OBTENÇÃO DA DIFERENÇA ENTRE GEOMETRIAS (INPUT E ARESTAS SOLTAS)
        fields = inputLyr.fields()
        inputLyr.startEditing()
        for linhas in inputLyr.getFeatures():
            linegeometria = linhas.geometry()
            for linhassoltas in danglelayer.getFeatures():
                linesoltageometria = linhassoltas.geometry()
                if linegeometria.equals(linesoltageometria):
                    inputLyr.deleteFeature(linhas.id())

        #MERGE DE LINHAS QUE SE TOCAM DE FORMA A VOLTAR CONFORME ORIGINAL
        for linha1 in inputLyr.getFeatures():
            geometria = linha1.geometry()
            atributos = linha1.attributes()
            geometria_a_mesclar = [geometria]
            geometria_mesclada = geometria
            bbox = geometria.boundingBox()
            for part in geometria.parts():
                vertices = list(part)
                ponto_inicio1 = QgsPointXY(QgsPointXY(vertices[0].x(), vertices[0].y()))
                ponto_fim1 = QgsPointXY(QgsPointXY(vertices[-1].x(), vertices[-1].y()))
            
            for linha2 in inputLyr.getFeatures(bbox):
                geometry = linha2.geometry()
                if geometria.equals(geometry):
                    continue
                for part in geometry.parts():
                    vertices = list(part)
                    ponto_inicio2 = QgsPointXY(QgsPointXY(vertices[0].x(), vertices[0].y()))
                    ponto_fim2 = QgsPointXY(QgsPointXY(vertices[-1].x(), vertices[-1].y()))

                if geometria_mesclada.touches(geometry) or geometria_mesclada.overlaps(geometry):
                    angulo1 = abs(degrees(atan2(ponto_inicio1.y() - ponto_fim1.y(), ponto_inicio1.x() - ponto_fim1.x())))
                    angulo2 = abs(degrees(atan2(ponto_inicio2.y() - ponto_fim2.y(), ponto_inicio2.x() - ponto_fim2.x())))
                    dif_ang = abs(angulo1 - angulo2)
                    tolerancia_angulo = 1  # Ajuste conforme necessário
                    if dif_ang < tolerancia_angulo:
                        geometria_a_mesclar.append(geometry)
                        geometria_mesclada = QgsGeometry.unaryUnion(geometria_a_mesclar)
                        geometria_a_mesclar = [geometria_mesclada]
                        inputLyr.deleteFeature(linha2.id())
            
            inputLyr.deleteFeature(linha1.id())
            nova_feature = QgsFeature(fields)
            nova_feature.setGeometry(geometria_mesclada)
            nova_feature.setAttributes(atributos)
            inputLyr.dataProvider().addFeatures([nova_feature])
            inputLyr.updateExtents()
        inputLyr.updateExtents()

        #REMOÇÃO DE GEOMETRIAS DUPLICADAS
        if inputLyr is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT)
            )
        multiStepFeedback = QgsProcessingMultiStepFeedback(2, feedback)
        multiStepFeedback.setCurrentStep(0)
        multiStepFeedback.pushInfo(
            self.tr("Identifying duplicated geometries in layer {0}...").format(
                inputLyr.name()
            )
        )
        flagLyr = algRunner.runIdentifyDuplicatedGeometries(
            inputLyr, context, feedback=multiStepFeedback, onlySelected=False
        )

        multiStepFeedback.setCurrentStep(1)
        multiStepFeedback.pushInfo(
            self.tr("Removing duplicated geometries in layer {0}...").format(
                inputLyr.name()
            )
        )
        self.removeFeatures(inputLyr, flagLyr, multiStepFeedback)
        #remoção de geometria dentro de outra

        for linhas in inputLyr.getFeatures():
            geometria = linhas.geometry()
            atributos = linhas.attributes()
            bbox = geometria.boundingBox()
            
            for line in inputLyr.getFeatures(bbox):
                geometry = line.geometry()
                #feedback.pushInfo(f'{linhas} está sendo analisada.')
                if (linhas.id() != line.id()) and geometria.within(geometry): inputLyr.deleteFeature(linhas.id())

        return {self.OUTPUT: inputLyr}

    def removeFeatures(self, inputLyr, flagLyr, feedback):
        featureList, total = self.getIteratorAndFeatureCount(flagLyr)
        localTotal = 100 / total if total else 0
        inputLyr.beginEditCommand("Removing duplicates")
        inputLyr.startEditing()
        removeSet = set()
        for current, feat in enumerate(featureList):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            removeSet = removeSet.union(
                set(
                    [
                        i
                        for i in map(
                            int, feat["reason"].split("(")[-1].split(")")[0].split(",")
                        )
                    ][1::]
                )
            )
            feedback.setProgress(current * localTotal)
        inputLyr.deleteFeatures(list(removeSet))
        inputLyr.endEditCommand()
        
        return {self.OUTPUT: inputLyr}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Aparar linhas'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return 'Aparar linhas'

    """def groupId(self):
        
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        
        return 'Projeto 6'"""

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Projeto5Solucao()
    
    def prepareFlagSink(self, parameters, source, wkbType, context, addFeatId=False):
        (self.flagSink, self.flag_id) = self.prepareAndReturnFlagSink(
            parameters, source, wkbType, context, self.FLAGS, addFeatId=addFeatId
        )

    def prepareAndReturnFlagSink(
        self, parameters, source, wkbType, context, UI_FIELD, addFeatId=False
    ):
        flagFields = self.getFlagFields(addFeatId=addFeatId)
        (flagSink, flag_id) = self.parameterAsSink(
            parameters,
            UI_FIELD,
            context,
            flagFields,
            wkbType,
            source.sourceCrs() if source is not None else QgsProject.instance().crs(),
        )
        if flagSink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, UI_FIELD))
        return (flagSink, flag_id)
    
    def getFlagFields(self, addFeatId=False):
        fields = QgsFields()
        fields.append(QgsField("reason", QVariant.String))
        if addFeatId:
            fields.append(QgsField("featid", QVariant.String))
        return fields
    
    def flagFeature(self, flagGeom, flagText, featid=None, fromWkb=False, sink=None):
        """
        Creates and adds to flagSink a new flag with the reason.
        :param flagGeom: (QgsGeometry) geometry of the flag;
        :param flagText: (string) Text of the flag
        """
        flagSink = self.flagSink if sink is None else sink
        newFeat = QgsFeature(self.getFlagFields(addFeatId=featid is not None))
        newFeat["reason"] = flagText
        if featid is not None:
            newFeat["featid"] = featid
        if fromWkb:
            geom = QgsGeometry()
            geom.fromWkb(flagGeom)
            newFeat.setGeometry(geom)
        else:
            newFeat.setGeometry(flagGeom)
        flagSink.addFeature(newFeat, QgsFeatureSink.FastInsert)
    
    def getIteratorAndFeatureCount(self, lyr, onlySelected=False):
        """
        Gets the iterator and feature count from lyr.
        """
        try:
            if onlySelected:
                total = (
                    100.0 / lyr.selectedFeatureCount()
                    if lyr.selectedFeatureCount()
                    else 0
                )
                iterator = lyr.getSelectedFeatures()
            else:
                total = 100.0 / lyr.featureCount() if lyr.featureCount() else 0
                iterator = lyr.getFeatures()
            return iterator, total
        except:
            return [], 0