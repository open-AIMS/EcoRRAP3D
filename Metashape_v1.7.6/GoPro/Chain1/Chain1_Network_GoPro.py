'''Authors and script details
@Eoghan @Januar @Sophie @Agustina @EcoRRAP

Title: Chain 1 Network-Adapted GoPro
Last edited: 19.11.2024   
User input/checks required: Input path to 'DisableLowQPhotos.py', 'MarkerQCheck.py,' and 'ScaleBarAddErrorCheck.py' script, and check network server address is correct. You will also be prompted for the target depth csv file location.

Script description:
Chain 1 Network processing. For use in the office/access to network processing. 
Before running the script, the full photo set just needs to be imported. 

Functionality is:
1: Quality checks all images and disables all < 0.5. If < 1500 photos, process repeats enabling/disabling at thresholds of 0.45, 0.4, 0.35 until 2000 photos achieved (error printed if not achieved). 
2: Aligns photo at Medium quality. Warning printed if < 80 % alignment.
3: Detects markers at specified initial and secondary tolerance (85 % then 95 %). Removes projections if pixel error is > 10. Disables markers if < 1 projections.
4: Adds scale bars based on marker pairings provided in ScaleBarAddErrorCheck_GoPro.py file
5: Checks no. scale bars and if < 1 deletes all markers, detects with secondary tolerance. Adds scale bars again, then performs same check.
7: Imports X Y Z depth values, co-ordinates, and error from specified depth csv.
8: Checks scale bar error and prints error if > 0.01 cm
9: Saves document
10: Prints number of photos enabled/disabled at the start and end of script, percentage photos aligned, number of markers and triads detected, scalebar error. Everything that happens will be in a process log file that is deposited in the same folder the project is in.
'''

#region Import libraries and define Metashape API

import Metashape
import sys
import os
from os import path
import math

app = Metashape.app
docpath = app.document.path
doc = Metashape.Document()
chunk = Metashape.app.document.chunk
#endregion 

#region Define variables
#IN 'DisableLowQPhotos.py': Minimum number of photos required = 1500
#IN LINE 87 BELOW: Alignment quality = Medium
#IN LINE 75 BELOW: task.path = "YourFilePath/DisableLowQPhotos_GoPro.py" # Path to the script that disables low-quality photos
tolerance_firstattempt = 85 # Marker tolerance
#IN LINE 106 BELOW: task.path = "YourFilePath/MarkerQCheck_GoPro.py" #Check and change as required
#IN 'MarkerQCheck_GoPro.py' SCRIPT: tolerance_secondattempt = 95 # Marker tolerance if too few scalebars on first attempt
#IN 'MarkerQCheck_GoPro.py' SCRIPT: min_marker_projections = 10 # Disable markers with less than this number
#IN 'MarkerQCheck_GoPro.py' SCRIPT: marker_projection_error_threshold = 150 # Remove marker projections from photos where error is greater than this value
targetpath = Metashape.app.getOpenFileName("Specify path to the depth csv:") #Prompted as popup when script is run
#IN LINE 121 BELOW: task.path = "YourFilePath/ScaleBarAddErrorCheck_GoPro.py" # Path to scale bar detection script
#IN 'ScaleBarAddErrorCheck_GoPro.py' SCRIPT: scalebar_error_threshold = 0.02 # Threshold for scale bar error
#IN 'ScaleBarAddErrorCheck_GoPro.py' SCRIPT: minimum number of scalebars: 7
#IN 'ScaleBarAddErrorCheck_GoPro.py' SCRIPT: define scalebar (marker) pairs and distance between markers
#endregion

#region Set network server and log path
network_server = 'YourNetworkServer' # Network server address
Metashape.app.settings.network_path = 'YourFilePath'# Path to the network folder
client = Metashape.NetworkClient()

current_dir = os.path.dirname(Metashape.app.document.path)
Metashape.app.settings.log_path = os.path.join(current_dir + "/log.txt")
Metashape.app.settings.log_enable = True
#endregion

#region: Save project
doc.open(docpath, read_only=False, ignore_lock=True)
doc.save()
#endregion

#region: Create network task list
tasks = []  
chunk = doc.chunks[0]
#endregion

#region: Quality control
task = Metashape.Tasks.AnalyzePhotos()
tasks.append(task)

# Create a task to run the script that disables low-quality photos
task = Metashape.Tasks.RunScript()
task.path = "YourFilePath/DisableLowQPhotos_GoPro.py" # Path to the script that disables low-quality photos
tasks.append(task)
#endregion

#region: Align photos (Medium) quality: Downscale '2')
task = Metashape.Tasks.MatchPhotos()
task.downscale = 2
task.generic_preselection = True
task.reference_preselection = True
task.keypoint_limit = 40000
task.tiepoint_limit = 10000
task.reset_matches = True
tasks.append(task)

task = Metashape.Tasks.AlignCameras()
tasks.append(task)
#endregion

#region: Marker Detection and Error Check
task = Metashape.Tasks.DetectMarkers()
task.target_type = Metashape.TargetType.CircularTarget12bit
task.tolerance = tolerance_firstattempt
task.filter_mask = False
task.inverted = True
task.noparity = False
task.maximum_residual = 5
task.minimum_size = 0
task.minimum_dist = 5
tasks.append(task)

task = Metashape.Tasks.RunScript()
task.path = "YourFilePath/MarkerQCheck_GoPro.py" #Check and change as required
tasks.append(task)
#endregion

#region: Import depth data
task = Metashape.Tasks.ImportReference()
task.path = targetpath
task.delimiter = ","
task.columns = "nxyzXYZ"
task.items = Metashape.ReferenceItemsMarkers
tasks.append(task)
#endregion

#region: Scale Bar Add and Error Check
task = Metashape.Tasks.RunScript()
task.path = "//YourFilePath/ScaleBarAddQCheck_GoPro.py" # Path to scale bar detection script
tasks.append(task)
#endregion

#region: Convert task list to network tasks and print output
network_tasks = []
for task in tasks:
    if task.target == Metashape.Tasks.DocumentTarget:
        network_tasks.append(task.toNetworkTask(doc))
    else:
        network_tasks.append(task.toNetworkTask(chunk))

client = Metashape.NetworkClient()
client.connect(app.settings.network_host)  # server ip
batch_id = client.createBatch(docpath, network_tasks)
client.resumeBatch(batch_id)

Metashape.app.messageBox("Tasks have been sent to the network. Please reopen this project without saving and it will display the progress of the jobs you have just sent.")
#endregion