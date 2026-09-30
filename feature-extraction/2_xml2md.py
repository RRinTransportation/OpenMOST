#!/usr/bin/env python
"""
Converts all Elsevier full-text XML files in an input folder to structured 
Markdown documents in an output folder. It extracts the main textual content, 
including titles, authors, abstract, sections, tables, figures, data availability, 
acknowledgements, and references.
"""

import argparse
from pathlib import Path
from lxml import etree
import sys
from typing import List, Optional, Dict, Set

# --- namespaces ----------------------------------------------------------
# Define the XML namespaces used in Elsevier documents for easier XPath queries.
NS = {
    "ce": "http://www.elsevier.com/xml/common/dtd",
    "ja": "http://www.elsevier.com/xml/ja/dtd",
    "sb": "http://www.elsevier.com/xml/common/struct-bib/dtd",
    "xlink": "http://www.w3.org/1999/xlink",
    "xocs": "http://www.elsevier.com/xml/xocs/dtd",
    "sv": "http://www.elsevier.com/xml/svapi/article/dtd",
    "dc": "http://purl.org/dc/elements/1.1/",
    "prism": "http://prismstandard.org/namespaces/basic/2.0/",
    "sa": "http://www.elsevier.com/xml/common/struct-aff/dtd",
}

# -------------------------------------------------------------------------
# Helper functions for processing XML elements
# -------------------------------------------------------------------------

def get_full_text(element: Optional[etree._Element]) -> str:
    """Recursively get all text from an element and its children."""
    if element is None:
        return ""
    # Use .itertext() to get all text nodes, and join them.
    # ' '.join() and split() are used to normalize whitespace.
    return ' '.join(''.join(element.itertext()).split())

def _find_first_text(root: etree._Element, xpaths: List[str]) -> str:
    """Try a list of XPaths and return the text content of the first match."""
    for path in xpaths:
        # Use the defined namespaces in the search
        result = root.findtext(path, namespaces=NS)
        if result and result.strip():
            return result.strip()
    return ""

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


def process_list(list_element: etree._Element) -> List[str]:
    """Processes a list element and returns its items as Markdown lines."""
    markdown_lines = []
    for item in list_element.findall('.//ce:list-item', NS):
        item_text = get_full_text(item.find('ce:para', NS))
        label = get_full_text(item.find('ce:label', NS))
        # Format as a Markdown list item
        markdown_lines.append(f"* {label} {item_text}".strip())
    if markdown_lines:
        markdown_lines.append("")
    return markdown_lines


def process_section_content(element: etree._Element) -> List[str]:
    """Processes the direct content of a section (paragraphs, lists, etc.)."""
    markdown_lines = []
    for child in element:
        tag = etree.QName(child.tag).localname
        
        if tag == 'para' or tag == 'simple-para':
            markdown_lines.append(get_full_text(child))
            markdown_lines.append("")
        
        elif tag == 'list':
            markdown_lines.extend(process_list(child))
            
    return markdown_lines


def process_section(section_element: etree._Element, level: int, is_appendix: bool = False) -> List[str]:
    """Processes a main section and its nested content, returning a list of Markdown lines."""
    markdown_lines = []
    
    # Process the section title with the appropriate heading level
    title_el = section_element.find('ce:section-title', NS)
    label_el = section_element.find('ce:label', NS)

    title_text = get_full_text(title_el)
    label_text = get_full_text(label_el)

    final_title = ""
    if is_appendix:
        if label_text and title_text:
            # Combine label and title for appendix with subtitle
            final_title = f"{label_text}: {title_text}"
        elif label_text:
            # Use label if no title
            final_title = label_text
        elif title_text and 'appendix' not in title_text.lower():
            # Use title with "Appendix" prefix if no label
            final_title = f"Appendix: {title_text}"
        else:
            final_title = title_text
    else:
        final_title = title_text

    if final_title:
        markdown_lines.append(f"{'#' * level} {final_title}")
        markdown_lines.append("")

    # Process the direct children of the section
    for child in section_element:
        tag = etree.QName(child.tag).localname
        
        if tag in ['para', 'simple-para']:
            markdown_lines.append(get_full_text(child))
            markdown_lines.append("")
        
        elif tag == 'section':
            # Recursively process nested sections, propagating the is_appendix flag
            markdown_lines.extend(process_section(child, level + 1, is_appendix=is_appendix))
            
        elif tag == 'list':
            markdown_lines.extend(process_list(child))

    return markdown_lines


def process_simple_section(root: etree._Element, xpath: str, default_title: str) -> List[str]:
    """
    Finds and processes a simple section like data-availability.
    These sections do not have nested sub-sections but may contain paragraphs and lists.
    """
    markdown_lines = []
    section_element = root.find(xpath, NS)
    if section_element is not None:
        title = get_full_text(section_element.find('ce:section-title', NS)) or default_title
        markdown_lines.append(f"## {title}\n")
        markdown_lines.extend(process_section_content(section_element))
    return markdown_lines


