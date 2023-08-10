
"""Interface to the image management server
This module contains the functionality to upload and download
imaging data (raw and metadata) form the OMERO server (v5.4).
It requires that the following software be installed within the Python
environment you are loading this module:
	* OMERO.cli (https://docs.openmicroscopy.org/omero/5.4.0/users/cli/index.html)
	* OMERO Python language bindings (https://docs.openmicroscopy.org/omero/5.4.0/developers/Python.html)
This code is based on the following documentation:
    https://docs.openmicroscopy.org/omero/5.4.0/developers/Python.html
It contains the following functions:
    * omero_connect - connects to server
    * TODO...
    
"""

import typer
from rich import print
from typing_extensions import Annotated
from typing import List
import configparser


#####################################

def get_omero_config(config_file_path):

    config = configparser.RawConfigParser()
    config.read(config_file_path)

    omero_username = config.get('OmeroServerSection', 'omero.username')
    omero_password = config.get('OmeroServerSection', 'omero.password')
    omero_host = config.get('OmeroServerSection', 'omero.host')
    omero_port = int(config.get('OmeroServerSection', 'omero.port'))

    return omero_username, omero_password, omero_host, omero_port

def format_xml_ouput(output_map):

    import xml.etree.ElementTree as ET

    output_root_element = ET.Element('omero-bifrost-output')
    for key in output_map.keys():
        output_element = ET.SubElement(output_root_element, "output-item")
        output_element.attrib = {"index":str(key),
                                 "type":output_map[key]["type"],
                                 "name":output_map[key]["name"],
                                 "id":output_map[key]["id"]}

    output_root_element.attrib = {"size":str(len(output_map.keys()))}
    xml_tree = ET.ElementTree(output_root_element)

    return xml_tree

def fetch_all_objects(conn):

    output_map = {}
    output_count = 0

    for project in conn.getObjects("Project"):

        output_map[output_count] = {"type": "project",
                                  "name": str(project.getName()),
                                  "id": str(project.getId())}
        output_count += 1

        for dataset in project.listChildren():

            output_map[output_count] = {"type": "dataset",
                                      "name": str(dataset.getName()),
                                      "id": str(dataset.getId())}
            output_count += 1
            
            for image in dataset.listChildren():

                output_map[output_count] = {"type": "image",
                                          "name": str(image.getName()),
                                          "id": str(image.getId())}
                output_count += 1

    return output_map

def print_data_tree(conn):
    """
    Prints all IDs of the data objects(Projects, Datasets, Images) associated with the logged in user on the OMERO server

    Args:
        conn: Established Connection to the OMERO Server via a BlitzGateway

    Returns:
        Nothing except a printed text output to console

    """

    from rich.tree import Tree
    from rich.table import Table

    tree = Tree("OMERO Data")

    for project in conn.getObjects("Project"):
    
        project_branch = tree.add("[bold red]" + str(project.getName()) + " : " + str(project.getId()))
        
        for dataset in project.listChildren():
    
            dataset_branch = project_branch.add("[blue]" + str(dataset.getName()) + " : " + str(dataset.getId()))

            image_table = Table(show_header=True, header_style="bold blue")
            image_table.add_column("Image Name", style="green")
            image_table.add_column("ID")

            dataset_branch.add(image_table)

            for image in dataset.listChildren():

                image_table.add_row(str(image.getName()), str(image.getId()))

    print(tree)


#################################

def omero_connect(usr, pwd, host, port):
    """
    Connects to the OMERO Server with the provided username and password.

    Args:
        usr: The username to log into OMERO
        pwd: a password associated with the given username
        host: the OMERO hostname
        port: the port at which the OMERO server can be reached

    Returns:
        Connected BlitzGateway to the OMERO Server with the provided credentials

    """
    from omero.gateway import BlitzGateway

    conn = BlitzGateway(usr, pwd, host=host, port=port)
    connected = conn.connect()
    conn.setSecure(True)

    if not connected:
        print("Error: Connection not available")

    return conn

