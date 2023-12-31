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
from code import interact
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.Qt import QVariant, QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsProcessingException,
                       QgsWkbTypes,
                       QgsFeatureSink,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsFeatureRequest,
                       QgsExpression,
                       QgsVectorLayer,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterField,
                       QgsProcessingParameterVectorLayer,
                       QgsFields,
                       QgsFeature,
                       QgsField)
import processing


class Projeto3Solucao(QgsProcessingAlgorithm):
    """
    
    Este algoritmo realiza a generalização de edifícios próximos às rodovias.

    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    # Camadas de input
    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_FIELDS = 'INPUT_FIELDS'
    OUTPUT = 'OUTPUT'
    INPUT_MAX_AREA = 'INPUT_MAX_AREA'

    # Camadas de output
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config):

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
                self.tr('Insira a área máxima dos poligonos pequenos a serem analisados'), 
                type=QgsProcessingParameterNumber.Double, 
                optional = False,
                minValue=0)
            )
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Flag Poligono com Atributos Iguais')
            )
        )         
        
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        feedback.setProgressText('Procurando descontinuidades...')
        layer = self.parameterAsVectorLayer(parameters,'INPUT_LAYER', context)
        inputFields = self.parameterAsFields( parameters,'INPUT_FIELDS', context )
        maxArea = self.parameterAsDouble(parameters,'INPUT_MAX_AREA', context)

        #Criação da lista de campos que serão analisados
        fieldsAnalyzeds = [field.name() for field in layer.fields()]
        for field in inputFields:
            fieldsAnalyzeds.remove(field)

        #Criação da lista de feições de polígonos pequenos
        smallPolygons = list()
        for lyr in layer.getFeatures():
            area = lyr.geometry().area()
            if area < maxArea: smallPolygons.append(lyr)
        #feedback.pushInfo(f'\nA lista {smallPolygons} é do tipo {type(smallPolygons)} e tem {len(smallPolygons)} áreas.')

        linesFlag = list()
        for feature in smallPolygons:
            
            if feedback.isCanceled():
                return {self.OUTPUT: 'processing cancelado'}
            
            AreaOfInterest = feature.geometry().boundingBox()
            request = QgsFeatureRequest().setFilterRect(AreaOfInterest)
            for feat in layer.getFeatures(request):
                if feature.geometry().touches(feat.geometry()) or feature.geometry().intersects(feat.geometry()):
                    geom = feature.geometry().intersection(feat.geometry())
                    if not (str(feature.geometry())==str(feat.geometry()) or geom.wkbType() == QgsWkbTypes.Point): #Não se preocupou se for polígono, visto que nesta fase, todas as interseções serão ponto ou linha
                        #feedback.pushInfo(f'\nA geometria {geom} é do tipo {type(geom)}.')
                        
                        flag = True
                        for field in fieldsAnalyzeds:
                            if feature[field] != feat[field]: flag = False 
                        
                        if flag == True: linesFlag.append(geom)

        if len(linesFlag)==0:
            return{self.OUTPUT: 'Nenhuma imutabilidade de atributos encontrada.'}
        
        #Eliminação de linhas duplicadas
        linesFlagUnicas = list()
        for i in linesFlag:
            is_duplicate = False
            for j in linesFlagUnicas:
                if i.equals(j) or i.contains(j):
                    is_duplicate = True
                    break
            if not is_duplicate:
                linesFlagUnicas.append(i)
        
        newLayer = self.outLayer(parameters, context, linesFlagUnicas, layer, 2) #2 significa camada de linhas
        
        return {self.OUTPUT: newLayer}

  
    def outLayer(self, parameters, context, features, layer, geomType):
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
            newFeat.setAttributes(['Polígono Pequeno Vizinho sem mudança de atributo.'])
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
        return 'Identificar Polígonos Vizinhos Pequenos Sem Mudança de Atributo'

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
        return 'Identificar Polígonos Vizinhos Pequenos Sem Mudança de Atributo'

    """def groupId(self):
        
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        
        return 'Projeto 3'"""

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Projeto3Solucao()