def process_figures(root: etree._Element) -> List[str]:
    """Finds all figures and extracts their labels and captions."""
    markdown_lines = []
    figures = root.findall('.//ce:figure', NS)
    if not figures:
        return []

    markdown_lines.append("## Figures\n")
    for figure in figures:
        label = get_full_text(figure.find('ce:label', NS))
        caption = get_full_text(figure.find('ce:caption', NS))
        if label and caption:
            markdown_lines.append(f"* **{label}:** {caption}")
    markdown_lines.append("")
    return markdown_lines


def process_tables(root: etree._Element) -> List[str]:
    """Finds all tables and extracts their labels and captions."""
    markdown_lines = []
    tables = root.findall('.//ce:table', NS)
    if not tables:
        return []

    markdown_lines.append("## Tables\n")
    for table in tables:
        label = get_full_text(table.find('ce:label', NS))
        caption = get_full_text(table.find('ce:caption', NS))
        if label and caption:
            markdown_lines.append(f"* **{label}:** {caption}")
    markdown_lines.append("")
    return markdown_lines


def convert_xml_to_markdown(xml_path: Path) -> str:
    """
    Main function to convert an Elsevier XML file to a Markdown string.

    Args:
        xml_path: Path object pointing to the XML file.

    Returns:
        A string containing the document in Markdown format.
    """
    with xml_path.open("rb") as f:
        tree = etree.parse(f)
    root = tree.getroot()
    
    markdown_output = []

    # --- Title (Updated with robust extraction) ---
    title = _find_first_text(root, [
        ".//sv:coredata/dc:title",
        ".//ce:title",
    ])
    if title:
        markdown_output.append(f"# {title}\n")

    # --- Start: Detailed Author and Affiliation Processing (Updated Logic) ---

    # 1. Build a map of all affiliations from their IDs
    aff_map: Dict[str, Dict] = {}
    for aff in root.findall(".//ce:affiliation", NS):
        aid = aff.get("id")
        if not aid:
            continue
        
        # Use 'sa:organization' for structured organization names
        orgs = [o.text.strip() for o in aff.findall(".//sa:organization", NS) if o.text and o.text.strip()]
        country = _find_first_text(aff, [".//sa:country"])

        # Fallback to ce:textfn if structured info is missing
        if not orgs:
            textfn = _find_first_text(aff, [".//ce:textfn"])
            if textfn:
                orgs = [textfn]

        aff_map[aid] = {"orgs": orgs, "country": country}

    # 2. Get all cross-reference IDs for corresponding authors
    corr_ids = {c.get("id") for c in root.findall(".//ce:correspondence", NS)}

    # 3. Process each author using the detailed logic
    all_authors: List[Dict] = []
    
    # Use an XPath that excludes authors from editor groups.
    author_elements = root.xpath("//ce:author-group[not(ancestor::xocs:title-editors-group)]/ce:author", namespaces=NS)
    for au in author_elements:
        given = au.findtext("ce:given-name", default="", namespaces=NS).strip()
        surname = au.findtext("ce:surname", default="", namespaces=NS).strip()
        name = f"{given} {surname}".strip()

        # Check if this author is a corresponding author
        is_corr = any(cr.get("refid") in corr_ids for cr in au.findall("ce:cross-ref", NS))

        institutions = []
        
        # Get all affiliation IDs for the author
        ref_ids = [cr.get("refid") for cr in au.findall("ce:cross-ref", NS) if cr.get("refid", "").startswith("af")]
        
        # If no explicit affiliation ref is found, check for an implicit one
        # (common when all authors share a single affiliation).
        if not ref_ids and len(aff_map) == 1:
            ref_ids.append(list(aff_map.keys())[0])

        for ref_id in ref_ids:
            aff = aff_map.get(ref_id)
            if aff:
                orgs = aff.get("orgs", [])
                if orgs:
                    full_institution_name = ", ".join(orgs)
                    if full_institution_name not in institutions:
                        institutions.append(full_institution_name)
        
        author_info = {
            "name": name,
            "institution": "; ".join(institutions),
            "is_corresponding_author": is_corr
        }
        all_authors.append(author_info)

    # 4. Format author information for Markdown output
    if all_authors:
        markdown_output.append("### Authors\n")
        for author in all_authors:
            # Add a marker for corresponding authors
            corr_marker = " (corresponding)" if author["is_corresponding_author"] else ""
            institution_info = f" - _{author['institution']}_" if author["institution"] else ""
            markdown_output.append(f"* **{author['name']}**{corr_marker}{institution_info}")
        markdown_output.append("")

    # --- End: Detailed Author and Affiliation Processing ---

    # --- Abstract ---
    abstract_element = root.find('.//ce:abstract', NS)
    if abstract_element is not None:
        para_elements = abstract_element.findall('.//ce:para', NS) + abstract_element.findall('.//ce:simple-para', NS)
        if para_elements:
            markdown_output.append("## Abstract\n")
            for para in para_elements:
                para_text = get_full_text(para)
                if para_text:
                    markdown_output.append(para_text)
                    markdown_output.append("")

    # --- Body Sections ---
    body = root.find('.//ja:body', NS)
    if body is not None:
        sections_container = body.find('ce:sections', NS)
        if sections_container is not None:
            for section in sections_container.findall('ce:section', NS):
                markdown_output.extend(process_section(section, 2))
    
    # --- Figures ---
    markdown_output.extend(process_figures(root))

    # --- Tables ---
    markdown_output.extend(process_tables(root))

    # --- Acknowledgements ---
    ack_element = root.find('.//ce:acknowledgment', NS)
    if ack_element is not None:
        title = get_full_text(ack_element.find('ce:section-title', NS)) or "Acknowledgements"
        ack_text = _collect_acknowledgement(root)
        if ack_text.startswith(title):
            ack_text = ack_text[len(title):].lstrip()
        
        if not ack_text.startswith("Acknowledgements"):
             markdown_output.append(f"## {title}\n")

        if ack_text:
            markdown_output.append(f"{ack_text}\n")

    # --- Data Availability ---
    markdown_output.extend(process_simple_section(
        root, './/ce:data-availability', "Data Availability"
    ))

    # --- Appendices ---
    appendices = root.find('.//ce:appendices', NS)
    if appendices is not None:
        for appendix in appendices.findall('ce:section', NS):
            markdown_output.extend(process_section(appendix, 2, is_appendix=True))
            
    # --- References ---
    bib = root.find('.//ce:bibliography', NS)
    if bib is not None:
        bib_title = get_full_text(bib.find('ce:section-title', NS)) or "References"
        markdown_output.append(f"## {bib_title}\n")
        for ref in bib.findall('.//ce:bib-reference', NS):
            ref_text = get_full_text(ref.find('.//sb:reference', NS))
            if not ref_text: # Fallback for other reference formats
                ref_text = get_full_text(ref.find('.//ce:other-ref', NS))
            if ref_text:
                markdown_output.append(f"* {ref_text}")
        markdown_output.append("")

    return "\n".join(markdown_output)


