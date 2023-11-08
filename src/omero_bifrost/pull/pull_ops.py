
def download_original_image_file(orig_file_id, download_path, usr, pwd, host, port=4064):
    """
    """

    import subprocess

    if orig_file_id != -1:
        cmd = "omero download -s " + host + " -p " + str(port) + " -u " + usr + " -w " + pwd + " " + str(orig_file_id) + " " + download_path
        proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                            universal_newlines=True)

        std_out, std_err = proc.communicate()
    
    return std_out, std_err

def export_ome_tiff_file(image_id, download_path, usr, pwd, host, port=4064):
    """
    """

    import subprocess
    import os

    if image_id != -1:
        
        # add ome.tiff extension if missing in filename
        name, ext = os.path.splitext(download_path)
        if  ext != ".tif" and ext != ".tiff":
            download_path = download_path + "ome.tiff"

        cmd = "omero export -s " + host + " -p " + str(port) + " -u " + usr + " -w " + pwd + " --file " + str(download_path) + " --type TIFF Image:" + str(image_id)
        proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                            universal_newlines=True)

        std_out, std_err = proc.communicate()
    
    return std_out, std_err


########################################
#functions to pull numpy arrays

def get_image_array(conn, image_id):
    """
    This function retrieves an image from an OMERO server as a numpy array
    TODO
    """

    import numpy as np

    image = conn.getObject("Image", image_id)

    #construct numpy array (t, c, x, y, z)

    size_x = image.getSizeX()
    size_y = image.getSizeY()
    size_z = image.getSizeZ()
    size_c = image.getSizeC()
    size_t = image.getSizeT()

    # X and Y fields have to be aligned this way since during generation of the image from the numpy array the 2darray is expected to be (Y,X)
    # See Documentation here https://downloads.openmicroscopy.org/omero/5.5.1/api/python/omero/omero.gateway.html#omero.gateway._BlitzGateway
    hypercube = np.zeros((size_t, size_c, size_y, size_x, size_z))

    pixels = image.getPrimaryPixels()

    for t in range(size_t):
        for c in range(size_c):
            for z in range(size_z):
                plane = pixels.getPlane(z, c, t)      # get a numpy array.
                hypercube[t, c, :, :, z] = plane

    return hypercube

