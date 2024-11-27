'''Authors and script details
 @Eoghan @Januar @Sophie @Agustina @EcoRRAP

Title: Marker Quality Check GoPro (Local processing, step in Chain 1)
Last edited: 19.11.2024
User input/checks required: None
'''
#region: Import libraries and define Metashape API
import Metashape
import sys
import os
from os import path
import math

doc = Metashape.app.document
chunk = doc.chunk
#endregion

#region Set variables
min_marker_projections = 10 # Disable markers with less than this number
marker_projection_error_threshold = 150 # Remove marker projections from photos where error is greater than this value
tolerance_secondattempt = 95 # Marker tolerance if too few scalebars on first attempt
chunk = doc.chunks[0]
#endregion

#region Marker Quality check 
# Disable markers that don't meet specified projections
for marker in chunk.markers:
    if len(marker.projections) < min_marker_projections:
        marker.enabled = False

    print(marker.label + " has " +
          str(len(marker.projections)) + " projections")

# For each marker in list of markers for active chunk, disable markers from each camera with error greater than input value

for marker in chunk.markers:
    # skip marker if it has no position
    if not marker.position:
        print(marker.label + " is not defined in 3D, skipping...")
        continue

    # reference the position of the marker
    position = marker.position

    # for each camera in the list of cameras for current marker
    for camera in marker.projections.keys():
        if not camera.transform:
            continue
        proj = marker.projections[camera].coord
        reproj = camera.project(position)
        error = (proj - reproj).norm()
        
        # disable markers with projection error greater than input value
        if error > marker_projection_error_threshold:
            # set the current marker projection to none for current camera/marker combination
            marker.projections[camera] = None

# Detect markers again with higher tolerance if necessary
if not chunk.markers:
    chunk.detectMarkers(
        target_type=Metashape.TargetType.CircularTarget12bit,
        tolerance=tolerance_secondattempt,
        filter_mask=False,
        inverted=True,
        noparity=False,
        maximum_residual=5,
        minimum_size=0,
        minimum_dist=5
    )

    for marker in chunk.markers:
        # if marker has < minimum number of projections, disable marker
        if len(marker.projections) < min_marker_projections:
            marker.enabled = False

    for marker in chunk.markers:
        print(marker.label + " has " +
              str(len(marker.projections)) + " projections")

    # For each marker in list of markers for active chunk, disable markers from each
    for marker in chunk.markers:
        # skip marker if it has no position
        if not marker.position:
            print(marker.label + " is not defined in 3D, skipping...")
            continue

        # reference the position of the marker
        position = marker.position

        # for each camera in the list of cameras for current marker
        for camera in marker.projections.keys():
            if not camera.transform:
                continue
            proj = marker.projections[camera].coord
            reproj = camera.project(position)
            error = (proj - reproj).norm()

            # disable markers with projection error > marker projection threshold
            if error > marker_projection_error_threshold:
                # set the current marker projection to none for current camera/marker combination
                marker.projections[camera] = None


# Disable markers with < 1 projection
for marker in chunk.markers:
    if len(marker.projections) < 1:
        marker.enabled = False

#endregion

#region Print results
print("Number of markers:" + str(len(chunk.markers)))

for marker in chunk.markers: # Print reprojection error for markers
    if not marker.position:
        print(marker.label + " is not defined in 3D, skipping...")
        continue
    position = marker.position
    proj_error = list()
    proj_sqsum = 0
    for camera in marker.projections.keys():
        if not camera.transform:
            continue #skipping not aligned cameras
        image_name = camera.label
        proj = marker.projections[camera].coord
        reproj = camera.project(marker.position)
        error = reproj - proj
        proj_error.append(error.norm())
        proj_sqsum += error.norm()**2
    if len(proj_error):
        error = math.sqrt(proj_sqsum / len(proj_error))
        print(marker.label + " had " + str(len(marker.projections)) + " projections. The error was " + str(error))
#endregion