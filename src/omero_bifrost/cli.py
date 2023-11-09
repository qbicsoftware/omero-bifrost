
"""Interface to the image management server
This module contains the functionality to upload and download
imaging data (raw and metadata) form the OMERO server (v5.6).
It requires that the following software be installed within the Python
environment you are loading this module:
	* OMERO-py
It contains the following functions:
    * omero_connect - connects to server
    * TODO...
    
"""

import typer
from rich import print
from typing_extensions import Annotated
from typing import List

#####################################

from omero_bifrost.utils.util_ops import get_omero_config, format_xml_ouput, omero_connect, img_map_from_tsv
from omero_bifrost.query.query_ops import fetch_all_objects, print_data_tree, print_data_ids, get_omero_dataset_id
from omero_bifrost.push.push_ops import register_image_file_with_dataset_id, register_image_folder_with_dataset_id 
from omero_bifrost.push.push_ops import attach_file_to_image, create_tag, add_tag_to_image, add_kv_to_image
from omero_bifrost.pull.pull_ops import download_original_image_file, export_ome_tiff_file

#####################################

app = typer.Typer()

query_app = typer.Typer()
push_app = typer.Typer()
pull_app = typer.Typer()
app.add_typer(query_app, name="query", help="Query an OMERO server for Project, Dataset, and Image objects.")
app.add_typer(push_app, name="push", help="Push image data into an OMERO Server.")
app.add_typer(pull_app, name="pull", help="Pull image data from an OMERO Server.")


@query_app.command("list-all", help="Query all accessible OMERO objects")
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

    conn.close()


@query_app.command("dataset-id", help="Query the ID of an OMERO dataset using project and dataset names")
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
    output_map[0] = {"type": "dataset",
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

    conn.close()

@query_app.command("img-ids", help="Query image IDs from OMERO using key-value pairs and tags")
def query_image_ids(
        p_name: Annotated[List[str], typer.Option(default=..., help="Project names to restrict query scope (assumes names are unique IDs), in format '--p-name name1 --p-name name2'")] = [],
        kv_pair: Annotated[List[str], typer.Option(default=..., help="Pairs of key-values for query, in format '--kv-pair key1:value1 --kv-pair key2:value2'")] = [],
        tag: Annotated[List[str], typer.Option(default=..., help="Tag values for query, in format '--tag value1 --tag value2'")] = [],
        config_file_path: Annotated[str, typer.Option("--config", "-c", help="Path to the OMERO config file")] = "./imaging_config.properties",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output TSV file")] = "./omero_bifrost_output.tsv",
        to_file: Annotated[bool, typer.Option(help="output to XML file")] = False,
        to_xml: Annotated[bool, typer.Option(help="Print XML ouput to system console")] = False
        ):
    
    import xml.etree.ElementTree as ET

    import ezomero
    import csv

    project_name_list = p_name

    #string format: key1:value1//key2:value2//key3:value3//...
    key_value_data = []
    kv_pair_list = kv_pair
    for pair in kv_pair_list:
        key_value = pair.split(":")
        key_value_data.append(key_value)

    tag_list = tag

    omero_username, omero_password, omero_host, omero_port = get_omero_config(config_file_path)
    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port))

    if len(project_name_list) > 0:
        project_obj_list = []
        for project_name in project_name_list:
            project_obj_list.extend(list(conn.getObjects("Project", attributes={"name": project_name})))
    else:
        project_obj_list = list(conn.getObjects("Project"))

    image_map = {}
    for project in project_obj_list:
        print("[bold blue]Inspecting project: " + str(project.getName()) + " (ID: " + str(project.getId()) + ")")
        for dataset in project.listChildren():
            for image in dataset.listChildren():
                img_path = (project.getName() + "/" + dataset.getName()).replace(" ", "_")
                img_name = image.getName().replace(" ", "_")
                image_map[int(image.getId())] = [img_path, img_name] # id -> path and name

    image_id_list = list(image_map.keys())

    for kv in key_value_data:
        image_id_list = ezomero.filter_by_kv(conn, image_id_list, key=kv[0], value=kv[1], across_groups=True)

    for tag in tag_list:
        image_id_list = ezomero.filter_by_tag_value(conn, image_id_list, tag_value=tag, across_groups=True)

    print("[bold green]Output image IDs: " + str(image_id_list))

    with open(output_file_path, 'w', newline='') as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t', lineterminator='\n')
        writer.writerow(['OMERO_IMG_ID', 'OMERO_IMG_PATH', 'OMERO_IMG_NAME'])
        for img_id in image_id_list:
            writer.writerow([img_id, image_map[img_id][0], image_map[img_id][1]])

    conn.close()


