'''Authors and script details
 @Eoghan @Januar @Sophie @Agustina @EcoRRAP

Title: Chain 3 (Local processing, NON-REFERENCE MODELS ONLY)
Last edited: 27.11.2024
User input/checks required: None

Script description:
Chain 3 Local processing. 
Before running the script, the full photo set needs to be imported, Chain 1 and 2 must be complete, and QAQC OK.

Functionality is:
1. Apply transformation matrix
2. Apply reference bounding box (extent) 
'''
#region: Import libraries and define Metashape API
import Metashape
import sys
import os
from PySide2 import QtWidgets
import time

doc = Metashape.app.document
chunk = doc.chunk
#endregion

#region Define variables
path = Metashape.app.getOpenFileName("Specify path to the transformation matrix") #Path to transformation matrix file
current = Metashape.app.getOpenFileName("Specify path to the current project:") #Path to current project
ref = Metashape.app.getOpenFileName("Specify path to the reference project:") #Path to reference project (for bounding box/extent)
#endregion

#region: Apply transformation matrix
#Specify path to the transformation matrix and open
#path = Metashape.app.getOpenFileName("Specify path to the transformation matrix") #Step completed in 'Define variables' section
f = open(path , 'r')
content = f.read()

#Convert string to list then a matrix
content = content.replace("\n", " ")
a = content.split(" ")
T = [[float(a[0]), float(a[1]), float(a[2]), float(a[3])],
    [float(a[4]), float(a[5]), float(a[6]), float(a[7])],
    [float(a[8]), float(a[9]), float(a[10]), float(a[11])],
    [float(a[12]), float(a[13]), float(a[14]), float(a[15])]]

#Create a Metashape matrix and apply to chunk
m = Metashape.Matrix(T)
chunk.transform.matrix = m * chunk.transform.matrix
doc.save()
#endregion

#region: Apply reference bounding box
#current = Metashape.app.getOpenFileName("Specify path to the current project:") #Step completed in 'Define variables' section
#ref = Metashape.app.getOpenFileName("Specify path to the reference project:") #Step completed in 'Define variables' section
#Select region of the first chunk in the project
doc.open(ref)
chunk = doc.chunks[0]
region = chunk.region

#Get the transformation matrix, region, centre, and size of the reference region
T0 = chunk.transform.matrix
region = chunk.region
R0 = region.rot
C0 = region.center
s0 = region.size

#Ensure the center vector has 4 components and set the fourth component to 1
C0.size = 4
C0.w = 1

# Open the current project and set the first chunk
doc.open(current)
chunk = doc.chunks[0]

#Calculate and apply the reference extent using the transformation matrix
T = chunk.transform.matrix.inv() * T0
R = Metashape.Matrix([[T[0, 0], T[0, 1], T[0, 2]], [T[1, 0], T[1, 1], T[1, 2]], [T[2, 0], T[2, 1], T[2, 2]]])
scale = R.row(0).norm()
R = R * (1 / scale)
region.rot = R * R0
c = T * C0
c = c / c[3] / 1.
c.size = 3
region.center = c
region.size = s0 * scale / 1.

#Update the region and save
chunk.region = region
doc.save()
#endregion

print("Script Finished. Transformation matrix applied and bounding box aligned")