def print_data_ids(conn):
    """
        Prints all IDs of the data objects(Projects, Datasets, Images) associated with the logged in user on the OMERO server

        Args:
            conn: Established Connection to the OMERO Server via a BlitzGateway

        Returns:
            Nothing except a printed text output to console

        """

    for project in conn.getObjects("Project"):
        print('project: ' + str(project.getName()) + ' -- ' + str(project.getId()))

        for dataset in project.listChildren():
            print('ds: ' + str(dataset.getName()) + ' -- ' + str(dataset.getId()))

            for image in dataset.listChildren():
                print('img: ' + str(image.getName()) + ' -- ' + str(image.getId()))

def get_omero_dataset_id(conn, project_name, dataset_name):
    """
    Gets the ID of the first encountered dataset with the given name
    (assumes the project and dataset names are unique IDs)
    
    Args:
        conn: Established Connection to the OMERO Server via a BlitzGateway
        openbis_project_id(project_name): Id specifying the project information stored on OpenBIS
        openbis_sample_id: Id specifying the sample information stored on OpenBIS
    Returns:
        omero_dataset_id:  Id specifying the dataset information stored on OMERO

    """

    omero_dataset_id = -1
    found_id = False

    my_exp_id = conn.getUser().getId()
    default_group_id = conn.getEventContext().groupId

    for project in conn.getObjects("Project"):

        if found_id:
            break

        if project.getName() == project_name:
            for dataset in project.listChildren():

                if dataset.getName() == dataset_name:
                    omero_dataset_id = dataset.getId()

                    found_id = True
                    break

    return omero_dataset_id

