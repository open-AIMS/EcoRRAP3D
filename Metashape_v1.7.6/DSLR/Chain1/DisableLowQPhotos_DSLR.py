'''Authors and script details
 @Eoghan @Januar @Sophie @Agustina @EcoRRAP

Title: Disable Low Quality Photos DSLR (Local processing, step in Chain 1)
Last edited: 19.11.2024
User input/checks required: None
Script specifications: Minimum number of photos enabled: 2000
'''

#region: Import libraries and define Metashape API
import Metashape
import sys
import os
from os import path

doc = Metashape.app.document
chunk = doc.chunk
#endregion

# region Quality Control
x = 0
for camera in chunk.cameras:
    x = x + 1

photos_init = x
camera = chunk.cameras[0]
if not camera.frames[0].meta["Image/Quality"]: # Only runs if image quality not yet assessed
    chunk.analyzePhotos() # Estimate image quality
for camera in chunk.cameras:
    if float(camera.meta["Image/Quality"]) < 0.5:
        camera.enabled = False # Disable photos with a quality value < 0.5

x = 0 # Placeholder counter starting at 0 for purpose of counting how many photos disabled
for camera in chunk.cameras:
    if camera.enabled:
        x = x + 1 # Increases the counter by 1 for every enabled photo

if x < 2000:
    x = 0 # resets counter to 0
    for camera in chunk.cameras:
        camera.enabled = True # Re-enables all cameras if < 2000 photos enabled
        if float(camera.meta["Image/Quality"]) <0.45: # Repeats same process with a lower threshold
            camera.enabled = False
        if camera.enabled:
            x = x + 1

if x < 2000:
    x = 0 # resets counter to 0
    for camera in chunk.cameras:
        camera.enabled = True # Re-enables all cameras if < 2000 photos enabled
        if float(camera.meta["Image/Quality"]) <0.4: # Repeats same process with a lower threshold
            camera.enabled = False
        if camera.enabled:
            x = x + 1


if x < 2000:
    for camera in chunk.cameras:
        camera.enabled = True # Re-enables all cameras if < 2000 photos enabled
        if float(camera.meta["Image/Quality"]) <0.35:# Repeats same process with a lower threshold
            camera.enabled = False

#region Print results

#Number of images enabled
x = 0
for camera in chunk.cameras:
    if camera.enabled:
        x = x + 1
photos_final = x # Number of photos enabled after quality control
print(f"Number of photos enabled: {x}") # Print the number of photos enabled

warnings = [] #Warning message if < 2000 photos enabled
if x <2000:
    warnings.append("WARNING: Number of photos is less than 2000 even with the lowest threshold. Manual "
                         "intervention needed. Script will continue from here anyway.")
if warnings:  # Check if the list is not empty
    print(warnings[0])  # Print the warning message

# Image quality threshold selected
lowest_quality = min(float(camera.meta["Image/Quality"]) for camera in chunk.cameras if camera.enabled)
print(f"Lowest image quality of enabled photos = {lowest_quality}")

# endregion
