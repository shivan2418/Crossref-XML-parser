from collections import OrderedDict
import time

from .constant import JOURNAL_TITLE,ABBREV_TITLE,ISSN,EMAIL,DEPOSITOR_NAME,DOI_BATCH_STR

def parse_contributors(authors,fill_empty_with_placeholders=False):
    '''Parses a an a list of authors, the first author is gets the status of first, subsequent ones get "additional"
    If fill_empty_with_placeholders is True it a placeholder author will be filled in if an empty list of authors is passed'''

    contributors = []
    first_author_taken = False

    for author in authors:
        d = OrderedDict([('person_name', OrderedDict([("@sequence", 'first' if not first_author_taken else 'additional'),
                                                      ("@contributor_role", "author"),
                                                      ("given_name", author['firstname']),
                                                      ("surname", author['lastname'])]))
                         ])
        first_author_taken = True
        contributors.append(d)

    if len(contributors)==0 and fill_empty_with_placeholders:
        contributors.append(     OrderedDict([('person_name', OrderedDict([("@sequence", 'first'),("@contributor_role", "author"),("given_name", "Placeholder"), ("surname", 'Author')]) )]) )

    return contributors


def wrap_in_key(key,content):
    '''Returns <key>content</key>'''
    if len(key.split(' ')) == 1:
        return '<{}>{}</{}>'.format((key), (content), (key))
    else:
        return '<{}>{}</{}>'.format((key), (content), (key.split(" ")[0]))

def parse_single_xml(d):
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

            xml = "".join([xml,wrap_in_key(key,parse_single_xml(remaining_values))])
        elif isinstance(value,list):
            xml = "".join([xml,wrap_in_key(key," ".join([parse_single_xml(item) for item in value]))])
        else:
            xml = "".join([xml,wrap_in_key(key,value)])

    return xml

def parse_xml(d):
    '''Converts a nested dict to valid XMl format. Wraps the dict in the required DOI_Batch header.
    Dict must be of format {"head":head,
                            "body:body}
    '''

    xml=''
    # iterate over the dicts and parse it into XML.
    for key, value in d.items():
        if isinstance(value,dict):
            xml = "".join([xml,wrap_in_key(key,parse_single_xml(value))])
        else:
            xml = "".join([xml,wrap_in_key(key,value)])

    xml = "".join([DOI_BATCH_STR,xml,"</doi_batch>"])
    return xml

def prepare_data_for_xml_parsing(doi_batch_id,year, journal_volume, issue_number, title, contributors, first_page, last_page,article_doi):
    '''Takes the args and combines them into a dictionary structuce that can be read by the XML parser'''

    # meta info
    doi_batch_id = doi_batch_id
    depositor_name = DEPOSITOR_NAME
    email = EMAIL

    # journal info
    journal_title = JOURNAL_TITLE
    abbrev_title = ABBREV_TITLE
    issn = ISSN

    # issue info
    year = year
    journal_volume = journal_volume
    issue_number = issue_number

    # article info
    title = title
    contributors = contributors
    first_page = first_page
    last_page = last_page
    article_publication_date = year
    article_doi = article_doi

    head = OrderedDict([('doi_batch_id',doi_batch_id),
                        ('timestamp',str(time.time()).split('.')[0]),
                        ('depositor',OrderedDict([('depositor_name',depositor_name),('email_address', email)])),
                        ('registrant','Crossref')])

    body = OrderedDict([('journal',OrderedDict([
         ('journal_metadata',OrderedDict([('@language','en'),('full_title',journal_title),('abbrev_title',abbrev_title),('issn',issn)]) ),
         ('journal_issue',OrderedDict(  [('publication_date',{'year':year}),('journal_volume',{'volume':journal_volume}),('issue',issue_number)])),
         ('journal_article',OrderedDict(
                                        [('@publication_type','full_text'),
                                         ('titles',{'title':title.replace("&", "&amp;")}), # convert ampersand since it breaks xml
                                         ('contributors',contributors),
                                         ('publication_date',OrderedDict([('@media_type','print'),('year',article_publication_date)])),
                                         ('pages',OrderedDict([('first_page',first_page),('last_page',last_page)]) ),
                                         ('doi_data',article_doi)]) )
         ]))])


    return  OrderedDict([('head',head),
                         ('body',body)])


if __name__ == '__main__':
