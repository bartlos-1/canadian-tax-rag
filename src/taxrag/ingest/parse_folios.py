"""Parse CRA Income Tax Folio HTML (data/raw/folios/**.html).

TODO:
  - Pull the main content out of the page (canada.ca puts it in <main>). Drop the nav/footer.
  - Folios use numbered paragraphs (1.1, 1.2, ...) under headings. Make each paragraph,
    or each heading section, a unit with id like 'S1-F2-C2 ¶2.14'.
  - Extract the folio's citations to the Act ("paragraph 118.5(1)(a)") into the xrefs table.
    Then a folio hit can pull in the statute text and a statute hit can pull in the folio.
"""
