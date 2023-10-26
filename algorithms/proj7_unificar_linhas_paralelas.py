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

class Projeto7Solucao(QgsProcessingAlgorithm):
    """
    
    Este algoritmo realiza a revisão de ligação entre produtos.

    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    # Camadas de input
    VIAS = 'VIAS'

    # Camadas de output
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config):
        
        self.addParameter(QgsProcessingParameterVectorLayer(self.VIAS, self.tr('Insira a camada de rodovias'), 
                                                            types=[QgsProcessing.TypeVectorLine], 
                                                            defaultValue=None))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Vias unificadas'), 
                                                            type=QgsProcessing.TypeVectorLine, 
                                                            createByDefault=True, 
                                                            supportsAppend=True, 
                                                            defaultValue='TEMPORARY_OUTPUT'))
        
        
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        vias = self.parameterAsVectorLayer(parameters,self.VIAS,context)

        #Criação da camada de saída do tipo ponto com o tipo de erro
        fields = vias.fields()
        (output_sink, output_dest_id) = self.parameterAsSink(parameters,
                                                            self.OUTPUT,
                                                            context,
                                                            fields,
                                                            2, #2 é para tipo linha, 1 é para tipo ponto
                                                            vias.sourceCrs())

        for linhas in vias.getFeatures():
            geomline = linhas.geometry()
            for parts in geomline.parts(): vertices = list(parts)
            startpoint = vertices[0]
            endpoint = vertices[1]
            coeficientes = QgsGeometryUtils.coefficients(startpoint, endpoint) #o terceiro elemento da tupla é a Constante da equação
            constante = coeficientes[2]/coeficientes[1] #Divide a Constante pela coeficiente de y (a/b x + y + c/b = 0)
            gradiente = QgsGeometryUtils.gradient(startpoint,endpoint)
            #comprimento = geomline.lenght()
            #feedback.pushInfo(f'\nA linha {geomline} contém a constante {coeficientes[2]} e gradiente {gradiente}.')

            #Criação de uma área de busca que dista 9,5 metros da linha com 8 vértices no arredondamento
            area_busca = geomline.buffer(9.5, 8)
            bbox = area_busca.boundingBox()
        #feedback.pushInfo(f'\nA área de busca {area_busca} é do tipo {type(area_busca)}.')
        #feedback.pushInfo(f'\nO bounding box {bbox} é do tipo {type(bbox)}.')
        
            for line in vias.getFeatures(bbox):
                geomline2 = line.geometry()
                atributos = line.attributes()
                if geomline.equals(geomline2) or geomline2.disjoint(area_busca): continue
                #feedback.pushInfo(f'\nA linha {geomline} são diferentes {geomline2}.')
                
                for parts in geomline2.parts(): vertices = list(parts)
                startpoint2 = vertices[0]
                endpoint2 = vertices[1]
                coeficientes2 = QgsGeometryUtils.coefficients(startpoint2, endpoint2) #o terceiro elemento da tupla é a Constante da equação
                constante2 = coeficientes2[2]/coeficientes2[1] 
                gradiente2 = QgsGeometryUtils.gradient(startpoint2,endpoint2)
                #comprimento2 = geomline2.lenght()

                #Verificação pelos gradientes se provavelmente são de mesma via.
                flag = False
                dif = abs(gradiente-gradiente2)
                if dif <= 0.01: flag = True #tolerância de 1 centésimo

                #dif = abs(constante-constante2)
                #if dif >= 2: flag = True #tolerância de 1 centésimo
                    
                if flag == True:
                    #Ponto 1
                    x_media = (startpoint.x() + endpoint2.x())/2
                    y_media = (startpoint.y() + endpoint2.y())/2
                    p_1 = QgsPoint(x_media, y_media)

                    #Ponto 2
                    x_media = (endpoint.x() + startpoint2.x())/2
                    y_media = (endpoint.y() + startpoint2.y())/2
                    p_2 = QgsPoint(x_media, y_media)

                    # Criação da linha média
                    newline = QgsGeometry.fromPolyline([p_1, p_2])

                    # Comprimento da extensão desejada (4,5 metros)
                    extensao = 4.5  # metros

                    # Calcula o vetor direção da linha
                    ponto_inicial = QgsPoint(newline.asPolyline()[0])
                    ponto_final = QgsPoint(newline.asPolyline()[-1])
                    vetor_direcao = ponto_final - ponto_inicial

                    # Calcula o comprimento do vetor direção
                    comprimento_vetor = (vetor_direcao.x()**2 + vetor_direcao.y()**2)**0.5

                    # Normaliza o vetor direção
                    if comprimento_vetor > 0:
                        vetor_direcao = QgsPoint(vetor_direcao.x() / comprimento_vetor, vetor_direcao.y() / comprimento_vetor)
                    else:
                        # Lida com o caso em que o vetor direção é uma linha de comprimento zero
                        # Você pode adotar uma abordagem diferente se necessário
                        print("A linha tem comprimento zero")

                   # Extende a linha no início e no final
                    ponto_inicial_extendido = QgsPoint(ponto_inicial.x() - extensao * vetor_direcao.x(), ponto_inicial.y() - extensao * vetor_direcao.y())
                    ponto_final_extendido = QgsPoint(ponto_final.x() + extensao * vetor_direcao.x(), ponto_final.y() + extensao * vetor_direcao.y())

                    linha_extendida = QgsGeometry.fromPolyline([ponto_inicial_extendido, ponto_final_extendido])


                    feature = QgsFeature(fields)
                    feature.setGeometry(linha_extendida)
                    feature.setAttributes(atributos)
                    output_sink.addFeatures([feature])

                #feedback.pushInfo(f'\nA linha {geomline} de gradiente {gradiente} e a linha {geomline2} de gradiente {gradiente2} provavelmente são da mesma via. Uma possui a constante {constante} e a outra possui a constante {constante2}.')
                #Verificação das constantes das vias. Caso tenham constante próximas, provavelmente estão na mesma equação de reta, ou seja, não quero.



                #feedback.pushInfo(f'\nA linha {geomline} contém a constante {coeficientes[2]} e gradiente {gradiente}\n a {geomline2} contém a constante {coeficientes2[2]} e gradiente {gradiente2}.')

        
        return {self.OUTPUT: output_dest_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Unificar linhas'

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
        return 'Unificar linhas'

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
        return Projeto7Solucao()
