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
from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtCore import QVariant
from qgis.core import (QgsFeature,
                       QgsFeatureRequest,
                       QgsFeatureSink,
                       QgsField,
                       QgsFields,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsExpression,
                       QgsWkbTypes)
import processing


class Projeto1Solucao(QgsProcessingAlgorithm):
    """
    This is an algorithm that takes a vector layer and
    creates a new identical one.

    """

    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_FIELDS = 'INPUT_FIELDS'
    INPUT_MAX_AREA = 'INPUT_MAX_AREA'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                self.tr('Selecione a camada'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'INPUT_FIELDS',
                self.tr('Selecione os campos que serão ignorados'), 
                type=QgsProcessingParameterField.Any, 
                parentLayerParameterName='INPUT_LAYER',
                allowMultiple=True)
            )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                'INPUT_MAX_AREA',
                self.tr('Insira a área máxima dos poligonos analisados'), 
                type=QgsProcessingParameterNumber.Double, 
                optional = True,
                minValue=0)
            )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Flag Poligono com Atributos Iguais')
            )
        ) 
    def processAlgorithm(self, parameters, context, feedback):
        feedback.setProgressText('Procurando descontinuidades...')
        layer = self.parameterAsVectorLayer(parameters,'INPUT_LAYER', context)
        inputFields = self.parameterAsFields( parameters,'INPUT_FIELDS', context )
        maxArea = self.parameterAsDouble(parameters,'INPUT_MAX_AREA', context)

        #Criação da lista de campos que serão analisados
        fieldsAnalyzeds = [field.name() for field in layer.fields()]
        for field in inputFields:
            fieldsAnalyzeds.remove(field)
        #feedback.pushInfo(f'\nOs campos de {layer} são {inputFields} do tipo {type(inputFields)} e serão analisados os campos {fieldsAnalyzeds} do tipo {type(fieldsAnalyzeds)}.')
        
        if  maxArea>0:
            expr = QgsExpression( "$area < " + str(maxArea))
            allFeatures = layer.getFeatures(QgsFeatureRequest(expr))
        
        linesFlag = list()
        for feature in layer.getFeatures():
            if feedback.isCanceled():
                return {self.OUTPUT: 'processing cancelado'}
            
            neighbouringPolygons = list() #self.polygonsTouched(layer, feature)
            AreaOfInterest = feature.geometry().boundingBox()
            request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
            for feat in layer.getFeatures(request):
                if feature.geometry().touches(feat.geometry()) or feature.geometry().intersects(feat.geometry()):
                    geom = feature.geometry().intersection(feat.geometry())

                    if not (str(feature.geometry())==str(feat.geometry()) or geom.wkbType() == QgsWkbTypes.Point): #Não se preocupou-se se for polígono, visto que nesta fase, todas as interseções serão ponto ou linha
                        #feedback.pushInfo(f'\nA geometria {geom} é do tipo {type(geom)}.')
                        neighbouringPolygons.append(feat)
                        feedback.pushInfo(f'\nA lista de geometrias vizinhas é {neighbouringPolygons} é do tipo {type(neighbouringPolygons)}.')
            
            if len(neighbouringPolygons) == 0:
                continue 
            for neighbourPolygon in neighbouringPolygons:
                fieldsNotChanged = list()
                fieldsNotChanged = self.nonChangedFields(fieldsAnalyzeds, neighbourPolygon, feature)
                if len(fieldsNotChanged) == len(inputFields):
                    linesFlag.append(feature.geometry().intersection(feat.geometry())) #feature

        if len(linesFlag)==0:
            return{self.OUTPUT: 'nenhuma imutabilidade de atributos encontrada'}
        
        newLayer = self.outLayer(parameters, context, linesFlag, layer, 2) #layer retirado do argumento, 2 significa camada de linhas
        return{self.OUTPUT: newLayer}

    """
    def polygonsTouched(self, layer, polygon):
        polygons = []
        AreaOfInterest = polygon.geometry().boundingBox()
        request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
        for feat in layer.getFeatures(request):
            if polygon.geometry().touches(feat.geometry()) or polygon.geometry().intersects(feat.geometry()):
                geom = polygon.geometry().intersection(feat.geometry())
                if not (str(polygon.geometry())==str(feat.geometry() and geom = ):
                    polygons.append(feat)
        return polygons
    """
    def nonChangedFields(self, inputFields, feature1, feature2):
        equalFields = list()
        for field in inputFields:
            if feature1[field] == feature2[field]:
                equalFields.append(field)
        return equalFields
    
    def outLayer(self, parameters, context, features, layer, geomType): #layer retirado do argumento
        fields = QgsFields()
        fields.append(QgsField('reason', QVariant.String))

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            geomType,
            layer.sourceCrs()
        )
        
        for feature in features:
            newFeat = QgsFeature()
            newFeat.setGeometry(feature)
            newFeat.setAttributes(['Polígonos vizinhos sem mudança de atributo.'])
            #for field in  range(len(feature.fields())):
            #    newFeat.setAttribute((field), feature.attribute((field)))
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer
    
    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Identificar imutabilidade de atributos em polígonos vizinhos'

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
        return 'Identificar imutabilidade de atributos em polígonos vizinhos'

    """def groupId(self):
        
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        
        return 'Projeto 1'"""

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Projeto1Solucao()