@push_app.command("img-file", help="Import an image file into OMERO")
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

    img_ids = register_image_file_with_dataset_id(file_path, int(dataset_id), omero_username, omero_password, omero_host, str(omero_port))

    output_map = {}
    output_count = 0

    for id_i in img_ids:
        output_map[output_count] = {"type": "image",
                                    "name": file_path,
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

@push_app.command("img-folder", help="Import a folder containing image files into OMERO")
def push_image_folder(
        folder_path: Annotated[str, typer.Argument(help="Path to the input folder containing image files (depth=1)")],
        dataset_id: Annotated[str, typer.Argument(help="ID of target dataset")],
        config_file_path: Annotated[str, typer.Option("--config", "-c", help="Path to the OMERO config file")] = "./imaging_config.properties",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output XML file")] = "./omero_bifrost_output.xml",
        to_file: Annotated[bool, typer.Option(help="output to XML file")] = False,
        to_xml: Annotated[bool, typer.Option(help="Print XML ouput to system console")] = False
        ):
    
    import xml.etree.ElementTree as ET
    
    omero_username, omero_password, omero_host, omero_port = get_omero_config(config_file_path)

    img_ids = register_image_folder_with_dataset_id(folder_path, int(dataset_id), omero_username, omero_password, omero_host, str(omero_port))

    output_map = {}
    output_count = 0

    for id_i in img_ids:
        output_map[output_count] = {"type": "image",
                                    "name": folder_path,
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

@push_app.command("key-value", help="Annotate an image with key-value pairs")
def push_key_value(
        image_id: Annotated[str, typer.Argument(help="ID of target image")],
        kv_pair: Annotated[List[str], typer.Option(default=..., help="Pairs of key-values, in format '--kv-pair key1:value1 --kv-pair key2:value2'")],
        config_file_path: Annotated[str, typer.Option("--config", "-c", help="Path to the OMERO config file")] = "./imaging_config.properties",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output XML file")] = "./omero_bifrost_output.xml",
        to_file: Annotated[bool, typer.Option(help="output to XML file")] = False,
        to_xml: Annotated[bool, typer.Option(help="Print XML ouput to system console")] = False
        ):
    
    omero_username, omero_password, omero_host, omero_port = get_omero_config(config_file_path)
    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port))

    #string format: key1:value1//key2:value2//key3:value3//...
    key_value_data = []
    pair_list = kv_pair
    for pair in pair_list:
        key_value = pair.split(":")
        key_value_data.append(key_value)

    add_kv_to_image(conn, image_id, key_value_data)

    conn.close()
    print("[bold red]Done.")

@push_app.command("img-tag", help="Tag an image, create OMERO tag if needed")
def push_image_tag(
        image_id: Annotated[str, typer.Argument(help="ID of target image")],
        tag_value: Annotated[str, typer.Argument(help="Text value of OMERO tag")],
        tag_desc: Annotated[str, typer.Option("--desc", "-d", help="Tag description used when creating new tag")] = "",
        config_file_path: Annotated[str, typer.Option("--config", "-c", help="Path to the OMERO config file")] = "./imaging_config.properties",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output XML file")] = "./omero_bifrost_output.xml",
        to_file: Annotated[bool, typer.Option(help="output to XML file")] = False,
        to_xml: Annotated[bool, typer.Option(help="Print XML ouput to system console")] = False
        ):
    
    omero_username, omero_password, omero_host, omero_port = get_omero_config(config_file_path)
    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port))

    tags = conn.getObjects("TagAnnotation", attributes={"textValue": tag_value})
    tags = list(tags)

    tag_id = -1

    if len(tags) > 0:
        tag = tags[0]
        tag_id = str(tag.getId())
    else:
        tag_id = create_tag(tag_value, tag_desc, omero_username, omero_password, omero_host, str(omero_port))

    if int(tag_id) > -1:
        std_out, std_err = add_tag_to_image(image_id, tag_id, omero_username, omero_password, omero_host, str(omero_port))

    conn.close()

    print("[bold blue]Output: " + std_out)
    print("[bold red]Error: " + std_err)

