import html
import zipfile
from pathlib import Path


OUT_PATH = Path("E_buy_Project_Documentation.docx")


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def esc(text):
    return html.escape(str(text), quote=False)


def run(text, bold=False, color=None, size=None):
    props = []
    if bold:
        props.append("<w:b/>")
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    if size:
        props.append(f'<w:sz w:val="{size}"/>')
        props.append(f'<w:szCs w:val="{size}"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    return f"<w:r>{rpr}<w:t>{esc(text)}</w:t></w:r>"


def paragraph(text="", style=None, bold=False, color=None, size=None, spacing_after=120):
    ppr = [f'<w:spacing w:after="{spacing_after}"/>']
    if style:
        ppr.insert(0, f'<w:pStyle w:val="{style}"/>')
    return f"<w:p><w:pPr>{''.join(ppr)}</w:pPr>{run(text, bold=bold, color=color, size=size)}</w:p>"


def heading(text, level=1):
    style = f"Heading{level}"
    return paragraph(text, style=style, spacing_after=120)


def bullet(text):
    return (
        '<w:p><w:pPr><w:pStyle w:val="ListParagraph"/>'
        '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
        '<w:spacing w:after="80"/></w:pPr>'
        f"{run(text)}</w:p>"
    )


def numbered(text):
    return (
        '<w:p><w:pPr><w:pStyle w:val="ListParagraph"/>'
        '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr>'
        '<w:spacing w:after="80"/></w:pPr>'
        f"{run(text)}</w:p>"
    )


def table(rows, widths):
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in widths)
    xml = [
        '<w:tbl>',
        '<w:tblPr><w:tblW w:w="9360" w:type="dxa"/>'
        '<w:tblInd w:w="120" w:type="dxa"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="DADCE0"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="DADCE0"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="DADCE0"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="DADCE0"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="DADCE0"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="DADCE0"/>'
        '</w:tblBorders>'
        '<w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/>'
        '<w:start w:w="120" w:type="dxa"/><w:end w:w="120" w:type="dxa"/></w:tblCellMar>'
        '</w:tblPr>',
        f"<w:tblGrid>{grid}</w:tblGrid>",
    ]
    for row_index, row in enumerate(rows):
        xml.append("<w:tr>")
        for cell, width in zip(row, widths):
            fill = '<w:shd w:fill="F2F4F7"/>' if row_index == 0 else ""
            xml.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{fill}</w:tcPr>'
                f'{paragraph(cell, bold=(row_index == 0), spacing_after=0)}</w:tc>'
            )
        xml.append("</w:tr>")
    xml.append("</w:tbl>")
    return "".join(xml)


def sect_pr():
    return (
        "<w:sectPr>"
        '<w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
        'w:header="708" w:footer="708" w:gutter="0"/>'
        "</w:sectPr>"
    )


def styles_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:after="120"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="0B2545"/><w:sz w:val="44"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Subtitle">
    <w:name w:val="Subtitle"/>
    <w:basedOn w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:after="240"/></w:pPr>
    <w:rPr><w:color w:val="555555"/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="320" w:after="160"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="2E74B5"/><w:sz w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="2E74B5"/><w:sz w:val="26"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="160" w:after="80"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="1F4D78"/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="ListParagraph">
    <w:name w:val="List Paragraph"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>
  </w:style>
</w:styles>"""


def numbering_xml():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="1">
    <w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/>
    <w:pPr><w:tabs><w:tab w:val="num" w:pos="720"/></w:tabs><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>
  <w:abstractNum w:abstractNumId="2">
    <w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/>
    <w:pPr><w:tabs><w:tab w:val="num" w:pos="720"/></w:tabs><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>
  </w:abstractNum>
  <w:num w:numId="2"><w:abstractNumId w:val="2"/></w:num>
</w:numbering>"""


