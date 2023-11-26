from pyfbsdk import *
import numpy as np
import math
from scipy.stats import pearsonr
from scipy.interpolate import interp1d

RootBoneName = 'Root'
BakedObjName = 'Root' #temp debug objects. Not needed in the release version
BakedObjName2 ='Root'
lExtremeCompareRange = 20  #the frame range on which the motion trajectory changes are analised
lChangeSignificanceFilter = -0.8 #the minimal value of Pearson's correlation to detect trajectory changes
lPeakInterpolationRnage = 6 #number of interpolation frames to smooth the bordgering ranges in motion changes.
lPolynomialFactor = 8
origRoot = FBFindModelByLabelName(RootBoneName)

#-------------------------------------------------------------------------------------------------------
def fFillArrayWithXZKeys (firstFrame, lastFrame):
    arrayOrigKeys=[]
    for i in range (0, (lastFrame-firstFrame+1)):
        arrayOrigKeys.append ((origRoot.Translation.GetAnimationNode().Nodes[0].FCurve.KeyGetValue (i),\
                               origRoot.Translation.GetAnimationNode().Nodes[2].FCurve.KeyGetValue (i)))
    return arrayOrigKeys
#-------------------------------------------------------------------------------------------------------
#--------debugging visualisation purposed function. Should be ignored in the released ------------------
def fBakeArrayToKeys (obj_name, x_values, y_values):
    # Find the lBakeObj by name
    lBakeObj = FBFindModelByLabelName (obj_name)
    lBakeObj.Translation.SetAnimated(True)        
    if not lBakeObj:
        print("Marker {} not found".format(obj_name))
        return
    # Clear existing animation on the lBakeObj's Position X and Position Y properties
    #lBakeObj.FBDeleteAnimation(True, True)
    lBakeObj.Translation.GetAnimationNode().Nodes[0].FCurve.EditClear()
    lBakeObj.Translation.GetAnimationNode().Nodes[2].FCurve.EditClear()
    lBakeObj.Translation = FBVector3d(0, 0, 0)
    # Create animation nodes for Position X and Position Y properties
    x_node = lBakeObj.Translation.GetAnimationNode().Nodes[0]
    y_node = lBakeObj.Translation.GetAnimationNode().Nodes[2]
    # Set keyframes for Position X and Position Y properties
    for i in range(len(x_values)):
        time = FBTime(0,0,0,i+lTakeStart,0)
        x_node.KeyAdd(time, x_values[i])
        y_node.KeyAdd(time, y_values[i])
#-------------------------------------------------------------------------------------------------------
def fGetPlayRange ():
##    lStart = FBPlayerControl().GetEditZoomStart ().GetFrame()
##    lStop  = FBPlayerControl().GetEditZoomStop  ().GetFrame()
    lStart = origRoot.Translation.GetAnimationNode().Nodes[0].FCurve.Keys[0].Time.GetFrame()
    lStop = origRoot.Translation.GetAnimationNode().Nodes[0].FCurve.Keys[-1].Time.GetFrame()
    return (lStart,lStop)
#-------------------------------------------------------------------------------------------------------
def fIsExtremeDetected (lSmallCoordArray):
    lCoordsP1 = lSmallCoordArray[0:lExtremeCompareRange]
    lCoordsP2 = lSmallCoordArray[lExtremeCompareRange::]
    lXValuesP1 = [i[0] for i in lCoordsP1]
    lYValuesP1 = [i[1] for i in lCoordsP1]
    lXValuesP2 = [i[0] for i in lCoordsP2]
    lYValuesP2 = [i[1] for i in lCoordsP2]
    lCorrCoefX, lPValueX = pearsonr (lXValuesP1,lXValuesP2)
    lCorrCoefY, lPValueY = pearsonr (lYValuesP1,lYValuesP2) 
    return lCorrCoefX,lCorrCoefY, lPValueX, lPValueY     
