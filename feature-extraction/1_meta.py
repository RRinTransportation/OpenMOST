#!/usr/bin/env python
"""
Extract metadata and structural information from an Elsevier full‑text XML,
including:
  • title and journal name
  • paper DOI
  • year, month
  • abstract
  • article type and subtype
  • detailed author information (name, institution, region, corresponding status)
  • primary institution and region
  • keywords from the specified <ce:keywords> tag
  • number of unique institutes
  • whether the article is Open Access
  • section and subsection headings
  • counts of figures, tables, references, and pages
  • figure and table captions
  • submission history dates (received / revised / accepted)
  • publication timeline dates (orig‑load, available‑online, VOR load/online)
  • funding agencies
  • hyperlinks within the text
  • data and code availability statements
  • data availability statement from <ce:data-availability>
  • acknowledgement text
"""

import argparse
from pathlib import Path
from lxml import etree
import json
import sys
import re
from typing import List, Dict, Set, Optional

# --- namespaces ----------------------------------------------------------
# Define the XML namespaces used in Elsevier documents for easier XPath queries.
NS = {
    "sv": "http://www.elsevier.com/xml/svapi/article/dtd",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ce": "http://www.elsevier.com/xml/common/dtd",
    "sa": "http://www.elsevier.com/xml/common/struct-aff/dtd",
    "xocs": "http://www.elsevier.com/xml/xocs/dtd",
    "prism": "http://prismstandard.org/namespaces/basic/2.0/",
    "xlink": "http://www.w3.org/1999/xlink",
}

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def _find_first_text(root: etree._Element, xpaths: List[str]) -> str:
    """Try a list of XPaths and return the text content of the first match."""
    for path in xpaths:
        # Use the defined namespaces in the search
        result = root.findtext(path, namespaces=NS)
        if result and result.strip():
            return result.strip()
    return ""


def _collect_dates(root: etree._Element) -> Dict[str, str]:
    """Return dict with received / revised / accepted dates as `YYYY‑MM‑DD`."""
    dates: Dict[str, str] = {}
    for label in ("received", "revised", "accepted"):
        # Elsevier XML has several ways to tag dates; we check them in order.
        history_date_paths = [
            f".//ce:date-{label}",
            f".//ce:date[@date-type='{label}']",
            f".//ce:date[@type='{label}']",
        ]
        for path in history_date_paths:
            el = root.find(path, NS)
            if el is None:
                continue

            iso = el.get("iso-8601-date")
            if iso:
                dates[label] = iso.strip()
                break  # Found the date, move to the next label

            day = el.get("day")
            month = el.get("month")
            year = el.get("year")
            if day and month and year:
                dates[label] = f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"
                break  # Found the date, move to the next label

            # Fallback to element text if attributes are missing
            text_date = " ".join(" ".join(t.split()) for t in el.itertext()).strip()
            if text_date:
                dates[label] = text_date
                break # Found the date, move to the next label
    return dates


def _collect_pub_dates(root: etree._Element) -> Dict[str, str]:
    """Return dict with important load / availability dates (ISO‑8601)."""
    pub_dates: Dict[str, str] = {}
    mapping = {
        "orig-load-date": "orig_load",
        "available-online-date": "available_online",
        "vor-load-date": "vor_load",
        "vor-available-online-date": "vor_available_online",
    }
    for tag, key in mapping.items():
        el = root.find(f".//xocs:{tag}", NS)
        if el is None:
            continue
        text_iso = (el.text or "").strip()
        if text_iso:
            pub_dates[key] = text_iso
        else:
            # Fallback for older formats
            ymd = el.get("yyyymmdd", "")
            if len(ymd) == 8 and ymd.isdigit():
                pub_dates[key] = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
    return pub_dates


def _is_open_access(root: etree._Element) -> bool:
    """Return True if any recognised marker indicates Open Access."""
    TRUTHY = {"y", "yes", "true", "1"}
    # Check specific, reliable XPath locations first.
    direct_paths = [
        ".//xocs:open-access",
        ".//sv:coredata/sv:openaccess",
        ".//sv:coredata/prism:openaccess",
    ]
    for path in direct_paths:
        el_text = root.findtext(path, default="", namespaces=NS).strip().lower()
        if el_text in TRUTHY:
            return True
            
    # As a fallback, iterate through elements with a relevant tag name.
    # This is less precise but can catch non-standard implementations.
    for el in root.iter():
        ln = el.tag.split("}")[-1].lower()
        if ln in {"openaccess", "open-access"}:
            if (el.text or "").strip().lower() in TRUTHY:
                return True
            if any(v.strip().lower() in TRUTHY for v in el.attrib.values()):
                return True
    return False


