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
import os
import concurrent.futures
from collections import defaultdict
import processing
from processing.tools import dataobjects
from itertools import combinations, tee
from typing import Iterable, List

from DsgTools.core.GeometricTools.layerHandler import LayerHandler

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsField,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsFeature,
    QgsGeometry,
    QgsGeometryUtils,
    QgsFields,
    QgsFeatureSink,
    QgsExpression,
    QgsWkbTypes,
    QgsPointXY,
    QgsProject,
    QgsFeatureRequest,
    QgsProcessingParameterField,
    QgsProcessingParameterVectorLayer,
    QgsProcessingMultiStepFeedback,
    QgsProcessingFeatureSourceDefinition,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterDistance,
    QgsProcessingParameterMultipleLayers,
    QgsSpatialIndex,
)
from qgis.PyQt.QtCore import QVariant
import math

class GeometryHandler(QgsProcessingAlgorithm):

    def linesTouched(self, layer, feature, point):
        lines = []
        AreaOfInterest = feature.geometry().boundingBox()
        request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
        for feat in layer.getFeatures(request):
            if feat.geometry().intersects(point):
                if str(feature.geometry())==str(feat.geometry()):
                    continue
                lines.append(feat)
        return lines

    def changedFields(self, inputFields, feature1, feature2):
        equalFields = []
        for field in inputFields:
            if not feature1[field] == feature2[field]:
                equalFields.append(field)
        return equalFields

    def fieldsName(self, inputFields, feature1, feature2):
        text = ''
        for field in inputFields:
            value1 = feature1[field]
            value2 = feature2[field]
            if text =='':
                text = str(field) + ": " + str(value1) + " e " + str(value2)
            else:
                text += ', ' + str(field) + ": " + str(value1) + " e " + str(value2)
        return text
    def getLinesWithSmallerAngle(self, pointsAndFields, lineLayer, inputFields):
        pointsToBeRemoved = []
        for point in pointsAndFields:
            linesArray = []
            for line in lineLayer.getFeatures():
                for geometry in line.geometry().constGet():
                    ptFin = QgsGeometry.fromPointXY(QgsPointXY(geometry[-1]))
                    ptIni = QgsGeometry.fromPointXY(QgsPointXY(geometry[0]))
                if ptFin.intersects(point[0]):
                    linesArray.append([line, ptFin])
                if ptIni.intersects(point[0]):
                    linesArray.append([line, ptIni])
            smallerAngle = 360
            for i in range(len(linesArray)):
                if i == len(linesArray)-1:
                    continue
                lineA = linesArray[i][0]
                for j in range(i+1, len(linesArray)):
                    lineB = linesArray[j][0]
                    angMinus180 = abs(self.anglesBetweenLines(lineA, lineB, linesArray[i][1])-180)
                    if angMinus180<smallerAngle:
                        smallerAngle=angMinus180
                        line1 = lineA
                        line2 = lineB
            fieldsChanged = []
            fieldsChanged = self.changedFields(inputFields, line1, line2)
            if len(fieldsChanged) == 0:
                pointsToBeRemoved.append(point)
        newPoints = [pt for pt in pointsAndFields if pt not in pointsToBeRemoved]
        return newPoints
    def getFlagFields(self, addFeatId=False):
        fields = QgsFields()
        fields.append(QgsField("reason", QVariant.String))
        if addFeatId:
            fields.append(QgsField("featid", QVariant.String))
        return fields
    
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

    def prepareFlagSink(self, parameters, source, wkbType, context, addFeatId=False):
        (self.flagSink, self.flag_id) = self.prepareAndReturnFlagSink(
            parameters, source, wkbType, context, self.FLAGS, addFeatId=addFeatId
        )

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

    def runAddAutoIncrementalField(
        self,
        inputLyr,
        context,
        feedback=None,
        outputLyr=None,
        fieldName=None,
        start=1,
        sortAscending=True,
        sortNullsFirst=False,
        is_child_algorithm=False,
    ):
        fieldName = "featid" if fieldName is None else fieldName
        outputLyr = "memory:" if outputLyr is None else outputLyr
        parameters = {
            "INPUT": inputLyr,
            "FIELD_NAME": fieldName,
            "START": start,
            "GROUP_FIELDS": [],
            "SORT_EXPRESSION": "",
            "SORT_ASCENDING": sortAscending,
            "SORT_NULLS_FIRST": sortNullsFirst,
            "OUTPUT": outputLyr,
        }
        output = processing.run(
            "native:addautoincrementalfield",
            parameters,
            context=context,
            feedback=feedback,
            is_child_algorithm=is_child_algorithm,
        )
        return output["OUTPUT"]

    def runCreateSpatialIndex(
        self, inputLyr, context, feedback=None, is_child_algorithm=False
    ):
        processing.run(
            "native:createspatialindex",
            {"INPUT": inputLyr},
            feedback=feedback,
            context=context,
            is_child_algorithm=is_child_algorithm,
        )


    def name(self):
        return "identifica_linhas_conectadas_com_mesmo_conjunto_de_atributos"