#-------------------------------------------------------------------------------------------------------
def fFindLocalExtremes (lCoordArray):
    larrayCorrCoefX=[]
    larrayCorrCoefY=[]
    larrayPValueX=[] 
    larrayPValueY=[]
    #adding extra lenght to original data array to calculate full range of correlation
    lFirstCoord = lCoordArray[0]
    lLastCoord  = lCoordArray[-1]
    larrayTails = np.full(shape=(lExtremeCompareRange,2) , fill_value=lFirstCoord) # it needs to make an array of tuples here
    lCoordArray = np.append(lCoordArray, larrayTails, axis=0)
    lCoordArray = np.roll(lCoordArray, lExtremeCompareRange*2)
    larrayTails = np.full(shape=(lExtremeCompareRange,2) , fill_value=lLastCoord)
    lCoordArray = np.append(lCoordArray, larrayTails, axis=0)
    lCoordArray = lCoordArray.tolist()
    #splitting coords into separate arrays
    for i in range (lExtremeCompareRange,len(lCoordArray)-lExtremeCompareRange) :
        lCorrCoefX,lCorrCoefY, lPValueX, lPValueY = fIsExtremeDetected (lCoordArray[i-lExtremeCompareRange:i+lExtremeCompareRange])
        larrayCorrCoefX.append(lCorrCoefX)
        larrayCorrCoefY.append(lCorrCoefY)
        larrayPValueX.append(lPValueX)
        larrayPValueY.append(lPValueY)
    #fBakeArrayToKeys (BakedObjName,larrayCorrCoefX,larrayCorrCoefY)   #to disable after the debug
    #fBakeArrayToKeys (BakedObjName2,larrayPValueX,larrayPValueY)      #to disable after the debug
    return fFindLocalMinima(larrayCorrCoefX,lExtremeCompareRange),fFindLocalMinima(larrayCorrCoefY,lExtremeCompareRange)
#-------------------------------------------------------------------------------------------------------
def fFindLocalMinima (CorrList, threshold) :
    # making a list of all local minima
    lMinima =[]
    lMinima.append(lTakeStart)
    for i in range (1, len(CorrList)-1) :
        if CorrList[i] < CorrList[i-1] and CorrList[i] < CorrList[i+1] and CorrList[i] < lChangeSignificanceFilter : 
            lMinima.append(i+lTakeStart)
    # leave only the keyframe with minimal value if they are within keyframe threshold range
    if (lMinima):
        lMergedMinima = [lMinima[0]]
        for i in range(1, len(lMinima)) :
            if abs(lMinima[i] - lMinima[i-1]) >= threshold:             
                lMergedMinima.append (lMinima[i])
            else :
                if CorrList[lMinima[i]] < CorrList[lMinima[i-1]] :
                    lMergedMinima.pop(-1)
                    lMergedMinima.append (lMinima[i])            
        lMergedMinima.append(len(CorrList)+lTakeStart)  
        return lMergedMinima
    else: 
        # in case of no curve corelation change - set first and last frames as minimals
        lMergedMinima = []
        lMergedMinima.append (0+lTakeStart)
        lMergedMinima.append (len(CorrList)+lTakeStart)
        return lMergedMinima
#-------------------------------------------------------------------------------------------------------
def fReturnStructuredKeys (arrayOfTupples, tuppleOfRanges) :
    lStructuredKeysX = []
    lStructuredKeysY = []
    # splitting an arrayOfTupple into list of arrays by the Ranges of the First elements of Tupples
    for i in range (1, len(arrayPeekKeyframes[0])) :
        lKeysRange = []    
        for j in range (tuppleOfRanges[0][i-1],tuppleOfRanges[0][i]) :
            lKeysRange.append(arrayOrigKeys [j-lTakeStart][0])
        lStructuredKeysX.append (lKeysRange)
    # splitting an arrayOfTupple into list of arrays by the Ranges of the Second (Y) elements of Tupples
    for i in range (1, len(arrayPeekKeyframes[1])) :
        lKeysRange = []
        for j in range (tuppleOfRanges[1][i-1],tuppleOfRanges[1][i]) :
            lKeysRange.append(arrayOrigKeys [j-lTakeStart][1])
        lStructuredKeysY.append (lKeysRange)
    return lStructuredKeysX , lStructuredKeysY
