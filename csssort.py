from bs4 import BeautifulSoup
from collections import OrderedDict
import tinycss2
import pathlib
import re
import sys


##########################################################
# HTML
##########################################################

def extract_dom_order(html_file):
    with open(html_file, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    order = []

    for tag in soup.find_all(True):

        if tag.get("id"):
            selector = "#" + tag["id"]
            if selector not in order:
                order.append(selector)

        for cls in tag.get("class", []):
            selector = "." + cls
            if selector not in order:
                order.append(selector)

    return order


##########################################################
# CSS
##########################################################

def extract_simple_selectors(selector_text):
    """
    Return simple selectors from a selector string.

    '#header:hover, .panel.active'
        ->
    ['#header', '.panel']
    """

    found = []

    for part in selector_text.split(","):

        part = part.strip()

        matches = re.findall(r"[#.][A-Za-z0-9_-]+", part)

        for m in matches:
            if m not in found:
                found.append(m)

    return found


##########################################################
# Main
##########################################################

def main(html_file, css_file):

    dom_order = extract_dom_order(html_file)

    with open(css_file, encoding="utf-8") as f:
        css = f.read()

    rules = tinycss2.parse_stylesheet(
        css,
        skip_comments=False,
        skip_whitespace=False
    )

    ordered = OrderedDict()
    leftovers = []

    for rule in rules:

        if rule.type != "qualified-rule":
            leftovers.append(rule)
            continue

        selector = tinycss2.serialize(rule.prelude).strip()

        simples = extract_simple_selectors(selector)

        matched = False

        for s in simples:

            if s in dom_order:

                ordered.setdefault(s, [])
                ordered[s].append(rule)

                matched = True
                break

        if not matched:
            leftovers.append(rule)

    outname = pathlib.Path(css_file).with_suffix(".sorted.css")

    with open(outname, "w", encoding="utf-8") as out:

        out.write("/* CSS sorted by DOM order */\n\n")

        used = set()

        for selector in dom_order:

            if selector not in ordered:
                continue

            out.write("\n")
            out.write("/* ")
            out.write(selector)
            out.write(" */\n\n")

            used.add(selector)

            for rule in ordered[selector]:
                out.write(tinycss2.serialize([rule]))
                out.write("\n\n")

        out.write("\n")
        out.write("/* ======================================= */\n")
        out.write("/* Remaining rules                         */\n")
        out.write("/* ======================================= */\n\n")

        for rule in leftovers:
            out.write(tinycss2.serialize([rule]))
            out.write("\n")

    ##########################################################
    # Report
    ##########################################################

    print()
    print("==========================================")
    print("CSS Sort Report")
    print("==========================================")

    print()
    print(f"DOM selectors found : {len(dom_order)}")
    print(f"Matched selectors   : {len(used)}")
    print(f"Unused CSS rules    : {len(leftovers)}")

    print()

    if leftovers:
        print("Selectors not matched to HTML:")

        for rule in leftovers:

            if rule.type != "qualified-rule":
                continue

            print("   ",
                  tinycss2.serialize(rule.prelude).strip())

    print()
    print("Wrote", outname)


##########################################################

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print()
        print("Usage:")
        print("    python csssort.py character.html css/pod.css")
        print()
        sys.exit()

    main(sys.argv[1], sys.argv[2])