from fnmatch import fnmatch

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import requests
from pattern import web

import ipdb
import re
import bs4
import tqdm

# set some nicer defaults for matplotlib
from matplotlib import rcParams

#these colors come from colorbrewer2.org. Each is an RGB triplet
dark2_colors = [(0.10588235294117647, 0.6196078431372549, 0.4666666666666667),
                (0.8509803921568627, 0.37254901960784315, 0.00784313725490196),
                (0.4588235294117647, 0.4392156862745098, 0.7019607843137254),
                (0.9058823529411765, 0.1607843137254902, 0.5411764705882353),
                (0.4, 0.6509803921568628, 0.11764705882352941),
                (0.9019607843137255, 0.6705882352941176, 0.00784313725490196),
                (0.6509803921568628, 0.4627450980392157, 0.11372549019607843),
                (0.4, 0.4, 0.4)]
cycler = matplotlib.rcsetup.cycler('color', dark2_colors)
rcParams['figure.figsize'] = (10, 6)
rcParams['figure.dpi'] = 150
# rcParams['axes.color_cycle'] = dark2_colors
rcParams['axes.prop_cycle'] = cycler
rcParams['lines.linewidth'] = 2
rcParams['axes.grid'] = True
rcParams['axes.facecolor'] = '#eeeeee'
rcParams['font.size'] = 14
rcParams['patch.edgecolor'] = 'none'

def get_poll_xml(poll_id):
    url = 'http://charts.realclearpolitics.com/charts/{}.xml'.format(poll_id)
    xml = requests.get(url).text
    return xml

def _strip(s):
    """This function removes non-letter characters from a word

    for example _strip('Hi there!') == 'Hi there'
    """
    return re.sub(r'[\W_]+', '', s)

def plot_colors(xml):
    """
    Given an XML document like the link above, returns a python dictionary
    that maps a graph title to a graph color.

    Both the title and color are parsed from attributes of the <graph> tag:
    <graph title="the title", color="#ff0000"> -> {'the title': '#ff0000'}

    These colors are in "hex string" format. This page explains them:
    http://coding.smashingmagazine.com/2012/10/04/the-code-side-of-color/

    Example
    -------
    >>> plot_colors(get_poll_xml(1044))
    {u'Approve': u'#000000', u'Disapprove': u'#FF0000'}
    """
    dom = web.Element(xml)
    result = {}
    for graph in dom.by_tag('graph'):
        title = _strip(graph.attributes['title'])
        result[title] = graph.attributes['color']
    return result

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

    # sometimes there's more than 2 graphs
    graph_element_list = xml_tree.getElementsByTagname('graph')
    for graph_tree in graph_element_list:
        current_list_title = graph_tree.title
        current_list = []
        for child in graph_tree:
            if isinstance(child, web.Element):
                current_list.append(child.content)
        dataframe_dict[current_list_title] = current_list

    result = pd.DataFrame(dataframe_dict)

    # remove rows with empty strings and convert to floats
    # as this is called by error_data()
    candidates = [c for c in result.columns if c is not 'date']
    for col in candidates:
        result = result[result[col] != '']
        result[col] = result[col].astype(float)

    return result

def poll_plot(poll_id):
    """
    Make a plot of an RCP Poll over time

    Parameters
    ----------
    poll_id : int
        An RCP poll identifier
    """

    # hey, you wrote two of these functions. Thanks for that!
    xml = get_poll_xml(poll_id)
    data = rcp_poll_data(xml)
    colors = plot_colors(xml)

    #remove characters like apostrophes
    data = data.rename(columns = {c: _strip(c) for c in data.columns})

    # remove rows where column is an empty string, then convert to float
    # sometimes the third column is an empty string!
#     data = data[data[colors.keys()[0]] != '']
#     pdb.set_trace()
    for key in colors.keys():
        data = data[data[key] != '']
        data[key] = data[key].astype(float)


    # normalize poll numbers so they add to 100%
    norm = data[colors.keys()].sum(axis=1) / 100
    for c in colors.keys():
        data[c] /= norm


    for label, color in colors.items():
        plt.plot(data['date'], data[label], color=color, label=label)

    plt.xticks(rotation=70)
    plt.legend(loc='best')
    plt.xlabel("Date")
    plt.ylabel("Normalized Poll Percentage")

def find_governor_races(html):
    pattern = '(http:\/\/www\.realclearpolitics\.com\/epolls\/[0-9]+\/governor\/[a-z]+\/\w+\-[0-9]+\.html)'
    url_list = re.findall(pattern, html)
    return url_list

def race_result(url):
    html = requests.get(url).text
    soup = bs4.BeautifulSoup(html, 'html.parser')
    # find all 'table' tags, with a class of 'data'
    data_table_list = soup.find_all('table', 'data')

    first_data_table = data_table_list[0]
    header_row = first_data_table.find_all('tr')[0]
    first_row = first_data_table.find_all('tr')[1]
    header_row_list = list(header_row.stripped_strings)
    first_row_list = list(first_row.stripped_strings)

    df = pd.DataFrame(dict(zip(header_row_list, first_row_list)), index=[0])

    # reduce to candidate columns
    for col in df.columns:
        try:
            df[col] = df[col].astype(float)
        except ValueError as e:
            df.drop(col, axis=1, inplace=True)

    # normalise
    norm = df.sum(axis=1) / 100
    for c in df.columns:
        df[c] /= norm

    # clean col names
    rename_dict = {}
    for col in df.columns:
        # match.groups() doesn't work
        try:
            cleaned_name = re.search('.+?(?= \()', col).group(0)
        # fails for people without ' (D)' or ' (R)'
        except AttributeError as e:
            cleaned_name = col
        rename_dict[col] = cleaned_name
    df = df.rename(columns=rename_dict)

    # convert to dict
    out_dict = df.T.to_dict()[0]

    return out_dict

