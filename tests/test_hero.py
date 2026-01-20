import json
from app.blocks2html import convert_blocks_to_html
from app.html2blocks import text_to_blocks
from app.main import Blocks

HERO_BLOCK = {
  "@type": "hero",
  "buttonLabel": "Learn more about the Observatory",
  "buttonLink": "http://localhost:3000/en/observatory/invitation_climate_change_and_health_9_november_2022.pdf",
  "copyright": "Some copyraight text",
  "copyrightIcon": "ri-copyright-line",
  "copyrightPosition": "left",
  "data": {
    "blocks": {
      "f0fa047b-02f3-4c36-bf3f-56a164e03369": {
        "@type": "slate",
        "plaintext": "Text two",
        "value": [
          {
            "children": [
              {
                "text": "Text two"
              }
            ],
            "type": "p"
          }
        ]
      },
      "f7ad796b-77e3-4967-82ba-eae49f433eac": {
        "@type": "slate",
        "plaintext": "Text one",
        "value": [
          {
            "children": [
              {
                "text": "Text one"
              }
            ],
            "type": "h2"
          }
        ]
      }
    },
    "blocks_layout": {
      "items": [
        "f7ad796b-77e3-4967-82ba-eae49f433eac",
        "f0fa047b-02f3-4c36-bf3f-56a164e03369"
      ]
    }
  },
  "fullHeight": True,
  "fullWidth": True,
  "image": [
    {
      "@id": "http://localhost:3000/en/observatory/virgolici-raluca-environment-me-eea.jpg",
      "image_field": "image",
    }
  ],
  "inverted": True,
  "overlay": True,
  "quoted": False,
  "spaced": False,
  "styles": {
    "alignContent": "center",
    "bg": "has--bg--center",
    "buttonAlign": "left",
    "textAlign": "left"
  }
}

def test_hero_roundtrip():
    # Wrap in Blocks structure
    data = Blocks(
        blocks={"uid1": HERO_BLOCK},
        blocks_layout={"items": ["uid1"]}
    )
    
    # Serialize
    html = convert_blocks_to_html(data)
    
    # print("Generated HTML:", html)
    
    # Check fields
    assert 'data-block-type="hero"' in html
    assert 'data-fieldname="buttonLabel"' in html
    assert 'Learn more about the Observatory' in html
    assert 'data-fieldname="copyright"' in html
    assert 'Some copyraight text' in html
    
    # Check nested blocks
    assert 'Text one' in html
    assert 'Text two' in html
    
    # Deserialize
    blocks = text_to_blocks(html)
    
    # Check structure
    # blocks is a list of [uid, block]
    assert len(blocks) == 1
    uid, block = blocks[0]
    
    assert block['@type'] == 'hero'
    assert block['buttonLabel'] == "Learn more about the Observatory"
    assert block['copyright'] == "Some copyraight text"
    assert block['inverted'] is True
    
    # Check nested blocks reconstruction
    assert 'data' in block
    assert 'blocks' in block['data']
    assert len(block['data']['blocks']) == 2