def document_xml():
    parts = [
        paragraph("E buy Ecommerce Project Documentation", style="Title", spacing_after=80),
        paragraph("Flask-based buyer and supplier marketplace with cart, checkout, wallet credits, order tracking, and email confirmations.", style="Subtitle"),
        heading("1. Project Overview"),
        paragraph("E buy is a local Flask ecommerce web application that supports two user roles: buyers and suppliers. Buyers can browse products, search the marketplace, add items to a cart, complete checkout using wallet credits, recharge their wallet, view order history, and track orders. Suppliers can register, maintain a listed item with uploaded images, and optionally switch into buyer shopping mode."),
        paragraph("The project is intentionally lightweight. It uses server-rendered Jinja templates, CSS assets, JSON-backed persistence, and a small test suite to validate the core marketplace flows."),
        heading("2. Objectives"),
        bullet("Provide a functional ecommerce prototype for buyer registration, shopping, checkout, and order tracking."),
        bullet("Allow suppliers to list products with multiple images and make those products available to buyers."),
        bullet("Simulate wallet-based payments with buyer credits, platform fees, seller payouts, and recharge support."),
        bullet("Send or queue buyer order confirmation emails when orders are confirmed."),
        bullet("Keep the application simple enough to run locally for demonstration and coursework purposes."),
        heading("3. Technology Stack"),
        table([
            ["Layer", "Technology", "Purpose"],
            ["Backend", "Python Flask", "Routes, sessions, form handling, checkout logic, and rendering"],
            ["Frontend", "HTML, Jinja, CSS", "Server-rendered pages and responsive visual styling"],
            ["Storage", "JSON file", "Primary datastore for users, orders, wallet credits, products, and email outbox"],
            ["Security", "Werkzeug password hashing", "Stores hashed passwords instead of plain text"],
            ["Email", "SMTP via smtplib", "Sends buyer order confirmation emails when SMTP settings exist"],
            ["Testing", "unittest", "Validates registration, login, cart, checkout, tracking, stock, recharge, and email queue flows"],
        ], [1600, 2200, 5560]),
        heading("4. Main Files"),
        table([
            ["File or Folder", "Description"],
            ["app.py", "Main Flask application containing routes, product catalog helpers, checkout logic, tracking snapshots, wallet recharge, and SMTP email support."],
            ["templates/", "Jinja templates for registration, dashboard, cart, checkout, orders, recharge, and supplier product listing."],
            ["static/style.css", "Shared styling for the application UI, marketplace cards, order tracking, forms, and buttons."],
            ["static/products/", "SVG product images and uploaded supplier product images."],
            ["data/ecommerce_data.json", "JSON datastore containing users, orders, platform credits, and queued/sent/failed email records."],
            ["test_app.py", "Automated tests for the core buyer, supplier, checkout, order, search, recharge, and email behaviors."],
        ], [2600, 6760]),
        heading("5. User Roles"),
        heading("Buyer", 2),
        bullet("Registers with full name, username, email, phone, address, and password."),
        bullet("Receives an initial wallet balance of 100000 credits."),
        bullet("Can browse/search products, add items to cart, buy now, confirm orders, recharge wallet, and view order history."),
        bullet("Receives an order confirmation email after checkout when SMTP is configured."),
        heading("Supplier", 2),
        bullet("Registers as a seller account with similar identity fields."),
        bullet("Can list one product with name, description, price, quantity, and at least two uploaded images."),
        bullet("Receives seller credits when buyers purchase supplier-listed items."),
        bullet("Can switch to buyer mode to shop from the marketplace."),
        heading("6. Core Workflows"),
        numbered("A visitor selects buyer or supplier registration from the home portal."),
        numbered("The user registers and logs in using a username and password."),
        numbered("Buyers view the marketplace dashboard, search products, and add products to the cart or use Buy now."),
        numbered("At checkout, the app verifies login state, buyer access, cart contents, and wallet balance."),
        numbered("When the order is confirmed, the app deducts buyer credits, calculates a 10% platform fee, records the order, updates supplier stock if relevant, clears the cart, and sends or queues an email confirmation."),
        numbered("The buyer opens the orders page and expands Track order for each order to view the delivery timeline."),
        heading("7. Key Features"),
        bullet("Password policy requiring uppercase, lowercase, number, symbol, and minimum length."),
        bullet("Keyword-friendly product search with aliases and simple typo coverage for terms like mobile, router, earbuds, TV, chair, shoes, backpack, and speaker."),
        bullet("Wallet recharge flow with positive amount validation."),
        bullet("Order tracking panel per order using a clear Track order option."),
        bullet("Supplier stock reduction after supplier product purchase."),
        bullet("Order email support with queued fallback for local development."),
        heading("8. Data Model Summary"),
        table([
            ["Record", "Important Fields"],
            ["User", "role, full_name, username, email, phone, address, password_hash, credits, created_at, item for suppliers"],
            ["Supplier Item", "name, description, price, quantity, image_path, image_paths"],
            ["Order", "order_number, buyer, items, total, platform_fee, seller_share, expected_delivery, status, created_at"],
            ["Email Outbox", "to, subject, body, order_number, created_at, status, error when sending fails"],
        ], [2200, 7160]),
        heading("9. Email Confirmation Behavior"),
        paragraph("When a buyer confirms an order, the app builds an order confirmation email with buyer details, delivery address, order number, placed date, status, expected delivery, payment details, and item details. If SMTP environment variables are available, it sends the email through the configured mail provider. If SMTP is not configured, it stores the message in email_outbox inside the JSON datastore with status queued."),
        bullet("SMTP_HOST: SMTP server hostname, for example smtp.gmail.com."),
        bullet("SMTP_PORT: SMTP server port, commonly 587 for STARTTLS."),
        bullet("SMTP_USERNAME: sender account login."),
        bullet("SMTP_PASSWORD: provider app password or SMTP key."),
        bullet("SMTP_SENDER: email address shown as the sender."),
        heading("10. Testing Summary"),
        paragraph("The automated test suite validates the most important user journeys and edge cases, including registration, login, supplier listing with uploads, buyer cart behavior, order placement, order tracking text, email queue records, cache headers, product search, supplier stock reduction, invalid login, insufficient credits, recharge validation, supplier buyer mode, and successful recharge."),
        paragraph("Focused validation commands used during development included:"),
        bullet(".venv/bin/python -m unittest test_app.ECommerceAppTests.test_buyer_order_placement_deducts_credits"),
        bullet(".venv/bin/python -m py_compile app.py test_app.py"),
        heading("11. Current Limitations"),
        bullet("The primary datastore is a JSON file, so it is suitable for demos but not concurrent production traffic."),
        bullet("Supplier accounts currently maintain one active listed item rather than a full product catalog."),
        bullet("Order tracking is simulated using generated timeline snapshots rather than real courier data."),
        bullet("Payment and card recharge flows are simulations and do not connect to a payment gateway."),
        bullet("Email delivery depends on external SMTP configuration and provider rules."),
        heading("12. Suggested Future Improvements"),
        bullet("Move persistence from JSON to a real database such as SQLite/PostgreSQL with proper models and migrations."),
        bullet("Add admin views for users, orders, platform credits, supplier products, and email delivery logs."),
        bullet("Support multiple supplier products per supplier account."),
        bullet("Add real product inventory quantities to cart items and checkout."),
        bullet("Add email templates with HTML formatting and retry logic for failed email sends."),
        bullet("Deploy using a production WSGI server and environment-based configuration."),
        heading("13. Conclusion"),
        paragraph("E buy is now a complete local ecommerce prototype with buyer and supplier flows, order management, wallet credits, supplier listing, order tracking, and email confirmation support. It is suitable as a coursework or demonstration project and provides a clear foundation for future database, admin, deployment, and production-email improvements."),
        sect_pr(),
    ]
    body = "".join(parts)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{NS['w']}" xmlns:r="{NS['r']}"><w:body>{body}</w:body></w:document>"""


def write_docx():
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    word_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>"""
    core = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>E buy Ecommerce Project Documentation</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
</cp:coreProperties>"""
    app = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Codex</Application></Properties>"""

    with zipfile.ZipFile(OUT_PATH, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("word/_rels/document.xml.rels", word_rels)
        docx.writestr("word/document.xml", document_xml())
        docx.writestr("word/styles.xml", styles_xml())
        docx.writestr("word/numbering.xml", numbering_xml())
        docx.writestr("docProps/core.xml", core)
        docx.writestr("docProps/app.xml", app)


if __name__ == "__main__":
    write_docx()
    print(OUT_PATH)