def register_image_file(file_path, project_id, sample_id, usr, pwd, host, port=4064):
    """
    This function imports an image file to an omero server using the OMERO.cli (using Bio-formats)
    This function assumes the OMERO.cli is installed
    Example:
        register_image_file("data/test_img.nd2", "project_x", "sample_y",
         "joe_usr", "joe_pwd", "192.168.2.2")
    Args:
        file_path (string): the path to the fastq file to validate
        project_id (string): the corresponding project ID in openBIS server
        sample_id (string): the corresponding sample ID in openBIS server
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

    conn = omero_connect(usr, pwd, host, str(port))
    ds_id = get_omero_dataset_id(conn, project_id, sample_id)

    if ds_id != -1:

        cmd = "omero-importer -s " + host + " -p " + str(port) + " -u " + usr + " -w " + pwd + " -d " + str(int(ds_id)) + " " + file_path
        print("----cmd: " + cmd)

        proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                            universal_newlines=True)

        std_out, std_err = proc.communicate()

        print("std_out: " + std_out)
        print("std_err: " + std_err)
        print("return_code: " + str(proc.returncode))

        if int(proc.returncode) == 0:

            print("-->" + std_out)

            fist_line = std_out.splitlines()[0]
            image_ids = fist_line[6:].split(',')

            print("id list: " + str(image_ids))

        else:
            print("return code fail")

    else:
        print("invalid sample_id")

    return image_ids

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


########################################
#functions to register numpy arrays

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

def add_annotations_to_image(conn, image_id, key_value_data):
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

#####################################

app = typer.Typer()

query_app = typer.Typer()
push_app = typer.Typer()
pull_app = typer.Typer()
app.add_typer(query_app, name="query", help="Query an OMERO server for Project, Dataset, and Image objects.")
app.add_typer(push_app, name="push", help="Push image data into an OMERO Server.")
app.add_typer(pull_app, name="pull", help="Pull image data from an OMERO Server.")

@query_app.command("list-all")
def query_list_all(
        config_file_path: Annotated[str, typer.Option("--config", "-c", help="Path to the OMERO config file")] = "./imaging_config.properties",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output XML file")] = "./omero_bifrost_output.xml",
        to_file: Annotated[bool, typer.Option(help="output to XML file")] = False,
        to_xml: Annotated[bool, typer.Option(help="Print XML ouput to system console")] = False
        ):

    import xml.etree.ElementTree as ET
    
    omero_username, omero_password, omero_host, omero_port = get_omero_config(config_file_path)
    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port))

    if to_file:
        xml_tree = format_xml_ouput(fetch_all_objects(conn))
        xml_tree.write(output_file_path)
    elif to_xml:
        xml_tree = format_xml_ouput(fetch_all_objects(conn))
        xml_str = ET.tostring(xml_tree.getroot(), encoding='unicode')
        print("[bold red]" + xml_str)
    else:
        print_data_tree(conn)



@query_app.command("dataset-id")
def query_dataset_id(
        project: Annotated[str, typer.Argument(help="The project name to be looked for (assumes it is a unique ID)")],
        dataset: Annotated[str, typer.Argument(help="The dataset name to be looked for (assumes it is a unique ID)")],
        config_file_path: Annotated[str, typer.Option("--config", "-c", help="Path to the OMERO config file")] = "./imaging_config.properties",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output XML file")] = "./omero_bifrost_output.xml",
        to_file: Annotated[bool, typer.Option(help="output to XML file")] = False,
        to_xml: Annotated[bool, typer.Option(help="Print XML ouput to system console")] = False
        ):
    
    import xml.etree.ElementTree as ET
    
    omero_username, omero_password, omero_host, omero_port = get_omero_config(config_file_path)
    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port))

    ds_id = get_omero_dataset_id(conn, project, dataset)

    output_map = {}
    output_map[0] = {"type": project,
                     "name": dataset,
                     "id": str(ds_id)}

    if to_file:
        xml_tree = format_xml_ouput(output_map)
        xml_tree.write(output_file_path)
    elif to_xml:
        xml_tree = format_xml_ouput(output_map)
        xml_str = ET.tostring(xml_tree.getroot(), encoding='unicode')
        print("[bold red]" + xml_str)
    else:
        print("[bold red]" + str(output_map))

@push_app.command("image")
def push_image_file(
        file_path: Annotated[str, typer.Argument(help="Path to the input image file")],
        dataset_id: Annotated[str, typer.Argument(help="ID of target dataset")],
        config_file_path: Annotated[str, typer.Option("--config", "-c", help="Path to the OMERO config file")] = "./imaging_config.properties",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output XML file")] = "./omero_bifrost_output.xml",
        to_file: Annotated[bool, typer.Option(help="output to XML file")] = False,
        to_xml: Annotated[bool, typer.Option(help="Print XML ouput to system console")] = False
        ):
    
    import xml.etree.ElementTree as ET
    
    omero_username, omero_password, omero_host, omero_port = get_omero_config(config_file_path)

    img_ids = register_image_file_with_dataset_id(file_path, int(dataset_id), omero_username, omero_password, omero_host)

    output_map = {}
    output_count = 0

    for id_i in img_ids:
        output_map[output_count] = {"type": "image",
                                    "name": "",
                                    "id": str(id_i)}
        output_count += 1

    if to_file:
        xml_tree = format_xml_ouput(output_map)
        xml_tree.write(output_file_path)
    elif to_xml:
        xml_tree = format_xml_ouput(output_map)
        xml_str = ET.tostring(xml_tree.getroot(), encoding='unicode')
        print("[bold red]" + xml_str)
    else:
        print("[bold red]" + str(output_map))

@push_app.command("key-value")
def push_key_value(
        image_id: Annotated[str, typer.Argument(help="ID of target image")],
        kv_pair: Annotated[List[str], typer.Option(default=..., help="Pairs of key-values, in format '--kv-pair key1:value1 --kv-pair key2:value2'")],
        config_file_path: Annotated[str, typer.Option("--config", "-c", help="Path to the OMERO config file")] = "./imaging_config.properties",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output XML file")] = "./omero_bifrost_output.xml",
        to_file: Annotated[bool, typer.Option(help="output to XML file")] = False,
        to_xml: Annotated[bool, typer.Option(help="Print XML ouput to system console")] = False
        ):
    
    import xml.etree.ElementTree as ET
    
    omero_username, omero_password, omero_host, omero_port = get_omero_config(config_file_path)
    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port))

    #string format: key1:value1//key2:value2//key3:value3//...
    key_value_data = []
    pair_list = kv_pair
    for pair in pair_list:
        key_value = pair.split(":")
        key_value_data.append(key_value)

    add_annotations_to_image(conn, image_id, key_value_data)

    print "0"