def _collect_funding_agencies(root: etree._Element) -> List[str]:
    """Return a list of unique funding agency names."""
    agencies: Set[str] = set()
    # Define various tags under which funding info can be found.
    funding_paths = [
        ".//xocs:funding-agency",
        ".//ce:funding-source",
        ".//ce:sponsor",
    ]
    for path in funding_paths:
        for el in root.findall(path, NS):
            text = (el.text or "").strip()
            if text:
                agencies.add(text)
    return sorted(list(agencies))


def _collect_links(root: etree._Element) -> List[str]:
    """Return a list of unique hyperlinks found in the document."""
    links: Set[str] = set()
    # Find all elements with an xlink:href attribute. Common tags are ce:link and ce:inter-ref.
    link_elements = root.xpath("//*[@xlink:href]", namespaces=NS)
    for el in link_elements:
        href = el.get(f"{{{NS['xlink']}}}href")
        if href:
            links.add(href.strip())
    return sorted(list(links))


def _collect_availability(root: etree._Element) -> Dict[str, list]:
    """Find and extract data and code availability statements."""
    availability = {"data": [], "code": []}
    
    # Keywords to identify data and code availability sections
    data_keywords = ["data available", "data availability", "zenodo", "figshare", "dryad"]
    code_keywords = ["code available", "code availability", "github", "gitlab"]

    # Search in common text-containing elements like paragraphs and list items
    for el in root.xpath('//ce:para | //ce:note-para | //ce:list-item/ce:para', namespaces=NS):
        text = "".join(el.itertext()).lower().strip()
        if not text:
            continue

        full_text = " ".join("".join(el.itertext()).split())

        # Check for data availability
        if any(keyword in text for keyword in data_keywords):
            if full_text not in availability["data"]:
                availability["data"].append(full_text)

        # Check for code availability
        if any(keyword in text for keyword in code_keywords):
            if full_text not in availability["code"]:
                availability["code"].append(full_text)

    return availability


def _collect_data_availability_statement(root: etree._Element) -> str:
    """Finds and extracts the data availability statement."""
    # Find the specific data-availability element by its ID.
    data_availability_element = root.find('.//ce:data-availability[@id="da005"]', NS)
    if data_availability_element is None:
        return ""
    
    # Extract all paragraph text within this element and join it.
    para_elements = data_availability_element.findall('.//ce:para', NS)
    if not para_elements:
        # Fallback to the text of the element if no paragraphs are found
        return " ".join("".join(data_availability_element.itertext()).split())

    full_text = " ".join(["".join(p.itertext()).strip() for p in para_elements])
    
    # Normalize whitespace and return
    return " ".join(full_text.split())


def _collect_acknowledgement(root: etree._Element) -> str:
    """Finds and extracts the acknowledgement text."""
    ack_element = root.find('.//ce:acknowledgment', NS)
    if ack_element is None:
        return ""
    
    # Find all paragraph elements within the acknowledgment section.
    para_elements = ack_element.findall('.//ce:para', NS)
    
    if not para_elements:
        # Fallback if no paragraphs are inside the acknowledgement
        return " ".join("".join(ack_element.itertext()).split())

    # Combine the text from all paragraphs.
    full_ack_text = " ".join(["".join(p.itertext()).strip() for p in para_elements])
    
    # Normalize whitespace
    return " ".join(full_ack_text.split())


def _collect_abstract(root: etree._Element) -> str:
    """Finds and extracts the main text abstract, ignoring graphical abstracts."""
    # Find all abstract elements and iterate to find the non-graphical one.
    abstract_elements = root.findall('.//ce:abstract', NS)
    target_abstract_element = None
    for el in abstract_elements:
        if el.get('class') != 'graphical':
            target_abstract_element = el
            break  # Use the first non-graphical abstract found

    # If no non-graphical abstract is found, fall back to dc:description or return empty.
    if target_abstract_element is None:
        return _find_first_text(root, [".//sv:coredata/dc:description"])

    # Find all paragraph elements (ce:para or ce:simple-para) within the abstract.
    para_elements = target_abstract_element.xpath('.//ce:para | .//ce:simple-para', namespaces=NS)
    
    if not para_elements:
        # If no paragraphs are found, extract all text from the abstract element.
        # This handles abstracts that don't use paragraph tags.
        text_content = "".join(target_abstract_element.itertext())
        # Clean up text from nested section titles like "Abstract"
        title_el = target_abstract_element.find('.//ce:section-title', NS)
        if title_el is not None and title_el.text:
            text_content = text_content.replace(title_el.text, "", 1)
        return " ".join(text_content.split())

    # Combine the text from all found paragraphs.
    full_abstract_text = " ".join(["".join(p.itertext()).strip() for p in para_elements])
    
    # Normalize whitespace.
    return " ".join(full_abstract_text.split())

