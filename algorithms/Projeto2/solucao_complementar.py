# -*- coding: utf-8 -*-

"""
/***************************************************************************
 ProgramacaoAplicadaGrupo4
                                 A QGIS plugin
 Solução do Grupo 4
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-05-04
        copyright            : (C) 2023 by Grupo 4
        emails               : e.tadeu.eb@ime.eb.br
                               raulmagno@ime.eb.br
                               arthur.cavalcante@ime.eb.br
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

__author__ = 'Grupo 4'
__date__ = '2023-05-04'
__copyright__ = '(C) 2023 by Grupo 4'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterRasterLayer,
                       QgsExpression)
import processing


class Projeto2SolucaoComplementar(QgsProcessingAlgorithm):
    """
    Este algoritmo realiza verificações topologicas em conjuntos de dados de recursos hidricos.

    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('drenagem', 'Drenagem', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('massas_de_agua', 'Massas de Agua', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Trecho_drenagens_ajust', 'Trecho_Drenagens_Ajust', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(12, model_feedback)
        results = {}
        outputs = {}

        # Indices Espaciais Drenagens
        alg_params = {
            'INPUT': parameters['drenagem']
        }
        outputs['IndicesEspaciaisDrenagens'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Indices Espaciais Massas de Agua
        alg_params = {
            'INPUT': parameters['massas_de_agua']
        }
        outputs['IndicesEspaciaisMassasDeAgua'] = processing.run('native:createspatialindex', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Intersecao 
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': outputs['IndicesEspaciaisDrenagens']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'OUTPUT': 'TEMPORARY_OUTPUT',
            'OVERLAY': outputs['IndicesEspaciaisMassasDeAgua']['OUTPUT'],
            'OVERLAY_FIELDS': ['null'],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Intersec'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Valores verdadeiros
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'dentro_de_poligono',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 6,  # Booleano
            'FORMULA': 'true',
            'INPUT': outputs['Intersec']['OUTPUT'],
            'OUTPUT': 'TEMPORARY_OUTPUT',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ValoresVerdadeiros'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Ajuste de id
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'fid',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Inteiro (32 bit)
            'FORMULA': '$id+50000',
            'INPUT': outputs['ValoresVerdadeiros']['OUTPUT'],
            'OUTPUT': 'TEMPORARY_OUTPUT',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AjusteDeId'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Diferenca simetrica
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': outputs['IndicesEspaciaisDrenagens']['OUTPUT'],
            'OUTPUT': 'TEMPORARY_OUTPUT',
            'OVERLAY': outputs['Intersec']['OUTPUT'],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DiferencaSimetrica'] = processing.run('native:symmetricaldifference', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Extrair por expressao
        alg_params = {
            'EXPRESSION': '"fid" is not null',
            'FAIL_OUTPUT': None,
            'INPUT': outputs['DiferencaSimetrica']['OUTPUT'],
            'OUTPUT': 'TEMPORARY_OUTPUT',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorExpressao'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s)
        alg_params = {
            'COLUMN': QgsExpression("'fid_2;id_2;nome_2;geometriaaproximada_2;navegavel_2;regime_2;encoberto_2;observacao_2;length_otf_2'").evaluate(),
            'INPUT': outputs['ExtrairPorExpressao']['OUTPUT'],
            'OUTPUT': 'TEMPORARY_OUTPUT',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Valores falsos
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'dentro_de_poligono',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 6,  # Booleano
            'FORMULA': 'false',
            'INPUT': outputs['DescartarCampos']['OUTPUT'],
            'OUTPUT': 'TEMPORARY_OUTPUT',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ValoresFalsos'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Uniao
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': outputs['ValoresFalsos']['OUTPUT'],
            'OUTPUT': 'TEMPORARY_OUTPUT',
            'OVERLAY': outputs['AjusteDeId']['OUTPUT'],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Uniao'] = processing.run('native:union', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Recriacao de IDs
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'fid',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Inteiro (32 bit)
            'FORMULA': '$id',
            'INPUT': outputs['Uniao']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RecriacaoDeIds'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Ajuste de Campos
        alg_params = {
            'FIELDS_MAPPING': [{'expression': 'if("fid" IS NULL AND "fid_2" IS NOT NULL,"fid_2","fid")','length': 0,'name': 'fid','precision': 0,'sub_type': 0,'type': 4,'type_name': 'int8'},{'expression': 'if("id" IS NULL AND "id_2" IS NOT NULL,"id_2","id")','length': 0,'name': 'id','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},{'expression': 'if("nome" IS NULL AND "nome_2" IS NOT NULL,"nome_2","nome")','length': 255,'name': 'nome','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},{'expression': 'if("geometriaaproximada" IS NULL AND "geometriaaproximada_2" IS NOT NULL,"geometriaaproximada_2","geometriaaproximada")','length': 0,'name': 'geometriaaproximada','precision': 0,'sub_type': 0,'type': 1,'type_name': 'boolean'},{'expression': 'if("navegavel" IS NULL AND "navegavel_2" IS NOT NULL,"navegavel_2","navegavel")','length': 0,'name': 'navegavel','precision': 0,'sub_type': 0,'type': 4,'type_name': 'int8'},{'expression': '','length': 0,'name': 'larguramedia','precision': 0,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'if("regime" IS NULL AND "regime_2" IS NOT NULL,"regime_2","regime")','length': 0,'name': 'regime','precision': 0,'sub_type': 0,'type': 4,'type_name': 'int8'},{'expression': 'if("encoberto" IS NULL AND "encoberto_2" IS NOT NULL,"encoberto_2","encoberto")','length': 0,'name': 'encoberto','precision': 0,'sub_type': 0,'type': 1,'type_name': 'boolean'},{'expression': 'if("observacao" IS NULL AND "observacao_2" IS NOT NULL,"observacao_2","observacao")','length': 0,'name': 'observacao','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},{'expression': 'if("length_otf" IS NULL AND "length_otf_2" IS NOT NULL,"length_otf_2","length_otf")','length': 0,'name': 'length_otf','precision': 0,'sub_type': 0,'type': 6,'type_name': 'double precision'},{'expression': 'if("dentro_de_poligono" IS NULL AND "dentro_de_poligono_2" IS NOT NULL,"dentro_de_poligono_2","dentro_de_poligono")','length': 0,'name': 'dentro_de_poligono','precision': 0,'sub_type': 0,'type': 1,'type_name': 'boolean'}],
            'INPUT': outputs['RecriacaoDeIds']['OUTPUT'],
            'OUTPUT': parameters['Trecho_drenagens_ajust']
        }
        outputs['AjusteDeCampos'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Trecho_drenagens_ajust'] = outputs['AjusteDeCampos']['OUTPUT']
        return results

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Solução Complementar do Projeto 2'

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
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Projeto 2'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Projeto2SolucaoComplementar()
    
  