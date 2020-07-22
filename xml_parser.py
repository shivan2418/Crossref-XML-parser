import requests
from bs4 import BeautifulSoup

from collections import OrderedDict
import time

from constants import JOURNAL_TITLE,ABBREV_TITLE,ISSN,EMAIL,DEPOSITOR_NAME,DOI_PREFIX
from constants import DOI_DEPOSIT_URL,DOI_BATCH_START,DOI_BATCH_END,VALIDATE_XML_URL

# Internal methods
def _parse_contributors(authors, fill_empty_with_placeholders=False):
    '''Parses a an a list of authors, the first author is gets the status of first, subsequent ones get "additional"
    If fill_empty_with_placeholders is True it a placeholder author will be filled in if an empty list of authors is passed'''

    contributors = []
    first_author_taken = False

    for author in authors:
        d = OrderedDict([('person_name', OrderedDict([("@sequence", 'first' if not first_author_taken else 'additional'),
                                                      ("@contributor_role", "author"),
                                                      ("given_name", author['firstname']),
                                                      ("surname", author['lastname'])]))])
        first_author_taken = True
        contributors.append(d)

    if len(contributors) == 0 and fill_empty_with_placeholders:
        contributors.append(OrderedDict([('person_name', OrderedDict([("@sequence", 'first'),("@contributor_role", "author"),("given_name", "Placeholder"), ("surname", 'Author')]))]))

    return contributors

def _wrap_in_key(key, content):
    '''Returns <key>content</key>'''
    if len(key.split(' ')) == 1:
        return '<{}>{}</{}>'.format((key), (content), (key))
    else:
        return '<{}>{}</{}>'.format((key), (content), (key.split(" ")[0]))

def _parse_single_xml(d):
    '''Recursively parses a nested dictionary and returns XML'''
    xml = ''
    for key, value in d.items():
        if isinstance(value,dict):
            meta_tags = [key for key in value.keys() if key[0] == '@']
            if len(meta_tags)>0:
                tags = []
                for tag in meta_tags:
                    tags.append('{}="{}"'.format((tag.replace("@","")), (value[tag])))
                key = '{} {}'.format((key), (" ".join(tags)))

            # make a copy of the values
            remaining_values = value.copy()
            # remove the metatags
            for tag in meta_tags:
                del remaining_values[tag]

            xml = "".join([xml, _wrap_in_key(key, _parse_single_xml(remaining_values))])
        elif isinstance(value,list):
            xml = "".join([xml, _wrap_in_key(key, " ".join([_parse_single_xml(item) for item in value]))])
        else:
            xml = "".join([xml, _wrap_in_key(key, value)])

    return xml

def _parse_dict_to_xml(d):
    '''Converts a nested dict to valid XMl format. Wraps the dict in the required DOI_Batch header.
    Dict must be of format {"head":head,
                            "body:body}
    '''

    xml = ''
    # iterate over the dicts and parse it into XML.
    for key, value in d.items():
        if isinstance(value,dict):
            xml = "".join([xml, _wrap_in_key(key, _parse_single_xml(value))])
        else:
            xml = "".join([xml, _wrap_in_key(key, value)])

    xml = "".join([DOI_BATCH_START, xml, DOI_BATCH_END])
    return xml

def _prepare_data_for_xml_parsing(year, journal_volume, issue_number, title, first_page, last_page, article_doi,media_type='print',publication_type='full_text',contributors=None, doi_batch_id=None, language='en'):
    '''Takes the args and combines them into a dictionary structure that can be read by the XML parser'''

    # meta info
    if doi_batch_id is None:
        doi_batch_id = '{}'.format(str(time.time()).split('.')[0])
    if contributors is None:
        contributors = []

    # article info



    article_publication_date = year

    head = OrderedDict([('doi_batch_id',doi_batch_id),
                        ('timestamp',str(time.time()).split('.')[0]),
                        ('depositor',OrderedDict([('depositor_name',DEPOSITOR_NAME),('email_address', EMAIL)])),
                        ('registrant','Crossref')])

    body = OrderedDict([('journal',OrderedDict([
         ('journal_metadata',OrderedDict([('@language',language),('full_title',JOURNAL_TITLE),('abbrev_title',ABBREV_TITLE),('issn',ISSN)]) ),
         ('journal_issue',OrderedDict(  [('publication_date',{'year':year}),('journal_volume',{'volume':journal_volume}),('issue',issue_number)])),
         ('journal_article',OrderedDict(
                                        [('@publication_type',publication_type),
                                         ('titles',{'title':title.replace("&", "&amp;")}), # convert ampersand since "&" breaks xml
                                         ('contributors',_parse_contributors(contributors)),
                                         ('publication_date',OrderedDict([('@media_type',media_type),('year',article_publication_date)])),
                                         ('pages',OrderedDict([('first_page',first_page),('last_page',last_page)]) ),
                                         ('doi_data',article_doi)]) )
         ]))])


    return  OrderedDict([('head',head),
                         ('body',body)])

# Main Methods

def generate_crossref_xml(year, journal_volume, issue_number, title, first_page, last_page, article_doi,contributors=None, doi_batch_id=None, language='en',output_file_name='temporary.xml'):
    '''Creates a crossref valid XML based on the args on passed to this function. Writes to a file by name of output_file_name, defaults to "temporary.xml"'''
    # check that constants have been updated from their default value
    if any([DOI_PREFIX == '99.9999',
            JOURNAL_TITLE == 'Academic Journal',
            ABBREV_TITLE == "QQ",
            ISSN == "01234567",
            DEPOSITOR_NAME == 'John Doe',
            EMAIL == 'email@example.com']):

        print("One or more values are still set to their default values. The parser will produce correctly formatted XML but "
              "your submission will be rejected by crossref. Update constants in constants.py")

    parseable_dict = _prepare_data_for_xml_parsing(year, journal_volume, issue_number, title, first_page, last_page, article_doi,contributors, doi_batch_id=None, language='en')
    xml = _parse_dict_to_xml(parseable_dict)

    with open(output_file_name,'w') as f:
        f.write(xml)

def validate_xml(filePath, headers=None):
    '''Sends the file located at filePath to the Crossref XML parser. Returns True/False to indicate if the XML is valid'''
    if headers is None:
        headers = {"User-Agent": "Mozilla/4.0", "Host": "Myhost", "enctype": "multipart/form-data"}

    file = open(filePath, 'r')
    files = {'file': file}
    resp = requests.post(url=VALIDATE_XML_URL, headers=headers, files=files)
    soup = BeautifulSoup(resp.text,features='html.parser')
    feedback = soup.select_one('#mainContent2 td')
    xml_valid = "[Fatal Error]" not in feedback.text

    return xml_valid

def submit_doi_by_http(login,password,xml_file_path='temporary.xml',headers=None):
    '''Submits the file at xml_file_path to the DOI registration endpoint'''

    data = {'login_id': login,
            'login_passwd': password,
            'operation': 'doMDUpload',
            }
    if headers is None:
        headers = {"User-Agent": "Mozilla/4.0", "Host": "Myhost", "enctype": "multipart/form-data"}

    file = open(xml_file_path, 'r')
    files = {'file': file}

    resp = requests.post(url=DOI_DEPOSIT_URL, data=data, headers=headers, files=files)
    return resp
