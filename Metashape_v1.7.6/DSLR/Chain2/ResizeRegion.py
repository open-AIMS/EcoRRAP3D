'''Authors and script details
 @Eoghan @Januar @Sophie @Agustina @EcoRRAP

Title: Resize Region (Network processing, step in Chain 2.1 - REFERENCE MODELS ONLY)
Last edited: 25.11.2024
User input/checks required: None
'''
#region: Import libraries and define Metashape API
import Metashape
import sys
import os

doc = Metashape.app.document
chunk = doc.chunk
#endregion

#region: Resize region to 12 x 6 x 10 m (x,y,z)

for chunk in doc.chunks:
    print("Resizing bounding box...")
    new_size = Metashape.Vector([12, 6, 10]) #size in the coordinate system units
    S = chunk.transform.scale
    crs = chunk.crs

    region = chunk.region
    region.size = new_size / S
    chunk.region = region
