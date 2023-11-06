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
                       QgsProject,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsProcessingException,
                       QgsWkbTypes,
                       QgsExpressionContextUtils,
                       QgsPointXY,
                       QgsPoint,
                       QgsPointLocator,
                       QgsSpatialIndex,
                       QgsFeatureSink,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsExpression,
                       QgsVectorLayer,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsFields,
                       QgsFeature,
                       QgsField,
                       QgsGeometry,
                       QgsGeometryUtils,
                       QgsGeometryCollection,
                       QgsMarkerSymbol)
import processing
from PyQt5.QtGui import QColor


class Projeto4Solucao(QgsProcessingAlgorithm):
    """
    
    Este algoritmo realiza a revisão de ligação entre produtos.

    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    # Camadas de input
    INPUT = 'INPUT'
    DISTANCE = "DISTANCE"

    # Camadas de output
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config):

        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, self.tr('Insira a camada de linha'), 
                                                            types=[QgsProcessing.TypeVectorLine], 
                                                            defaultValue=None))
        
        self.addParameter(QgsProcessingParameterNumber(self.DISTANCE,
                                                       self.tr('Insira a distancia de fechamento'),
                                                       defaultValue=10,
                                                       type=QgsProcessingParameterNumber.Double))

        self.addOutput(QgsProcessingOutputVectorLayer(self.OUTPUT, self.tr("Camada original com as linha fechada")))
        
        
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        inputLyr = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)

        #Criação de uma camada de linhas de interseção entre os produtos
        for linhas in inputLyr.getFeatures():
            geometria = linhas.geometry()
            for parts in geometria.parts():vertices = list(parts)

            #Atribuição dos pontos extremos
            ponto_inicial = vertices[0]
            ponto_final = vertices[-1]

            #Distância entre os pontos extremos
            distancia = ponto_final.distance(ponto_inicial)

            #Condição para caso a distância entre os pontos extremos distam menor que a distancia minima
            if distancia <= distance: vertices.append(ponto_inicial)
            
            #Inserção da linha fechada à camada
            linha_fechada = QgsGeometry.fromPolyline(vertices)
            linhas.setGeometry(linha_fechada)
            inputLyr.updateFeature(linhas)
                   
        return {self.OUTPUT: inputLyr}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Fechar linhas'

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
        return 'Fechar linhas'

    """def groupId(self):
        
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        
        return 'Projeto 4'"""

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Projeto4Solucao()