class ParameterConfig(GeometryHandler):
    INPUT = "INPUT"
    OUTPUT = 'OUTPUT'
    SELECTED = "SELECTED"
    ATTRIBUTE_BLACK_LIST = "ATTRIBUTE_BLACK_LIST"
    IGNORE_VIRTUAL_FIELDS = "IGNORE_VIRTUAL_FIELDS"
    IGNORE_PK_FIELDS = "IGNORE_PK_FIELDS"
    POINT_FILTER_LAYERS = "POINT_FILTER_LAYERS"
    LINE_FILTER_LAYERS = "LINE_FILTER_LAYERS"
    FLAGS = "FLAGS"

    layerHandler = LayerHandler()

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def initAlgorithm(self,config):
        """
        Parameter setting.
        """
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT,
                self.tr("Input layer"),
                [
                    QgsProcessing.TypeVectorLine,
                ],
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SELECTED, self.tr("Process only selected features")
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.ATTRIBUTE_BLACK_LIST,
                self.tr("Fields to ignore"),
                None,
                "INPUT",
                QgsProcessingParameterField.Any,
                allowMultiple=True,
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.IGNORE_VIRTUAL_FIELDS,
                self.tr("Ignore virtual fields"),
                defaultValue=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.IGNORE_PK_FIELDS,
                self.tr("Ignore primary key fields"),
                defaultValue=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.FLAGS, self.tr("Flags").format(self.displayName())
            )
        )
    


class Projeto2Solucao(ParameterConfig): #NÃO ALTERE O NOME "PROJETO2SOLUCAO"
    def displayName(self):
        return (
            "Identificar linhas conectadas com mesmo conjunto de atributos"
        )

    def group(self):
        return "Projeto 2"

    def createInstance(self):
        return Projeto2Solucao()
    
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        
        layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)

        feedback.setProgressText('Procurando linhas conectadas...')

        inputFields = self.parameterAsFields( parameters,'INPUT_FIELDS', context )
        maxLength = self.parameterAsDouble(parameters,'INPUT_MAX_SIZE', context)
        allFeatures = layer.getFeatures()
        if  maxLength>0:
            expr = QgsExpression( "$length < " + str(maxLength))
            allFeatures = layer.getFeatures(QgsFeatureRequest(expr))
        pointsAndFields= []
        for feature in allFeatures:
            if feedback.isCanceled():
                return {self.OUTPUT: "cancelado pelo usuário"}
            featgeom = feature.geometry()
            for geometry in featgeom.constGet():
                ptFin = QgsGeometry.fromPointXY(QgsPointXY(geometry[-1]))
                lineTouched = self.linesTouched(layer, feature, ptFin)
            if len(lineTouched) == 0:
                continue
            for lineToBeSelected in lineTouched:
                
                line = lineToBeSelected
            fieldsChanged = []
            
            fieldsChanged = self.changedFields(inputFields, feature, line)
            nameOfFields = self.fieldsName(fieldsChanged, feature, line)
            if len(fieldsChanged) == 0:
                continue
            if [ptFin,nameOfFields] not in pointsAndFields:
                pointsAndFields.append([ptFin, nameOfFields])

        newPoints = self.getLinesWithSmallerAngle(pointsAndFields, layer, inputFields)
        if len(newPoints)==0:
            return{self.OUTPUT: 'Não foi encontrada nenhuma flag de mudança de atributo em linhas'}
        newLayer = self.outLayer(parameters, context, newPoints, layer, 4)
        print(f'newlayer : {newLayer} \n allFeatures: {allFeatures}')
        return{self.OUTPUT: newLayer}

