from .html2slate import text_to_slate


def test_one():
    html = """<p>Please find below the recordings and presentations
    of<span>&nbsp;</span><strong>past webinars</strong>. Please find information
    on<span>&nbsp;</span><strong>upcoming webinars<span> <span class="link-external"><a
    href="https://climate-adapt.eea.europa.eu/cca-events" data-linktype="external"
    data-val="https://climate-adapt.eea.europa.eu/cca-events"
    target="_blank">here</a></span></span></strong></p>"""

    slate = text_to_slate(html)
    pass


def run():
    test_one()
    return
