from collections import OrderedDict
import sys
import tinycss2


def serialize_declaration(decl):
    """Turn a declaration back into CSS."""
    value = tinycss2.serialize(decl.value).strip()

    if decl.important:
        return f"    {decl.name}: {value} !important;"

    return f"    {decl.name}: {value};"


def main(filename):

    with open(filename, "r", encoding="utf-8") as f:
        css = f.read()

    rules = tinycss2.parse_stylesheet(
        css,
        skip_comments=False,
        skip_whitespace=False
    )

    selector_map = OrderedDict()
    output = []

    duplicate_count = 0

    for rule in rules:

        # Preserve comments and whitespace exactly where possible
        if rule.type != "qualified-rule":
            output.append(rule)
            continue

        selector = tinycss2.serialize(rule.prelude).strip()

        declarations = tinycss2.parse_declaration_list(
            rule.content,
            skip_comments=False,
            skip_whitespace=False
        )

        if selector not in selector_map:
            selector_map[selector] = declarations
        else:
            duplicate_count += 1

            # Preserve declaration order by appending
            selector_map[selector].extend(declarations)

    print()
    print("======================================")
    print(" CSS Doctor")
    print("======================================")
    print(f"Duplicate selector blocks: {duplicate_count}")
    print(f"Unique selectors:          {len(selector_map)}")
    print()

    outname = filename.replace(".css", ".cleaned.css")

    with open(outname, "w", encoding="utf-8") as out:

        out.write("/*\n")
        out.write(" * CSS Doctor\n")
        out.write(" * Duplicate selectors consolidated.\n")
        out.write(" * Original file preserved.\n")
        out.write(" */\n\n")

        for selector, declarations in selector_map.items():

            out.write(selector)
            out.write(" {\n")

            for decl in declarations:

                if decl.type == "declaration":
                    out.write(serialize_declaration(decl))
                    out.write("\n")

            out.write("}\n\n")

    print(f"Wrote {outname}")


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage:")
        print("    python cssdoctor.py css/characters.css")
        sys.exit(1)

    main(sys.argv[1])