
def register_image_file_with_dataset_id(file_path, dataset_id, usr, pwd, host, port=4064):
    """
    This function imports an image file to an omero server using the OMERO-py (using Bio-formats)
    This function assumes OMERO-py (cli) is installed
    Example:
        register_image_file("data/test_img.nd2", 10,
         "joe_usr", "joe_pwd", "192.168.2.2")
    Args:
        file_path (string): the path to the fastq file to validate
        dataset_id (string): the ID of the omero dataset
        usr (string): username for the OMERO server
        pwd (string): password for the OMERO server
        host (string): OMERO server address
        port (int): OMERO server port
    Returns:
        list of strings: list of newly generated omero IDs for registered images
                (a file can contain many images)
    """

    import subprocess

    image_ids = []

    ds_id = dataset_id

    if ds_id != -1:
        cmd = "omero import -s " + host + " -p " + str(port) + " -u " + usr + " -w " + pwd + " -d " + str(int(ds_id)) + " " + file_path
        proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                            universal_newlines=True)

        std_out, std_err = proc.communicate()

        # the terminal output of the omero-importer tool provides a lot of information on the registration process 
        # we are looking for a line with this format: "Image:id_1,1d_2,id_3,...,id_n"
        # where id_1,...,id_n are a list of ints, which denote the unique OMERO image IDs for the image file
        # (one file can have many images)

        if int(proc.returncode) == 0:
            for line in std_out.splitlines():
                if line[:6] == "Image:":
                    image_ids = line[6:].split(',')
                    break
        else:
            image_ids = []
    else:
        image_ids = []
    return image_ids

def register_image_folder_with_dataset_id(folder_path, dataset_id, usr, pwd, host, port=4064):
    """
    """

    import subprocess

    image_ids = []

    ds_id = dataset_id

    if ds_id != -1:
        cmd = "omero import -s " + host + " -p " + str(port) + " -u " + usr + " -w " + pwd + " -d " + str(int(ds_id)) + " --depth 1 " + folder_path
        proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                            universal_newlines=True)

        std_out, std_err = proc.communicate()

        # the terminal output of the omero-importer tool provides a lot of information on the registration process 
        # we are looking for a line with this format: "Image:id_1,1d_2,id_3,...,id_n"
        # where id_1,...,id_n are a list of ints, which denote the unique OMERO image IDs for the image file
        # (one file can have many images)

        if int(proc.returncode) == 0:
            for line in std_out.splitlines():
                if line[:6] == "Image:":
                    image_ids.extend(line[6:].split(','))
        else:
            image_ids = []
    else:
        image_ids = []
    return image_ids

def attach_file_to_image(file_path, image_id, usr, pwd, host, port=4064):
    """
    This function imports an image file to an omero server using the OMERO-py (using Bio-formats)
    This function assumes OMERO-py (cli) is installed
    Example:
        register_image_file("data/test_img.nd2", 10,
         "joe_usr", "joe_pwd", "192.168.2.2")
    Args:
        file_path (string): the path to the fastq file to validate
        dataset_id (string): the ID of the omero dataset
        usr (string): username for the OMERO server
        pwd (string): password for the OMERO server
        host (string): OMERO server address
        port (int): OMERO server port
    Returns:
        list of strings: list of newly generated omero IDs for registered images
                (a file can contain many images)
    """

    import subprocess

    original_file_id = ""
    file_ann_id = ""
    image_ann_link_id = ""

    # upload original file and get ID

    cmd = "omero upload -s " + host + " -p " + str(port) + " -u " + usr + " -w " + pwd + " " + file_path
    proc = subprocess.Popen(cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                        universal_newlines=True)
    std_out, std_err = proc.communicate()

    if int(proc.returncode) == 0:
        for line in std_out.splitlines():
            if line[:13] == "OriginalFile:":
                original_file_id = line[13:]
                break

    # create new file annotation

    cmd = "omero obj -s " + host + " -p " + str(port) + " -u " + usr + " -w " + pwd + " " + "new FileAnnotation file=OriginalFile:" + original_file_id

    proc = subprocess.Popen(cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                        universal_newlines=True)
    std_out, std_err = proc.communicate()

    if int(proc.returncode) == 0:
        for line in std_out.splitlines():
            if line[:15] == "FileAnnotation:":
                file_ann_id = line[15:]
                break

    # create new annotation link

    cmd = "omero obj -s " + host + " -p " + str(port) + " -u " + usr + " -w " + pwd + " " + "new ImageAnnotationLink parent=Image:" + str(image_id) + " child=FileAnnotation:" + file_ann_id

    proc = subprocess.Popen(cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                        universal_newlines=True)
    std_out, std_err = proc.communicate()

    if int(proc.returncode) == 0:
        for line in std_out.splitlines():
            if line[:20] == "ImageAnnotationLink:":
                image_ann_link_id = line[20:]
                break

    return image_ann_link_id