def _collect_structured_sections(root: etree._Element, parent_xpath: str) -> List[Dict]:
    """
    Collects sections and their nested subsections from a given parent path.
    This function processes XML structures where sections can contain other sections.
    """
    parent_el = root.find(parent_xpath, NS)
    if parent_el is None:
        return []

    def _process_section_recursively(section_element: etree._Element) -> Dict:
        """
        Recursively processes a section element to extract its title and any nested subsections.

        Args:
            section_element: The lxml element for the current section.

        Returns:
            A dictionary representing the section's structure.
        """
        # Extract the title of the current section.
        title_el = section_element.find("ce:section-title", NS)
        title = "".join(title_el.itertext()).strip() if title_el is not None else ""
        
        subsections = []
        # Find direct child sections (subsections) and recurse into them.
        for sub_section_element in section_element.findall("ce:section", NS):
            subsections.append(_process_section_recursively(sub_section_element))
        
        result = {"section": title}
        if subsections:
            result["subsections"] = subsections
        return result

    # Start the recursive processing from the top-level sections within the parent element.
    top_level_sections = []
    for sec_el in parent_el.findall("ce:section", NS):
        top_level_sections.append(_process_section_recursively(sec_el))
    
    return top_level_sections

def _collect_figure_info(root: etree._Element) -> Dict:
    """Finds all figures, extracts their captions, and returns a count and a list of captions."""
    figures_info = {
        "count": 0,
        "captions": []
    }
    figure_elements = root.findall(".//ce:figure", NS)
    figures_info["count"] = len(figure_elements)
    
    for fig in figure_elements:
        caption_el = fig.find(".//ce:caption", NS)
        if caption_el is not None:
            # Extract all text from the caption element, normalize whitespace, and append.
            caption_text = " ".join("".join(caption_el.itertext()).split())
            figures_info["captions"].append(caption_text if caption_text else "")
        else:
             # Add a placeholder if a caption is not found for a figure
             figures_info["captions"].append("")

    return figures_info

def _collect_table_info(root: etree._Element) -> Dict:
    """Finds all tables, extracts their captions, and returns a count and a list of captions."""
    tables_info = {
        "count": 0,
        "captions": []
    }
    table_elements = root.findall(".//ce:table", NS)
    tables_info["count"] = len(table_elements)
    
    for tbl in table_elements:
        caption_el = tbl.find(".//ce:caption", NS)
        if caption_el is not None:
            # Extract all text from the caption element, normalize whitespace, and append.
            caption_text = " ".join("".join(caption_el.itertext()).split())
            tables_info["captions"].append(caption_text if caption_text else "")
        else:
            # Add a placeholder if a caption is not found for a table
            tables_info["captions"].append("")

    return tables_info

# -------------------------------------------------------------------------
# Main extractor
# -------------------------------------------------------------------------

