'''Authors and script details
@Eoghan @Januar @Sophie @Agustina @EcoRRAP

Title: Chain 1 Local Processing GoPro
Last edited: 25.11.2024   
User input/checks required: You will be prompted for the target depth csv file location.

Script description:
Chain 1 Local processing. For use in the field or situations with no access to network processing. 
Before running the script, the full photo set needs to be imported. 

Functionality is:
1. Quality checks all images and disables all < 0.5. If < 2000 photos, process repeats enabling/disabling at thresholds of 0.45, 0.4, 0.35 until 2000 photos achieved (error printed if not achieved). 
2. Aligns photo at Lowest quality. Warning printed if < 80 % alignment.
3. Detects markers  at specified initial and secondary tolerance (25 % then 50 %). Removes projections if pixel error is > 10. Disables markers if < 1 projections.
4. Adds scale bars based on marker pairings provided in lines X file
5. Checks no. scale bars and if < 1 deletes all markers, detects with secondary tolerance. Adds scale bars again, then performs same check.
7. Imports X Y Z depth values, co-ordinates, and error from specified depth csv.
8. Checks scale bar error and prints error if > 0.01 cm
9. Saves document
10. Prints number of photos enabled/disabled at the start and end of script, percentage photos aligned, number of markers and triads detected, scalebar error. Everything that happens will be in a process log file that is deposited in the same folder the project is in.
'''

#region Import libraries and define Metashape API

import Metashape
import sys
import os
from os import path
import math

doc = Metashape.Document()
chunk = Metashape.app.document.chunk
#endregion 

#region Define variables
#IN LINES 76, 85, 95, 109, 110, 111 BELOW: Minimum number of photos required = 2000
#IN LINES 121, 124 BELOW: Alignment quality = Medium
tolerance_firstattempt = 85 # Marker tolerance
tolerance_secondattempt = 95 # Marker tolerance if too few scalebars on first attempt
min_marker_projections = 10 # Disable markers with less than this number
marker_projection_error_threshold = 150 # Remove marker projections from photos where error is greater than this value
targetpath = Metashape.app.getOpenFileName("Specify path to the depth csv:") #Prompted as popup when script is run
scalebar_error_threshold = 0.02 # Threshold for scale bar error
#IN LINES 314, 316 BELOW: minimum number of scalebars: 7
#IN LINES 272-297 AND 376-382 BELOW: Define scalebar (marker) pairs and distance between markers, and triad targets
#endregion

#region Set log path
current_dir = path.dirname(Metashape.app.document.path)
Metashape.app.settings.log_path = path.join(current_dir + "/log.txt")
Metashape.app.settings.log_enable = True
#endregion


#region: Photo quality check
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
#endregion

#region: Align photos (Medium quality: Downscale '2')
if not chunk.point_cloud:
    chunk.matchPhotos(
        downscale=2, 
        generic_preselection=True, 
        reference_preselection=True, 
        keypoint_limit=40000, 
        tiepoint_limit=4000
    )
    chunk.alignCameras()

x = 0
y = 0

for camera in chunk.cameras: # Checks for 80 % alignment of photographs, prints warning if not achieved
    x = x + 1
    if camera.transform:
        y = y + 1

if y < (x * 0.8):
    Metashape.app.messageBox("WARNING: Poor alignment of photos. Recommend processing this plot manually")
print(str(y/x*100) + "% of photos aligned")
#endregion

#region: Marker Detection and Error Check
# detect inverted circular 12bit coded markers
if not chunk.markers:
    chunk.detectMarkers(
        target_type=Metashape.TargetType.CircularTarget12bit,
        tolerance=tolerance_firstattempt,
        filter_mask=False,
        inverted=True,
        noparity=False,
        maximum_residual=5,
        minimum_size=0,
        minimum_dist=5
    )
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

# Print results
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

#region: Import depth data
chunk.importReference(targetpath, delimiter=",",columns = "nxyzXYZ",
                      items = Metashape.ReferenceItemsMarkers)
#endregion

#region: Add scale bars and check error
#Add scalebars
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

# Scale the model and print warning if < 7 scalebars.
warnings = []  # Initialize the warnings list
if len(chunk.scalebars) >6:
    chunk.updateTransform()
else:
     warnings.append("WARNING: There are not enough scale bars. Inadequate detection of markers. Starting marker detection with higher tolerance.")
     chunk.remove(chunk.markers)
# Check if there are any warnings before printing
if warnings:
    print(warnings[0])  # Print the warning message

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

# Check if any scale bar has an error >2 cm. If greater, print a warning.
for scalebar in chunk.scalebars:
    if dist_error > 0.02:
        warnings.append("The error on at least one scale bar is >2 cm - Manual intervention is needed.")
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
#endregion