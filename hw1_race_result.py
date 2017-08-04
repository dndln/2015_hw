import bs4
import requests
import pandas as pd
import re
import ipdb
#
#
# html_doc = """
# <html><head><title>The Dormouse's story</title></head>
# <body>
# <p class="title"><b>The Dormouse's story</b></p>
#
# <p class="story">Once upon a time there were three little sisters; and their names were
# <a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
# <a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
# <a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
# and they lived at the bottom of a well.</p>
#
# <p class="story">...</p>
# """
#
# soup = bs4.BeautifulSoup(html_doc, 'html.parser')
#
# # soup = bs4.BeautifulSoup('<b class="boldest">Extremely bold</b>', 'html.parser')
# # tag = soup.b

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
    norm = df.sum(axis=1)
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
    print(out_dict)
    return out_dict
    ipdb.set_trace()



url = 'http://www.realclearpolitics.com/epolls/2010/governor/ca/california_governor_whitman_vs_brown-1113.html'
# url = 'https://www.realclearpolitics.com/epolls/2010/governor/co/colorado_governor_maes_vs_hickenlooper_vs_tancredo-1677.html'
race_result(url)