def create_tag(tag_value, tag_desc, usr, pwd, host, port=4064):
    """
    """

    import subprocess

    tag_id = -1

    cmd = "omero tag create -s " + host + " -p " + str(port) + " -u " + usr + " -w " + pwd + " --name " + str(tag_value) + " --desc '" + str(tag_desc) + "'"
    proc = subprocess.Popen(cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                        universal_newlines=True)

    std_out, std_err = proc.communicate()

    if int(proc.returncode) == 0:
        for line in std_out.splitlines():
            if line[:14] == "TagAnnotation:":
                tag_id = int(line[14:])
                break
    
    return tag_id

def add_tag_to_image(image_id, tag_id, usr, pwd, host, port=4064):
    """
    """

    import subprocess
    
    cmd = "omero tag link -s " + host + " -p " + str(port) + " -u " + usr + " -w " + pwd + " Image:" + str(image_id) + " " + str(tag_id)
    proc = subprocess.Popen(cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                        universal_newlines=True)

    std_out, std_err = proc.communicate()
    
    return std_out, std_err

def add_kv_to_image(conn, image_id, key_value_data):
    """
    This function is used to add key-value pair annotations to an image
    Example:
        key_value_data = [["Drug Name", "Monastrol"], ["Concentration", "5 mg/ml"]]
        add_annotations_to_image(conn, image_id, key_value_data)
    Args:
        conn: Established Connection to the OMERO Server via a BlitzGateway
        image_id (int): An OMERO image ID
        key_value_data (list of lists): list of key-value pairs
    Returns:
        int: not relevant atm
    """

    import omero

    map_ann = omero.gateway.MapAnnotationWrapper(conn)
    # Use 'client' namespace to allow editing in Insight & web
    namespace = omero.constants.metadata.NSCLIENTMAPANNOTATION
    map_ann.setNs(namespace)
    map_ann.setValue(key_value_data)
    map_ann.save()

    image = conn.getObject("Image", image_id)
    # NB: only link a client map annotation to a single object
    image.linkAnnotation(map_ann)

    return 0


########################################
#functions to push numpy arrays

def generate_array_plane(new_img):
    """
    TODO
    """

    img_shape = new_img.shape
    size_z = img_shape[4]
    size_t = img_shape[0]
    size_c = img_shape[1]

    for z in range(size_z):              # all Z sections
        for c in range(size_c):          # all channels
            for t in range(size_t):      # all time-points

                new_plane = new_img[t, c, :, :, z]
                yield new_plane

def create_array(conn, img, img_name, img_desc, ds):
    """
    TODO
    """

    dims = img.shape
    z = dims[4]
    t = dims[0]
    c = dims[1]

    new_img = conn.createImageFromNumpySeq(generate_array_plane(img),
                                           img_name,
                                           z, c, t,
                                           description=img_desc,
                                           dataset=ds)

    return new_img.getId()

def register_image_array(img, img_name, img_desc, project_id, sample_id, usr, pwd, host, port=4064):
    """
    This function imports a 5D (time-points, channels, x, y, z) numpy array of an image
    to an omero server using the OMERO Python bindings 
    Example:
        register_image_array(hypercube, "tomo_0", "this is a tomogram",
         "project_x", "sample_y", "joe_usr", "joe_pwd", "192.168.2.2")
    Args:
        file_path (string): the path to the fastq file to validate
        project_id (string): the corresponding project ID in openBIS server
        sample_id (string): the corresponding sample ID in openBIS server
        usr (string): username for the OMERO server
        pwd (string): password for the OMERO server
        host (string): OMERO server address
        port (int): OMERO server port
    Returns:
        int: newly generated omero ID for registered image array
    """

    img_id = -1
    save_flag = 0

    conn = omero_connect(usr, pwd, host, str(port))

    for project in conn.getObjects("Project"):
        if project.getName() == project_id:
            for dataset in project.listChildren():
                if dataset.getName() == sample_id:

                    img_id = create_array(conn, img, img_name, img_desc, dataset)

                    save_flag = 1
                    break
        if save_flag == 1:
            break

    return int(img_id)


