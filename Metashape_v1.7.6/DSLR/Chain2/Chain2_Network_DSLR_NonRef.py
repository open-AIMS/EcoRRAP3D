'''Authors and script details
@Eoghan @Januar @Sophie @Agustina @EcoRRAP

Title: Chain 2 Network-Adapted DSLR - NON-REFERENCE MODELS ONLY
Last edited: 27.11.2024
User input/checks required: Input path to 'SparseCloudClean_DSLR.py' script and check network server address is correct.

Script description:
Chain 2 Network processing. For use in the office/access to network processing. 
Before running the script, the full photo set needs to be imported, Chain 1 must be complete, and QAQC OK.

Functionality is:
1. High quality alignment (resets previous alignment)
2. Run sparse cloud filtering script (includes duplicate chunk before filtering)
3. Build depth maps (Medium quality: Downscale '4')
4. Build model (mesh)
5. Build texture
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
#IN LINE 71 BELOW: task.path = "YourFilePath/SparseCloudClean_DSLR.py" # Path to the script that duplicates and renames the chunk
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

#region: Align photos (High quality: Downscale '1')
task = Metashape.Tasks.MatchPhotos()
task.downscale = 1 
task.generic_preselection = True
task.reference_preselection = True
task.keypoint_limit = 40000
task.tiepoint_limit = 10000
task.reset_matches = True
tasks.append(task)

task = Metashape.Tasks.AlignCameras()
tasks.append(task)
#endregion

#region: Run sparse cloud filtering script (includes duplicate chunk before filtering)
task = Metashape.Tasks.RunScript()
task.path = "YourFilePath//SparseCloudClean_DSLR.py" #Check and change as required
tasks.append(task)
#endregion

#region: Build depth maps (Medium quality: Downscale '4')
chunk = doc.chunks[0]
task = Metashape.Tasks.BuildDepthMaps()
task.downscale = 4
task.reuse_depth = False
task.max_neighbors = 40
task.max_workgroup_size = 100
tasks.append(task)
#endregion

#region: Build model (mesh)
task = Metashape.Tasks.BuildModel()
task.surface_type = Metashape.Arbitrary
task.interpolation = Metashape.EnabledInterpolation
task.face_count = Metashape.FaceCount.HighFaceCount
task.source_data = Metashape.DepthMapsData
task.vertex_colors = True
task.vertex_confidence = True,
task.volumetric_masks = False,
task.keep_depth = True,
task.trimming_radius = 10
task.subdivide_task = True
task.workitem_size_cameras = 20
task.max_workgroup_size = 100
tasks.append(task)
#endregion

#region: Build texture
uv_task = Metashape.Tasks.BuildUV()
uv_task.mapping_mode = Metashape.MappingMode.GenericMapping  # Set the mapping mode
tasks.append(uv_task)
task = Metashape.Tasks.BuildTexture()
task.blending_mode = Metashape.BlendingMode.MosaicBlending  # Set the blending mode
task.texture_size = 8192  # Texture size
task.fill_holes = True  # Fill texture holes
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