def extract_meta_and_sections(xml_path: Path) -> dict:
    """
    Parses an Elsevier XML file and extracts key metadata and structural info.

    Args:
        xml_path: Path object pointing to the XML file.

    Returns:
        A dictionary containing the extracted information.
    """
    with xml_path.open("rb") as f:
        root = etree.parse(f).getroot()

    # 1. Title, Journal & DOI ----------------------------------------------
    title = _find_first_text(root, [
        ".//sv:coredata/dc:title",
        ".//ce:title",
    ])
    journal = _find_first_text(root, [
        ".//sv:coredata/prism:publicationName",
        ".//prism:publicationName",
        ".//sv:coredata/sv:journal/sv:journal-name",
        ".//prism:journalTitle",
    ])
    doi = _find_first_text(root, [
        ".//sv:coredata/prism:doi",
        ".//xocs:doi",
        ".//ce:doi",
    ])

    # 2. Year, Month, Issue ------------------------------------------------
    # Start with empty values
    year, month, issue = "", "", ""
    
    # Try to get the full publication date first
    cover_date = _find_first_text(root, [".//prism:coverDate"])
    if cover_date and re.match(r"\d{4}-\d{2}-\d{2}", cover_date):
        year = cover_date[:4]
        month = cover_date[5:7]

    # If the year is still missing, try other common tags
    if not year:
        year = _find_first_text(root, [".//xocs:copyright-year"])

    # Find the issue number from several possible tags
    issue = _find_first_text(root, [
        ".//prism:issueIdentifier",
        ".//xocs:issue-num",
        ".//ce:issue"
    ])

    # 3. Article type & Abstract -------------------------------------------
    article_type = _find_first_text(root, [".//xocs:document-type"])
    article_subtype = _find_first_text(root, [".//xocs:document-subtype"])
    abstract = _collect_abstract(root)


    # 4. Keywords ----------------------------------------------------------
    # This XPath specifically targets keywords within the element with id='kg005' and class='keyword'.
    keyword_xpath = ".//ce:keywords[@class='keyword']/ce:keyword/ce:text"
    kws = [kw.text.strip() for kw in root.findall(keyword_xpath, NS) if kw.text]

    # 5. Affiliation map ---------------------------------------------------
    aff_map: Dict[str, Dict] = {}
    for aff in root.findall(".//ce:affiliation", NS):
        aid = aff.get("id")
        if not aid:
            continue
        
        orgs = [o.text.strip() for o in aff.findall(".//sa:organization", NS) if o.text and o.text.strip()]
        country = _find_first_text(aff, [".//sa:country"])
        address_parts = [
            _find_first_text(aff, [".//sa:address-line"]),
            _find_first_text(aff, [".//sa:city"]),
            _find_first_text(aff, [".//sa:state"]),
            _find_first_text(aff, [".//sa:postal-code"])
        ]
        address = ", ".join(part for part in address_parts if part)

        # Fallback to ce:textfn if structured info is missing
        if not address and not orgs:
            textfn = _find_first_text(aff, [".//ce:textfn"])
            if textfn:
                address = textfn
                orgs = [textfn] # Use the full text as the organization as a fallback

        aff_map[aid] = {"orgs": orgs, "country": country, "address": address}

    # 6. Correspondence IDs -----------------------------------------------
    corr_ids = {c.get("id") for c in root.findall(".//ce:correspondence", NS)}

    # 7. Authors & institutes ---------------------------------------------
    all_authors: List[Dict] = []
    institute_set: Set[str] = set()
    primary_institution: str = ""
    primary_region: str = ""

    # Use an XPath that excludes authors from editor groups.
    for au in root.xpath("//ce:author-group[not(ancestor::xocs:title-editors-group)]/ce:author", namespaces=NS):
        given = au.findtext("ce:given-name", default="", namespaces=NS).strip()
        surname = au.findtext("ce:surname", default="", namespaces=NS).strip()
        name = f"{given} {surname}".strip()

        is_corr = any(cr.get("refid") in corr_ids for cr in au.findall("ce:cross-ref", NS))

        institutions = []
        countries = []
        addresses = []
        
        # Get all affiliation IDs for the author
        ref_ids = [cr.get("refid") for cr in au.findall("ce:cross-ref", NS) if cr.get("refid", "").startswith("af")]
        
        # If no explicit affiliation ref is found, check for an implicit one.
        # This is common when all authors share a single affiliation.
        if not ref_ids and len(aff_map) == 1:
            ref_ids.append(list(aff_map.keys())[0])

        for ref_id in ref_ids:
            aff = aff_map.get(ref_id)
            if aff:
                orgs = aff.get("orgs", [])
                if orgs:
                    # Join multiple organization tags for a complete institution name.
                    full_institution_name = ", ".join(orgs)
                    if full_institution_name not in institutions:
                        institutions.append(full_institution_name)
                    institute_set.add(full_institution_name)
                
                country = aff.get("country", "")
                if country and country not in countries:
                    countries.append(country)

                address = aff.get("address", "")
                if address and address not in addresses:
                    addresses.append(address)
        
        # Set primary info from the first author that has it
        if not primary_institution and institutions:
            primary_institution = institutions[0]
        if not primary_region and countries:
            primary_region = countries[0]

        author_info = {
            "name": name,
            "institution": "; ".join(institutions),
            "address": "; ".join(addresses),
            "regoin": "; ".join(countries),
            "is_corresponding_author": is_corr
        }
        all_authors.append(author_info)


    # 8. Sections & Appendices with Subsections --------------------------
    sections = _collect_structured_sections(root, ".//ce:sections")
    appendices = _collect_structured_sections(root, ".//ce:appendices")

    # 9. Counts & misc -----------------------------------------------------
    figure_info = _collect_figure_info(root)
    table_info = _collect_table_info(root)
    ref_count = len(root.findall(".//ce:bib-reference", NS))
    
    # Page count calculation: Prioritize direct page count, fallback to calculation.
    page_count_str = _find_first_text(root, [".//xocs:web-pdf-page-count"])
    page_count = 0
    if page_count_str.isdigit():
        page_count = int(page_count_str)
    else:
        first_page_str = _find_first_text(root, [".//xocs:first-fp"])
        last_page_str = _find_first_text(root, [".//xocs:last-lp"])
        if first_page_str.isdigit() and last_page_str.isdigit():
            try:
                first_page = int(first_page_str)
                last_page = int(last_page_str)
                if last_page >= first_page:
                    page_count = last_page - first_page + 1
            except (ValueError, TypeError):
                page_count = 0 

    # 10. Dates, OA, funding, and Links ------------------------------------
    submission_history = _collect_dates(root)
    publication_dates = _collect_pub_dates(root)
    open_access = _is_open_access(root)
    funding_agencies = _collect_funding_agencies(root)
    links = _collect_links(root)
    availability = _collect_availability(root)
    data_availability_statement = _collect_data_availability_statement(root)
    acknowledgement = _collect_acknowledgement(root)

    # ---------------------------------------------------------------------
    return {
        "title": title,
        "journal": journal,
        "doi": doi,
        "year": year,
        "month": month,
        "issue": issue,
        "abstract": abstract,
        "article_type": article_type,
        "article_subtype": article_subtype,
        "authors": all_authors,
        "primary_institution": primary_institution,
        "primary_region": primary_region,
        "keywords": kws,
        "institute_count": len(institute_set),
        "open_access": open_access,
        "sections": sections,
        "appendices": appendices,
        "links": links,
        "availability": availability,
        "data_availability_statement": data_availability_statement,
        "acknowledgement": acknowledgement,
        "figure_count": figure_info["count"],
        "figure_captions": figure_info["captions"],
        "table_count": table_info["count"],
        "table_captions": table_info["captions"],
        "reference_count": ref_count,
        "page_count": page_count,
        "submission_history": submission_history,
        "publication_dates": publication_dates,
        "funding_agencies": funding_agencies,
    }


