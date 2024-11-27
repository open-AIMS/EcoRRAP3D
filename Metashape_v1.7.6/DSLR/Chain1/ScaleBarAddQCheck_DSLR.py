'''Authors and script details
 @Eoghan @Januar @Sophie @Agustina @EcoRRAP

Title: Scalebar Add and Quality Check DSLR (Local processing, step in Chain 1)
Last edited: 19.11.2024
User input/checks required: Input scalebar information in 'scalebar_data'c(target pair 1, target pair 2, distance between targets in metres)
'''
#region: Import libraries and define Metashape API
import Metashape
import sys
import os
from os import path

doc = Metashape.app.document
chunk = doc.chunk
#endregion

#region Add scalebars
scalebar_data = """
target 1,target 2,0.3
target 3,target 4,0.3
target 5,target 6,0.3
target 7,target 8,0.3
target 9,target 10,0.3
target 11,target 12,0.3
target 13,target 14,0.3
target 15,target 16,0.3
target 17,target 18,0.3
target 19,target 20,0.3
target 21,target 22,0.3
target 23,target 24,0.3
target 25,target 26,0.3
target 27,target 28,0.3
target 29,target 30,0.3
target 31,target 32,0.3
target 33,target 34,0.3
target 35,target 36,0.3
target 37,target 38,0.3
target 39,target 40,0.3
target 41,target 42,0.3
target 43,target 44,0.3
target 45,target 46,0.3
target 47,target 48,0.3
target 49,target 50,0.3
"""

if not chunk.scalebars:
    markers = {}
    for marker in chunk.markers:
        markers[marker.label] = marker

    # Read the scale bar data and add scale bars to the chunk
    lines = scalebar_data.strip().split('\n')
    for line in lines:
        t1, t2, dist = line.split(',')

        if t1 in markers.keys() and t2 in markers.keys():
            s = chunk.addScalebar(markers[t1], markers[t2])
            s.reference.distance = float(dist)
#endregion

# Scale the model and print warning if < 3 scalebars.
warnings = []  # Initialize the warnings list
if len(chunk.scalebars) >2:
    chunk.updateTransform()
else:
     warnings.append("WARNING: There are not enough scale bars. Inadequate detection of markers. Starting marker detection with higher tolerance.")
     chunk.remove(chunk.markers)
# Check if there are any warnings before printing
if warnings:
    print(warnings[0])  # Print the warning message
#endregion

# region Scale bar error check

# This section calculates the error of each scale bar, by comparing the estimated measurement of the scale bar
# with the input distance we have applied. 

sb_err = []

for scalebar in chunk.scalebars:
    dist_source = scalebar.reference.distance
    if not dist_source:
            continue #skipping scalebars without source values
    if type(scalebar.point0) == Metashape.Camera:
        if not (scalebar.point0.center and scalebar.point1.center):
                continue #skipping scalebars with undefined ends
        dist_estimated = (scalebar.point0.center - scalebar.point1.center).norm() * chunk.transform.scale
    else:
        if not (scalebar.point0.position and scalebar.point1.position):
                continue #skipping scalebars with undefined ends
        dist_estimated = (scalebar.point0.position - scalebar.point1.position).norm() * chunk.transform.scale
    dist_error = dist_estimated - dist_source
    print(str(dist_error))
    sb_err.append(dist_error)

# Check if any scale bar has an error >1 cm. If greater, print a warning.
for scalebar in chunk.scalebars:
    if dist_error > 0.01:
        warnings.append("The error on at least one scale bar is >1 cm - Manual intervention is needed.")
    else:
        print(dist_error)

print("Number of markers:" + str(len(chunk.markers)))

for marker in chunk.markers:
    print(marker.label + "had " + str(len(marker.projections)))

for scalebar in chunk.scalebars:
    print(scalebar.label + " error: " + str(dist_error*100) + "cm")

# Checks if there are any triads in the model

marker_list = []

for marker in chunk.markers:
    try:
        marker_list.append(int(marker.label[7:]))
    except ValueError:
        print(f"Skipping marker with invalid label: {marker.label}")


count = sum(map(lambda x : x>100, marker_list))

print('Count of Triad targets: ', count)

triad_1 = [102, 103, 104]
triad_2 = [105, 106, 107]
triad_3 = [108, 109, 110]
triad_4 = [111, 112, 113]
triad_5 = [114, 115, 116]
triad_6 = [117, 118, 119]
triad_7 = [120, 121, 112]

if all(value in marker_list for value in triad_1) or all(value in marker_list for value in triad_2) or all(value in marker_list for value in triad_3) or all(value in marker_list for value in triad_4) or all(value in marker_list for value in triad_5) or all(value in marker_list for value in triad_6) or all(value in marker_list for value in triad_7):
    print('At least one triad has been detected')
else:
    Metashape.app.messageBox("Warning - no complete triads have been detected. Please intervene.")
# endregion