def main():
    """Main function to parse arguments and run the converter on a folder."""
    parser = argparse.ArgumentParser(
        description="Convert all Elsevier full-text XML files in a folder to Markdown.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_folder", 
        type=Path, 
        help="Path to the folder containing Elsevier XML files."
    )
    parser.add_argument(
        "-o", "--output_folder",
        type=Path,
        default=Path("markdown_output"),
        help="Output folder for the Markdown files. Defaults to './markdown_output'."
    )
    args = parser.parse_args()

    # Validate that the input path is a directory
    if not args.input_folder.is_dir():
        print(f"Error: Input path '{args.input_folder}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    # Create the output directory; exist_ok=True prevents an error if it already exists
    try:
        args.output_folder.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error: Could not create output directory '{args.output_folder}': {e}", file=sys.stderr)
        sys.exit(1)

    # Find all XML files in the input folder
    xml_files = list(args.input_folder.glob('*.xml'))
    if not xml_files:
        print(f"No XML files found in '{args.input_folder}'.")
        return

    print(f"Found {len(xml_files)} XML file(s). Starting conversion to '{args.output_folder}'...")

    success_count = 0
    error_count = 0

    # Loop through each XML file and convert it
    for xml_path in xml_files:
        print(f"Processing '{xml_path.name}'...", end='', flush=True)
        # Define the output path for the new .md file
        output_filename = xml_path.with_suffix('.md').name
        output_path = args.output_folder / output_filename
        
        try:
            markdown_content = convert_xml_to_markdown(xml_path)
            
            # Write the converted content to the output file
            with open(output_path, 'w', encoding='utf-8') as f_out:
                f_out.write(markdown_content)
            
            print(" Done.")
            success_count += 1

        except etree.XMLSyntaxError as e:
            print(f"\n  -> Error: XML syntax error in '{xml_path.name}': {e}", file=sys.stderr)
            error_count += 1
        except Exception as e:
            print(f"\n  -> An unexpected error occurred while processing '{xml_path.name}': {e}", file=sys.stderr)
            error_count += 1
            
    print(f"\nConversion complete. {success_count} file(s) converted successfully, {error_count} failed.")


if __name__ == "__main__":
    main()