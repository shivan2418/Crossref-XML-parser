'''Very primitive unit-tests. '''

from ..xml_parser import validate_xml,generate_crossref_xml

# test validate xml method
assert validate_xml('correct_xml.xml') is True
assert validate_xml('wrong_xml.xml') is False

# test generate_crossref_xml
    # with author
authors = [{"first":'Test','last':'author'}]
generate_crossref_xml('1986', '1', '2', 'Unittest paper title', 12, 24, 123445,contributors=authors,output_file_name='unit_test_xml.xml')
assert validate_xml('unit_test_xml.xml') is True
    # without authors
generate_crossref_xml('1986', '1', '2', 'Unittest paper title', 12, 24, 123445,output_file_name='unit_test_xml.xml')
assert validate_xml('unit_test_xml.xml') is True