#-------------------------------------------------------------------------------------------------------
def fPolynomRegression (arrayOfKeys) :   
    # getting a polynomilal regression coefficients to degree of 5
    arrayOfTime = list(range(len(arrayOfKeys))) #j ust an itterator converted into an array
    lCoefs = np.polyfit(arrayOfTime, arrayOfKeys, lPolynomialFactor)
    # calculating aproximated values by polynomial model
    def calculate_polynomial(coefs, x):
        x1 = 0
        n = len(coefs)
        for i in range(n):
            x1 += coefs[i] * x ** (n-i-1)
        return x1
    # making a new array of of Regressed Keys
    arrayRegressedKeys = []
    for t in arrayOfTime :
        arrayRegressedKeys.append (calculate_polynomial(lCoefs,t))
    return arrayRegressedKeys 
#-------------------------------------------------------------------------------------------------------
def fRegressingKeyframes (lStructuredKeys) :
    # merging all regressed values into one array for X
    lNonestructuredRegressedKeysX = np.array ([])
    for i in range (0, len (lStructuredKeys[0])) :
        lNonestructuredRegressedKeysX = np.append (lNonestructuredRegressedKeysX, fPolynomRegression (lStructuredKeys[0][i]))
    # merging all regressed values into one array for Y
    lNonestructuredRegressedKeysY = np.array ([])
    for i in range (0, len (lStructuredKeys[1])) :
        lNonestructuredRegressedKeysY = np.append (lNonestructuredRegressedKeysY, fPolynomRegression (lStructuredKeys[1][i]))
   
    return lNonestructuredRegressedKeysX.tolist(), lNonestructuredRegressedKeysY.tolist()
#-------------------------------------------------------------------------------------------------------
def fInterpRangedIntersection (lOrigArray, InterpIndex, InterpRange) :
    # using Cubic interpolation to override the regressed functions overlaps 
    if ((InterpIndex > InterpRange) and (len(lOrigArray)>=InterpIndex+InterpRange) ) :  #interpolating in the middle of array:
        lFixArrayValues = np.array (lOrigArray [InterpIndex-InterpRange : InterpIndex+InterpRange])
        lFixFullIndexes = list(range(0,InterpRange*2))
        lFixInterpIndexes = list(range(2,InterpRange*2-2))
        lFixFragmentedValues = np.append (lFixArrayValues[:2],lFixArrayValues[-2:])
        lFixFragmentedIndexes = np.append (lFixFullIndexes[:2],lFixFullIndexes[-2:])
        fInterp = interp1d (lFixFragmentedIndexes, lFixFragmentedValues, kind = "cubic")
        lNewInterpValues = fInterp(lFixInterpIndexes)
        lOrigArray [InterpIndex-InterpRange+2 : InterpIndex+InterpRange-2] = lNewInterpValues
        return lOrigArray 
    elif (InterpIndex < InterpRange): #interpolating at the beggining of array:
        lFixArrayValues = np.array (lOrigArray [InterpIndex : InterpIndex+InterpRange])
        lFixFullIndexes = list(range(0,InterpRange))
        lFixInterpIndexes = list(range(1,InterpRange-2))
        lFixFragmentedValues = np.append (lFixArrayValues[:1],lFixArrayValues[-2:])
        lFixFragmentedIndexes = np.append (lFixFullIndexes[:1],lFixFullIndexes[-2:])
        fInterp = interp1d (lFixFragmentedIndexes, lFixFragmentedValues, kind = "quadratic")
        lNewInterpValues = fInterp(lFixInterpIndexes)
        lOrigArray [InterpIndex+1 : InterpIndex+InterpRange-2] = lNewInterpValues
        return lOrigArray
    elif (len(lOrigArray) < InterpIndex+InterpRange) : 
        lFixArrayValues = np.array (lOrigArray [InterpIndex-InterpRange : InterpIndex])
        lFixFullIndexes = list(range(0,InterpRange))
        lFixInterpIndexes = list(range(2,InterpRange-1))
        lFixFragmentedValues = np.append (lFixArrayValues[:2],lFixArrayValues[-1:])
        lFixFragmentedIndexes = np.append (lFixFullIndexes[:2],lFixFullIndexes[-1:])
        fInterp = interp1d (lFixFragmentedIndexes, lFixFragmentedValues, kind = "quadratic")
        lNewInterpValues = fInterp(lFixInterpIndexes)
        lOrigArray [InterpIndex-InterpRange+2 : InterpIndex-1] = lNewInterpValues
        return lOrigArray    
