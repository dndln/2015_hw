import ipdb
import pandas as pd
from pattern import web
import sys

test_str = """
    <chart>
    <series>
    <value xid="0">1/27/2009</value>
    <value xid="1">1/28/2009</value>
    </series>
    <graphs>
    <graph gid="1" color="#000000" balloon_color="#000000" title="Approve">
    <value xid="0">62.3</value>
    <value xid="1">63.3</value>
    </graph>
    <graph gid="2" color="#FF0000" balloon_color="#FF0000" title="Disapprove">
    <value xid="0">19.0</value>
    <value xid="1">20.0</value>
    </graph>
    </graphs>
    </chart>
    """

def rcp_poll_data(xml_string):
    xml_tree = web.Element(xml_string)

    dataframe_dict = {}

    # assume there's only 1 series_tree
    series_tree = xml_tree.getElementsByTagname('series')[0]
    date_list = []
    # more explicitly: "for child in series_tree.children"
    for child in series_tree:
        if isinstance(child, web.Element):
            date_list.append(child.content)
    dataframe_dict['date'] = pd.to_datetime(date_list)

    graph_element_list = xml_tree.getElementsByTagname('graph')
    for graph_tree in graph_element_list:
        current_list_title = graph_tree.title
        current_list = []
        for child in graph_tree:
            if isinstance(child, web.Element):
                current_list.append(child.content)
        dataframe_dict[current_list_title] = current_list

    result = pd.DataFrame(dataframe_dict)
    return result


df = rcp_poll_data(test_str)
print(df)
