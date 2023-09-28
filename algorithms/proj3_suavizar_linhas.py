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
                       QgsSpatialIndex,
                       QgsFeatureSink,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsExpression,
                       QgsVectorLayer,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterVectorLayer,
                       QgsFields,
                       QgsFeature,
                       QgsField,
                       QgsGeometry,
                       QgsGeometryUtils,
                       QgsGeometryCollection)
import processing


class Projeto3Solucao(QgsProcessingAlgorithm):
    """
    
    Este algoritmo realiza a generalização de edifícios próximos às rodovias.

    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    # Camadas de input
    EDIFICACOES = 'EDIFICACOES'
    RODOVIAS = 'RODOVIAS'
    DISTANCIA = 'DISTANCIA'

    # Camadas de output
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config):

        self.addParameter(QgsProcessingParameterVectorLayer(self.EDIFICACOES, self.tr('Insira as edificações'), 
                                                            types=[QgsProcessing.TypeVectorPoint], 
                                                            defaultValue=None))
        
        self.addParameter(QgsProcessingParameterVectorLayer(self.RODOVIAS, self.tr('Insira as rodovias'), 
                                                            types=[QgsProcessing.TypeVectorLine], 
                                                            defaultValue=None))
                
        self.addParameter(QgsProcessingParameterNumber(self.DISTANCIA,
                                                       self.tr('Insira a distância máxima de deslocamento'),
                                                       defaultValue=60,
                                                       type=QgsProcessingParameterNumber.Double))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Edificações generalizadas'), 
                                                            type=QgsProcessing.TypeVectorPoint, 
                                                            createByDefault=True, 
                                                            supportsAppend=True, 
                                                            defaultValue='TEMPORARY_OUTPUT'))
        
        
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        edificios = self.parameterAsVectorLayer(parameters,self.EDIFICACOES,context)
        rodovias = self.parameterAsVectorLayer(parameters,self.RODOVIAS,context)
        distancia = self.parameterAsDouble(parameters,self.DISTANCIA,context)

        sinkFields = edificios.fields()
        (output_sink, output_dest_id) = self.parameterAsSink(parameters,self.OUTPUT,context,
                                                             sinkFields,1,edificios.sourceCrs())
        
        total = 100.0 / edificios.featureCount() if edificios.featureCount() else 0

        pontos = edificios.getFeatures()
        dist_min = 30.5 #Pouco maior que a soma da metade da via (25/2) + a metade da diagonal de um quadrado de lado 25
        dist_min_ed = 35.5 #Pouco maior que a soma das metade das diagonais de um quadrado de lado 25
        for current, ponto in enumerate(pontos):
            geometriaPonto = ponto.geometry()
            for partes in geometriaPonto.parts():
                for p in partes.vertices():
                    xi = p.x()
                    yi = p.y()
                    xn = xi
                    yn = yi

                    for linha in rodovias.getFeatures():
                        geometriaLinha = linha.geometry()
                        for l in geometriaLinha.parts():
                            pontoaux = QgsGeometry.fromPointXY(QgsPointXY(xn,yn))
                            geoaux = QgsPoint(xn,yn)
                            distance = pontoaux.distance(geometriaLinha)
                            if distance < dist_min:
                                p_prox = QgsGeometryUtils.closestPoint(l,geoaux)
                                xp = p_prox.x()
                                yp = p_prox.y()
                                m = ((xn-xp)**2 + (yn-yp)**2)**0.5
                                xn = xp + (dist_min/m)*(xn-xp)
                                yn = yp + (dist_min/m)*(yn-yp)
                            
                            pontoaux_n = QgsGeometry.fromPointXY(QgsPointXY(xn,yn))
                            pontoaux_i = QgsGeometry.fromPointXY(QgsPointXY(xi,yi))
                            deslocamento = pontoaux_n.distance(pontoaux_i)
                            if deslocamento > distancia:
                                xn = xi
                                yn = yi
                            
                            if feedback.isCanceled():
                                break
                    """
                    for point in edificios.getFeatures():
                        geometriaPoint = point.geometry()
                        if not geometriaPonto.equals(geometriaPoint):
                            distance = geometriaPonto.distance(geometriaPoint)
                            if distance < dist_min_ed:
                                for partes in geometriaPoint.parts():
                                    for pp in partes.vertices():
                                        xp = pp.x()
                                        yp = pp.y()
                                        m = ((xn-xp)**2 + (yn-yp)**2)**0.5
                                        xn = xp + (dist_min_ed/m)*(xn-xp)
                                        yn = yp + (dist_min_ed/m)*(yn-yp)
                            
                            if feedback.isCanceled():
                                break"""

                    novo_ponto = QgsGeometry.fromPointXY(QgsPointXY(xn,yn))
                    novo_feat = QgsFeature(sinkFields)
                    novo_feat.setGeometry(novo_ponto)
                    output_sink.addFeature(novo_feat)

            current += 1
            feedback.setProgress(int(current * total))

        # Configurando o estilo da camada

        # Get the path to the plugin directory
        plugin_dir = os.path.dirname(__file__)

        # Construct the path to the layer style file
        style_file = os.path.join(plugin_dir, 'edificacoes.qml')

        alg_params = {
            'INPUT': output_dest_id,
            'STYLE': style_file
        }
        processing.run('native:setlayerstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return {self.OUTPUT: output_dest_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Solução do Projeto 3'

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
        return 'Suavizar linhas'

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
