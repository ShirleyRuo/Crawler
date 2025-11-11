import pytest

from src.PageParse.JabPageParser.JabActressId import JabActressId

@pytest.fixture
def jab_actress_id():
    with open('tests/PageParse/JabPageParser/test_files/actress_home.html', 'r', encoding='utf-8') as f:
        html_text = f.read()
    parser = JabActressId(html_text=html_text)
    return parser

def test_parse(jab_actress_id):
    jab_actress_id._parse()
    assert jab_actress_id.actress_info[0].actress_id == '10000001'
    assert jab_actress_id.actress_info[0].actress_name == '白石麻衣'