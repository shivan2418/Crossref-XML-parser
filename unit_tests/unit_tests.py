from crossref_xml_parser import validate_xml

# ensure that validate xml works correctly
assert validate_xml('correct_xml.xml') is True
assert validate_xml('wrong_xml.xml') is False