def id_from_url(url):
    """Given a URL, look up the RCP identifier number"""
    return url.split('-')[-1].split('.html')[0]

def plot_race(url):
    """Make a plot summarizing a senate race

    Overplots the actual race results as dashed horizontal lines
    """
    #hey, thanks again for these functions!
    id = id_from_url(url)
    xml = get_poll_xml(id)
    colors = plot_colors(xml)

    if len(colors) == 0:
        return

    #really, you shouldn't have
    result = race_result(url)

    poll_plot(id)
    plt.xlabel("Date")
    plt.ylabel("Polling Percentage")

    for r in result:
        plt.axhline(result[r], color=colors[_strip(r)], alpha=0.6, ls='--')

def party_from_color(color):
    if color in ['#0000CC', '#3B5998']:
        return 'democrat'
    if color in ['#FF0000', '#D30015']:
        return 'republican'
    return 'other'


def error_data(url):
    """
    Given a Governor race URL, download the poll data and race result,
    and construct a DataFrame with the following columns:

    candidate: Name of the candidate
    forecast_length: Number of days before the election
    percentage: The percent of poll votes a candidate has.
                Normalized so that the candidate percentages add to 100%
    error: Difference between percentage and actual race reulst
    party: Political party of the candidate

    The data are resampled as necessary, to provide one data point per day
    """

    id = id_from_url(url)
    xml = get_poll_xml(id)

    colors = plot_colors(xml)
    if len(colors) == 0:
        return pd.DataFrame()

    df = rcp_poll_data(xml)
    result = race_result(url)

    #remove non-letter characters from columns
    df = df.rename(columns={c: _strip(c) for c in df.columns})
    # this will actually add keys while not removing the old ones.
    for k, v in result.items():
        result[_strip(k)] = v

    candidates = [c for c in df.columns if c is not 'date']

    #turn into a timeseries...
    df.index = df.date # this keeps 'date' as a column as well as making it the index

    #...so that we can resample at regular, daily intervals
    # added .mean() as .resample() is now deferred
    df = df.resample('D').mean()
    df = df.dropna()
    # add the date back in
    df['date'] = df.index

    #compute forecast length in days
    #(assuming that last forecast happens on the day of the election, for simplicity)
    forecast_length = (df['date'].max() - df['date']).values
    forecast_length = forecast_length / np.timedelta64(1, 'D')  # convert to number of days

    #compute forecast error
    errors = {}
    normalized = {}
    poll_lead = {}

    for c in candidates:
        #turn raw percentage into percentage of poll votes
        # normalise proportion, also deals with multiple candidates!
        corr = df[c].values / df[candidates].sum(axis=1).values * 100.
        # result[_strip(c)] is a scalar of the final result (also normalised)
        # comes from race_result()
        err = corr - result[_strip(c)]

        normalized[c] = corr
        errors[c] = err
    # same as len(df), really
    n = forecast_length.size

    result = {}
    result['percentage'] = np.hstack(normalized[c] for c in candidates)
    result['error'] = np.hstack(errors[c] for c in candidates)
    # make the candidate name as long as the df, then hstack them
    result['candidate'] = np.hstack(np.repeat(c, n) for c in candidates)
    # the 'color' dict comes outta nowhere
    result['party'] = np.hstack(np.repeat(party_from_color(colors[_strip(c)]), n) for c in candidates)
    # hstack forecast_length the same number of times as there are candidates,
    # as it's the days are the same for everyone
    result['forecast_length'] = np.hstack(forecast_length for _ in candidates)

    result = pd.DataFrame(result)
    return result

def all_error_data():
    page = requests.get(
        'http://www.realclearpolitics.com/epolls/2010/governor/2010_elections_governor_map.html').text.encode('ascii', 'ignore')
    url_list = find_governor_races(page)
    error_df_list = []
    for url in tqdm.tqdm(url_list):
        current_error_data = error_data(url)
        error_df_list.append(current_error_data)

    df = pd.concat(error_df_list, ignore_index=True)
    return df


def bootstrap_resample(url):
    errors = all_error_data()
    election_result = race_result(url)
    selected_errors = np.random.choice(errors['error'], N)

    candidate_list = list(election_result.keys())

    # There's only 2 candidates in the examples required so I'm going to
    # ignore the possiblity of more!
    first_candidate = candidate_list[0]
    second_candidate = candidate_list[1]
    first_candidate_result = election_result[first_candidate]

    fcr_before_array = np.repeat(first_candidate_result, N)
    fcr_after_array = fcr_before_array + selected_errors
    # np.where returns indexes if (x, y) not provided
    win_index_array = np.where(fcr_after_array > 50)[0]

    # wow, python 2.7 and floor division...
    first_candidate_percentage = (len(win_index_array) / float(N)) * 100
    second_candidate_percentage = 100 - first_candidate_percentage

    print('{} won {}%, and {} won {}% using bootstrap resampling of {} simulations.'.format(
        first_candidate, first_candidate_percentage, second_candidate,
        second_candidate_percentage, N))

if __name__ == '__main__':
    errors = all_error_data()
