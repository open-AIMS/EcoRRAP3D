'''Authors and script details
Eoghan @Januar @Sophie @Agustina @EcoRRAP

Title: Sparsecloud edit GoPro
Last edited: 27.11.2024
User input/checks required:None

Script description:
Sript is loaded as part of processing Chain 2. 
It edits the sparse cloud in the following way:
- Deletes all points outside the bounding box
- Performs an initial optimisation of the cameras 
- Sets the criteria for simultaneous point selection (see 'Define user input variables')
- Simultaneously selects all points not meeting specifed criteria, then checks whether over half of the sparse cloud is selected
- If > 50 % of the sparse cloud is selected, then reduces the selection to half (too avoid losing too many points)
- Optimizes cameras
- Conducts 5 x loops of selecting points based on reprojection error by removing the worst 10 % of points and then optimising.
- This loop will stop if EITHER reprojection error is <0.5 OR point cloud size reaches < 30 % of original size
- Performs final, full optimisation

It is unlikely with our data that we get to 0.5, but in this way the
routine is looking for a target and can be stopped in 2 different ways,
which will improve the estimation of positions of the camera network.
'''

#region: Define user input variables
reconst_uncertainty = 50 # ideal is 10
projection_accuracy = 10  # ideal is 3
reprojection_error = 0.5  # ideal is 0.5
min_percentage = 0.3 # Lower threshold of points for reprojection error improvement
#endregion

#region: Import libraries and define Metashape API
import Metashape as ms
import math
import sys
app = ms.app
docpath = app.document.path
doc = ms.Document()
chunk = ms.app.document.chunk
doc.open(docpath, read_only=False, ignore_lock=True)
chunk = ms.app.document.chunk
#endregion

#region: Duplicate chunk to preserve source
duplicate = True
if duplicate is True:
    chunk_label = chunk.label  # create reference to source chunk
    chunk.copy()  # duplicate source chunk
    chunks = ms.app.document.chunks  # update reference to chunks
    # set reference to the duplicated chunks since we will be working with this chunk:
    dupeChunk = ms.app.document.chunks[len(ms.app.document.chunks)-1]
    if dupeChunk in chunks:
        dupeChunk.label = str(chunk_label) + " _UnFiltered"  # rename duplicated chunk
#endregion

#region: Remove points outside bounding box
chunk = doc.chunks[0]
R = chunk.region.rot  # Bounding box rotation matrix
C = chunk.region.center  # Bounding box center vector
size = chunk.region.size

chunk.point_cloud.points

for point in chunk.point_cloud.points:

    if point.valid:
        v = point.coord
        v.size = 3
        v_c = v - C
        v_r = R.t() * v_c

        if abs(v_r.x) > abs(size.x / 2.):
            point.valid = False
        elif abs(v_r.y) > abs(size.y / 2.):
            point.valid = False
        elif abs(v_r.z) > abs(size.z / 2.):
            point.valid = False
        else:
            continue
#endregion

#region: Calculate initial reprojection error and points
def calc_reprojection(chunk):
    point_cloud = chunk.point_cloud
    points = point_cloud.points
    npoints = len(points)
    projections = chunk.point_cloud.projections
    err_sum = 0
    num = 0
    point_ids = [-1] * len(point_cloud.tracks)
    for point_id in range(0, npoints):
        point_ids[points[point_id].track_id] = point_id

    for camera in chunk.cameras:
        if not camera.transform:
            continue
        for proj in projections[camera]:
            track_id = proj.track_id
            point_id = point_ids[track_id]
            if point_id < 0:
                continue
            point = points[point_id]
            if not point.valid:
                continue
            error = camera.error(point.coord, proj.coord).norm() ** 2
            err_sum += error
            num += 1
    sigma = math.sqrt(err_sum / num)
    return (sigma)

reproj_initial = calc_reprojection(chunk)
points_initial = len(chunk.point_cloud.points)
#endregion

#region: Create filter options
# create reference to filter technique
selection = ms.PointCloud.Filter()
# generate filter options
# options = ms.PointCloud.Filter(.ReprojectionError,
#                                       .ReconstructionUncertainty,
#                                       .ImageCount, # do not use
#                                       .ProjectionAccuracy)
# gradual selection settings  
actions = \
    [
        [ms.PointCloud.Filter.ReconstructionUncertainty, reconst_uncertainty],
        [ms.PointCloud.Filter.ProjectionAccuracy, projection_accuracy],
        [ms.PointCloud.Filter.ReprojectionError, reprojection_error]
    ]
