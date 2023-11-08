
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
    from rich import print

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