def main():
    """
    Main function to parse all XML files in a directory and save the
    extracted metadata to a corresponding JSON file in another directory.
    Usage:
        python meta.py --input_dir 'data' --output_dir 'meta'
        python meta.py --input_dir 'mvd' --output_dir 'mvd-meta'
    """
    parser = argparse.ArgumentParser(
        description="Extract metadata from all Elsevier XML files in a directory.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input_dir",
        type=Path,
        default=Path("../data"),
        help="Directory containing the Elsevier XML files.",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("../meta"),
        help="Directory to save the output JSON files.",
    )
    args = parser.parse_args()

    # Ensure the output directory exists, creating it if necessary.
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all XML files in the input directory.
    xml_files = list(args.input_dir.glob("*.xml"))
    if not xml_files:
        print(f"Error: No XML files found in '{args.input_dir}'", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(xml_files)} XML files to process.")

    # Process each XML file found.
    for xml_path in xml_files:
        print(f"Processing '{xml_path.name}'...")
        # Define the output path for the JSON file.
        output_path = args.output_dir / xml_path.with_suffix(".json").name

        try:
            # Extract the data using the core function.
            data = extract_meta_and_sections(xml_path)
            
            # Write the extracted data to the corresponding JSON file.
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"  -> Successfully saved metadata to '{output_path}'")

        except etree.XMLSyntaxError as e:
            # Log syntax errors but continue with the next file.
            print(f"Error: XML syntax error in '{xml_path.name}': {e}", file=sys.stderr)
        except Exception as e:
            # Log any other unexpected errors and continue.
            print(f"An unexpected error occurred while processing '{xml_path.name}': {e}", file=sys.stderr)

    print("\nBatch processing complete.")


if __name__ == "__main__":
    main()