import numpy as np
import vtk
from vtk.util import numpy_support
import base64
import struct



#VTP Writer so we just save the coords + radii -> Glyph for Spheres
def writeVTP(coords, radii, outFile):
    print("Writing sphere points to ", outFile)

    coords = np.asarray(coords, dtype=np.float64)
    radii = np.asarray(radii, dtype=np.float64)

    points = vtk.vtkPoints()
    points.SetData(numpy_support.numpy_to_vtk(coords, deep=True))

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)

    radius_array = numpy_support.numpy_to_vtk(radii, deep=True)
    radius_array.SetName("radius")
    polydata.GetPointData().AddArray(radius_array)
    polydata.GetPointData().SetActiveScalars("radius")

    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(outFile)
    writer.SetInputData(polydata)
    writer.SetDataModeToBinary()
    writer.SetCompressorTypeToZLib()

    if writer.Write() != 1:
        raise RuntimeError(f"Failed to write {outFile}")

    print("Finished writing VTP:", outFile)

#save a CSV with the following format : x,y,z,r
def writeCSV(coords, radii, fileName):
    #create columnstack from the coords and radii
    data = np.column_stack((coords, radii))
    np.savetxt(
        fileName,
        data,
        delimiter=",",
        header="x,y,z,r",
        comments=""
    )
    print("Saved ", fileName)