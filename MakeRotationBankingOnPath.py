# making an object banking along this position trajectory with some smooth factor on rotation
from pyfbsdk import *
import numpy as np
import math
from scipy.signal import symiirorder1

obj_1 = "Marker PreRoot"
sSmoothFactor = 0.75 # value in [0.0;1.0]  range for scipy.signal.symiirorder1 filter

#-----------------------------
def fGetKeyRange (obj_name):
    ProcObj = FBFindModelByLabelName (obj_name)
    ProcObj = FBFindModelByLabelName (obj_name)
    lStart = ProcObj.Translation.GetAnimationNode().Nodes[0].FCurve.Keys[0].Time.GetFrame()
    lStop = ProcObj.Translation.GetAnimationNode().Nodes[0].FCurve.Keys[-1].Time.GetFrame()
    return (lStart,lStop)
    
#-----------------------------
def fFillArrayCurveKeys (obj_name, firstFrame, lastFrame) :
    ProcObj = FBFindModelByLabelName (obj_name)
    ProcObj = FBFindModelByLabelName (obj_name)
    Keys = []
    for i in range (0, (lastFrame-firstFrame+1)):
        Keys.append ((ProcObj.Translation.GetAnimationNode().Nodes[0].FCurve.KeyGetValue (i),\
                               ProcObj.Translation.GetAnimationNode().Nodes[1].FCurve.KeyGetValue (i),\
                               ProcObj.Translation.GetAnimationNode().Nodes[2].FCurve.KeyGetValue (i)))
    return Keys
#-----------------------------
def filter_array (PosKeysArray, lFilterParam):
    x1= symiirorder1 ( np.array(PosKeysArray)[:,0], 1, lFilterParam)
    y1= symiirorder1 ( np.array(PosKeysArray)[:,1], 1, lFilterParam)
    z1= symiirorder1 ( np.array(PosKeysArray)[:,2], 1, lFilterParam)
    res = []
    for i in range (0, len (x1)-1):
        res.append ((x1[i], y1[i], z1[i]))
    return  res
#-----------------------------
def aim_yaw_rotation(from_pos, to_pos) :
    direction = np.array(to_pos) - np.array(from_pos)
    yaw = math.degrees(math.atan2(direction[0], direction[2]))  #pitch formula: pitch = math.degrees(-math.atan2(direction[1],math.sqrt(direction[0]**2 + direction[2]**2)))
    return yaw     
#-----------------------------
def fMakeArrayRotationYaw (PosKeysArray) :
    lFilteredPos = filter_array (PosKeysArray, sSmoothFactor) # smoothing/filtering factor is here
    lYawArray = []
    for i in range (0, len (lFilteredPos) -1) :             
        lYawArray.append(aim_yaw_rotation(lFilteredPos[i],lFilteredPos[i+1]))
    return lYawArray
#-----------------------------
def fBakeRotationToKeys (obj_name, yaw_values) :  
    lBakeObj = FBFindModelByLabelName (obj_name)
    lBakeObj.Translation.SetAnimated(True)        
    if not lBakeObj:
        print("Object {} not found".format(obj_name))
        return
    lBakeObj.Rotation.GetAnimationNode().Nodes[0].FCurve.EditClear()
    lBakeObj.Rotation.GetAnimationNode().Nodes[1].FCurve.EditClear()
    lBakeObj.Rotation.GetAnimationNode().Nodes[2].FCurve.EditClear()
    yaw_node = lBakeObj.Rotation.GetAnimationNode().Nodes[1]
    for i in range(len(yaw_values)):
        time = FBTime(0,0,0,i+lTakeStart,0)
        yaw_node.KeyAdd(time, yaw_values[i])    
#-----------------------------

lTakeStart, lTakeEnd = fGetKeyRange(obj_1)
lPosKeysArray = fFillArrayCurveKeys (obj_1, lTakeStart, lTakeEnd) 
lYawKeyArray = fMakeArrayRotationYaw (lPosKeysArray)
fBakeRotationToKeys (obj_1, lYawKeyArray)
