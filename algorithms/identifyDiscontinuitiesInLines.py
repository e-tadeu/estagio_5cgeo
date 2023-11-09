# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import (QCoreApplication, QVariant)
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsPointXY,
                       QgsFeature,
                       QgsProcessingParameterVectorLayer,
                       QgsField,
                       QgsFeatureRequest,
                       QgsGeometryUtils,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsGeometry,
                       QgsExpression,
                       QgsFields
                       )
import math
class IdentifyDiscontinuitiesInLines(QgsProcessingAlgorithm): 

    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_FIELDS = 'INPUT_FIELDS'
    INPUT_ANGLE = 'INPUT_ANGLE'
    INPUT_MAX_SIZE = 'INPUT_MAX_SIZE'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT_LAYER',
                self.tr('Selecione a camada'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'INPUT_FIELDS',
                self.tr('Selecione os campos que serão analisados'), 
                type=QgsProcessingParameterField.Any, 
                parentLayerParameterName='INPUT_LAYER',
                allowMultiple=True)
            )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                'INPUT_ANGLE',
                self.tr('Insira o desvio máximo (em graus) para detectar continuidade'), 
                type=QgsProcessingParameterNumber.Double, 
                minValue=0)
            )

        self.addParameter(
            QgsProcessingParameterNumber(
                'INPUT_MAX_SIZE',
                self.tr('Insira o comprimento máximo, em metros, das linhas analisadas'), 
                type=QgsProcessingParameterNumber.Double, 
                optional = True,
                minValue=0)
            )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Flag Mudança de atributos')
            )
        ) 
    def processAlgorithm(self, parameters, context, feedback):      
        feedback.setProgressText('Procurando descontinuidades...')
        layer = self.parameterAsVectorLayer(parameters,'INPUT_LAYER', context)
        inputFields = self.parameterAsFields( parameters,'INPUT_FIELDS', context )
        angle = self.parameterAsDouble(parameters,'INPUT_ANGLE', context)
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
            smallerAngle = 360
            for lineToBeSelected in lineTouched:
                angMinus180 = abs(self.anglesBetweenLines(feature, lineToBeSelected, ptFin)-180)
                if angMinus180<smallerAngle:
                    smallerAngle=angMinus180
                    line = lineToBeSelected
            fieldsChanged = []
            if self.anglesBetweenLines(feature, line, ptFin) < (180 + angle) and self.anglesBetweenLines(feature, line, ptFin) > (180 - angle):
                fieldsChanged = self.changedFields(inputFields, feature, line)
                nameOfFields = self.fieldsName(fieldsChanged, feature, line)
                if len(fieldsChanged) == 0:
                    continue
                if [ptFin,nameOfFields] not in pointsAndFields:
                    pointsAndFields.append([ptFin, nameOfFields])
        newPoints = self.getLinesWithSmallerAngle(pointsAndFields, layer, inputFields)
        if len(newPoints)==0:
            return{self.OUTPUT: 'nenhuma descontinuidade encontrada'}
        newLayer = self.outLayer(parameters, context, newPoints, layer, 4)
        return{self.OUTPUT: newLayer}

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
    
    def adjacentPoint(self, line, point):
        vertexPoint = line.geometry().closestVertexWithContext(point)[1]
        adjpoints = line.geometry().adjacentVertices(vertexPoint)
        adjptvertex = adjpoints[0]
        if adjptvertex<0:
            adjptvertex = adjpoints[1]
        adjpt = line.geometry().vertexAt(adjptvertex)
        return QgsPointXY(adjpt)

    def anglesBetweenLines(self, line1, line2, point):
        pointB = QgsPointXY(point.asPoint())
        pointA = self.adjacentPoint(line1, pointB)
        pointC = self.adjacentPoint(line2, pointB)
        angleRad = QgsGeometryUtils().angleBetweenThreePoints(pointA.x(), pointA.y(), pointB.x(), pointB.y(), pointC.x(), pointC.y())
        angle = math.degrees(angleRad)

        return abs(angle)

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
    def outLayer(self, parameters, context, pointsAndFields, layer, geomType):
        newField = QgsFields()
        newField.append(QgsField('Campos que Mudaram', QVariant.String))
        

        (sink, newLayer) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newField,
            geomType,
            layer.sourceCrs()
        )
        
        for feature in pointsAndFields:
            newFeat = QgsFeature()
            newFeat.setGeometry(feature[0])
            newFeat.setFields(newField)
            newFeat['Campos que Mudaram'] = feature[1]
            sink.addFeature(newFeat, QgsFeatureSink.FastInsert)
        
        return newLayer
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IdentifyDiscontinuitiesInLines()

    def name(self):
        return 'identifydiscontinuitiesinlines'

    def displayName(self):
        return self.tr('Identifica Mudança de Atributos em Linhas')

    def group(self):
        return self.tr('Missoes')

    def groupId(self):
        return 'missoes'

    def shortHelpString(self):
        return self.tr("O algoritmo identifica se existe alguma mudança de atributos entre linhas nos campos escolhidos e dentro da tolerância para continuidade")
    
