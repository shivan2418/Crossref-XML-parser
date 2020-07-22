## Crossref XML parser

After spending considerable time on figuring out the the Crossref API I decided to share this module so other people can save some time.

#### User guide
  1) Install dependencies
  2) Before you make your first submission change the default values in constants.py.
  3) Import methods from crossref_xml_parser.py as needed.  

#### Methods
This module contains three main methods. 
* `generate_crossref_xml` generates a Crossref compatible XML. Some arguments are optional, but you should fill in as much information as you have. doi_batch is used to label the submission batch and useful to tracking what went wrong. If not filled in defaults to an integer format timestamp.
* `validate_xml`  is just programmatic access at to the [Crossref XML validator](https://www.crossref.org/02publishers/parser.html). Returns True if the words "[Fatal Error]" are not represent in the response text.
* `submit_doi_by_http` Submits an XML to the Crossref DOI registration. Note that the Crossref API will return `status code 200` even if you provide incorrect login credentials or your XML is invalid. You have to read the text of the response to determine if the submission was successful. 
Even if the submission was successful, it tracks only the submission, check your email to determine if the XML was finally accepted to the server.  


#### Limitations
   * Supports only main fields 
   * Does not support annotations
   * Assumes that the user submits for one journal, submitting to an new journal requires a re-edit constants.py
   
#### License
Feel free to fork, share, reuse and improve this module. I hope someone may find it useful.