@push_app.command("file-atch", help="Attach a file to image")
def push_file_atch(
        file_path: Annotated[str, typer.Argument(help="Path to the attachment file")],
        image_id: Annotated[str, typer.Argument(help="ID of target image")],
        config_file_path: Annotated[str, typer.Option("--config", "-c", help="Path to the OMERO config file")] = "./imaging_config.properties",
        output_file_path: Annotated[str, typer.Option("--output", "-o", help="Path to output XML file")] = "./omero_bifrost_output.xml",
        to_file: Annotated[bool, typer.Option(help="output to XML file")] = False,
        to_xml: Annotated[bool, typer.Option(help="Print XML ouput to system console")] = False
        ):
    
    omero_username, omero_password, omero_host, omero_port = get_omero_config(config_file_path)

    img_ann_id = attach_file_to_image(file_path, image_id, omero_username, omero_password, omero_host, str(omero_port))

    print("[bold blue]File Annotation ID: " + str(img_ann_id))

@pull_app.command("ome-tiffs", help="Export OME-TIFF image files from a list of OMERO image IDs")
def pull_ome_tiff_files(
        output_path: Annotated[str, typer.Argument(help="Output path, destination of pulled files")],
        img_id: Annotated[List[str], typer.Option(default=..., help="List of image IDs, in format '--img-id id1 --img-id id2'")] = [],
        id_list_path: Annotated[str, typer.Option("--list", "-l", help="Path to a TSV file with image IDs, takes priority if not empty")] = "",
        config_file_path: Annotated[str, typer.Option("--config", "-c", help="Path to the OMERO config file")] = "./imaging_config.properties"
        ):

    import os

    if id_list_path == "":
        img_id_list = img_id
    else:
        img_map = img_map_from_tsv(id_list_path)
        img_id_list = list(img_map.keys())

    print("[bold green]Processing image ID list: " + str(img_id_list))
    
    omero_username, omero_password, omero_host, omero_port = get_omero_config(config_file_path)
    
    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port))

    file_map = {}
    for img_id in img_id_list:
        image = conn.getObject("Image", img_id)
        if not img_id in file_map.keys():
                file_map[img_id] = str(image.getName()).replace(" ", "_")

    # TODO: fix, previously imported '.tif' files are not automatically exported as OME-TIFF by OMERO,
    #       these files need to be downloaded as original files. Look into triggering OME-TIFF generation in OMERO

    for img_id in file_map.keys():
        ouput_file_path = os.path.join(output_path, "omero_img_id_" + str(img_id) + "__" + file_map[img_id] + ".ome.tiff")
        print("[bold blue]Pulling: " + ouput_file_path)
        std_out, std_err = export_ome_tiff_file(img_id, ouput_file_path, omero_username, omero_password, omero_host, str(omero_port))
        print("[bold blue]Output: " + std_out)
        print("[bold red]Error: " + std_err)

    conn.close()

@pull_app.command("orig-files", help="Download original image files from a list of OMERO image IDs")
def pull_original_image_files(
        output_path: Annotated[str, typer.Argument(help="Output path, destination of pulled files")],
        img_id: Annotated[List[str], typer.Option(default=..., help="List of image IDs, in format '--img-id id1 --img-id id2'")] = [],
        id_list_path: Annotated[str, typer.Option("--list", "-l", help="Path to a TSV file with image IDs, takes priority if not empty")] = "",
        config_file_path: Annotated[str, typer.Option("--config", "-c", help="Path to the OMERO config file")] = "./imaging_config.properties"
        ):

    import os

    if id_list_path == "":
        img_id_list = img_id
    else:
        img_map = img_map_from_tsv(id_list_path)
        img_id_list = list(img_map.keys())

    print("[bold green]Processing image ID list: " + str(img_id_list))
    
    omero_username, omero_password, omero_host, omero_port = get_omero_config(config_file_path)

    conn = omero_connect(omero_username, omero_password, omero_host, str(omero_port))

    orig_file_map = {}
    for img_id in img_id_list:
        image = conn.getObject("Image", img_id)

        if len(image.getFileset().listFiles()) > 0:
            orig_file_obj = image.getFileset().listFiles()[0] # assume first file is original image file
            orig_file_id = str(orig_file_obj.getId()) 
            if not orig_file_id in orig_file_map.keys():
                orig_file_map[orig_file_id] = str(orig_file_obj.getName())

    for orig_file_id in orig_file_map.keys():
        ouput_file_path = os.path.join(output_path, "omero_file_id_" + str(orig_file_id) + "__" + orig_file_map[orig_file_id])
        print("[bold blue]Pulling: " + ouput_file_path)
        std_out, std_err = download_original_image_file(orig_file_id, ouput_file_path, omero_username, omero_password, omero_host, str(omero_port))
        print("[bold blue]Output: " + std_out)
        print("[bold red]Error: " + std_err)

    conn.close()