#endregion

#region: Optimise cameras
chunk.optimizeCameras(
    fit_f=True,
    fit_cx=True,
    fit_cy=True,
    fit_b1=False,
    fit_b2=False,
    fit_k1=True,
    fit_k2=True,
    fit_k3=True,
    fit_k4=False,
    fit_p1=True,
    fit_p2=True,
    fit_corrections=False,
    adaptive_fitting=False,
    tiepoint_covariance=False
)
#endregion

#region: Conduct gradual selection
for index, filterOption in enumerate(actions):
    print("=========================================================================")
    print("performing filter action " +
          str(index) + ", " + str(filterOption[0]))
    print("=========================================================================")

    # If current action is not reprojection error, run below
    if filterOption[0] is not ms.PointCloud.Filter.ReprojectionError:
        # perform filter selection
        selection.init(
            chunk,
            criterion=filterOption[0]
        )
        # select all points above the passed threshold value
        selection.selectPoints(filterOption[1])
        nselected = len(
            [p for p in chunk.point_cloud.points if p.selected])
        half_points = (len(chunk.point_cloud.points) * 0.5)

        # check if less than half of all points are selected;
        # if more, then re-select half the points only
        if nselected < half_points:
            selection.removePoints(filterOption[1])
        else:
            copy_points = selection.values.copy()
            copy_points.sort()
            t50 = copy_points[int(len(copy_points) * 0.5)]
            selection.selectPoints(t50)
            selection.removePoints(t50)
        # optimise cameras
        chunk.optimizeCameras(
            fit_f=True,
            fit_cx=True,
            fit_cy=True,
            fit_b1=False,
            fit_b2=False,
            fit_k1=True,
            fit_k2=True,
            fit_k3=True,
            fit_k4=False,
            fit_p1=True,
            fit_p2=True,
            fit_corrections=False,
            adaptive_fitting=False,
            tiepoint_covariance=False
        )
    # time for reprojection errors
    # filter by reprojection error (removes 10 % of data each time up to 5 times)
    # if threshold is reached then stop the loop and optimise cameras
    else:
        repError = calc_reprojection(chunk)
        # repeat 5 times so that what remains are 100 % * 0.9^5 = 59 % of the data
        for i in range(5): 
            if repError > filterOption[1] and len(chunk.point_cloud.points) > points_initial*min_percentage:
                selection.init(
                    chunk,
                    criterion=ms.PointCloud.Filter.ReprojectionError
                )
                values = selection.values.copy()
                values.sort()  # sort the filter values by reprojection error
                # identify 10 % points with highest reprojection error:
                thresh = values[int(len(values) * 0.9)]
                selection.selectPoints(thresh)  # select those points
                # no. of points selected
                nselected = len(
                    [p for p in chunk.point_cloud.points if p.selected])
                chunk.point_cloud.removeSelectedPoints()
                print(nselected,"points removed during reprojection error filtering")
                # Camera optimisation
                chunk.optimizeCameras(
                    fit_f=True,
                    fit_cx=True,
                    fit_cy=True,
                    fit_b1=True,
                    fit_b2=True,
                    fit_k1=True,
                    fit_k2=True,
                    fit_k3=True,
                    fit_k4=False,
                    fit_p1=True,
                    fit_p2=True,
                    fit_corrections=False,
                    adaptive_fitting=False,
                    tiepoint_covariance=False)
#endregion

#region: Perform final full optimisation
chunk.optimizeCameras(
    fit_f=True,
    fit_cx=True,
    fit_cy=True,
    fit_b1=True,
    fit_b2=True,
    fit_k1=True,
    fit_k2=True,
    fit_k3=True,
    fit_k4=True,
    fit_p1=True,
    fit_p2=True,
    fit_corrections=True,
    adaptive_fitting=False,
    tiepoint_covariance=True)

points_final = len(chunk.point_cloud.points)
chunk.updateTransform()
doc.save()
#endregion