#-------------------------------------------------------------------------------------------------------
def fIinterpRegressedKeys (lRegressedKeys, arrayPeekKeyframes, InterpRange) :
    lRegressedKeys = list (lRegressedKeys)
    if (len (arrayPeekKeyframes[0])>2) :
        for i in range (0, len(arrayPeekKeyframes[0])) :
            lRegressedKeys[0] = fInterpRangedIntersection (lRegressedKeys[0], arrayPeekKeyframes[0][i]-lTakeStart, InterpRange)
    if (len (arrayPeekKeyframes[1])>2) :
        for i in range (0, len(arrayPeekKeyframes[1])) :
            lRegressedKeys[1] = fInterpRangedIntersection (lRegressedKeys[1], arrayPeekKeyframes[1][i]-lTakeStart, InterpRange)  
    return lRegressedKeys
#-------------------------------------------------------------------------------------------------------
def aim_yaw_rotation(from_pos, to_pos) :
    direction = np.array(to_pos) - np.array(from_pos)
    yaw = math.degrees(math.atan2(direction[0], direction[1]))  #pitch formula: pitch = math.degrees(-math.atan2(direction[1],math.sqrt(direction[0]**2 + direction[2]**2)))
    return yaw
#-------------------------------------------------------------------------------------------------------
def fMakeArrayRotationYaw (X_Array, Y_Array) :
    minArrayLenght = min (len(X_Array), len(Y_Array))
    lYawArray = []
    for i in range (0, minArrayLenght-1) :
        lCurrPos = (X_Array[i], Y_Array[i], 0)
        lLaterPos = (X_Array[i+1], Y_Array[i+1], 0)
        lYawArray.append(aim_yaw_rotation(lCurrPos,lLaterPos))
    return lYawArray
#------------------------------------------------------------------------------------------------------- 
def fBakeRotationToKeys (obj_name, yaw_values) :  
        # Find the lBakeObj by name
    lBakeObj = FBFindModelByLabelName (obj_name)
    lBakeObj.Translation.SetAnimated(True)        
    if not lBakeObj:
        print("Marker {} not found".format(obj_name))
        return
    # Clear existing animation on the lBakeObj's Position X and Position Y properties
    lBakeObj.Rotation.GetAnimationNode().Nodes[0].FCurve.EditClear()
    lBakeObj.Rotation.GetAnimationNode().Nodes[1].FCurve.EditClear()
    lBakeObj.Rotation.GetAnimationNode().Nodes[2].FCurve.EditClear()
    #lBakeObj.Rotation = FBVector3d(0, 0, 0)
    # Create animation nodes for Position X and Position Y properties
    yaw_node = lBakeObj.Rotation.GetAnimationNode().Nodes[2]
    # Set keyframes for Position X and Position Y properties
    for i in range(len(yaw_values)):
        time = FBTime(0,0,0,i+lTakeStart,0)
        yaw_node.KeyAdd(time, yaw_values[i])                
#------------------------------------------------------------------------------------------------------- 
    
lTakeStart, lTakeEnd = fGetPlayRange()
arrayOrigKeys = fFillArrayWithXZKeys(lTakeStart,lTakeEnd)
arrayPeekKeyframes =  fFindLocalExtremes (arrayOrigKeys)
lStructuredKeys = fReturnStructuredKeys (arrayOrigKeys,arrayPeekKeyframes)
lRegressedKeys = fRegressingKeyframes (lStructuredKeys)
fBakeArrayToKeys (BakedObjName,lRegressedKeys[0],lRegressedKeys[1])
lRegressedKeys = fIinterpRegressedKeys (lRegressedKeys, arrayPeekKeyframes, lPeakInterpolationRnage)
fBakeArrayToKeys (BakedObjName2,lRegressedKeys[0],lRegressedKeys[1])
lYawKeys = fMakeArrayRotationYaw(lRegressedKeys[0],lRegressedKeys[1])
fBakeRotationToKeys (BakedObjName2, lYawKeys)   