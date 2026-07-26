import pytest
import responses
import re
from main import fetch_pending_records, restructure_content, correct_grammar

@responses.activate
def test_fetch_pending_records():
    mock_data = {
        "records": [
            {"id": "rec123", "fields": {"Topic": "AI Tech", "Status": "Pending"}},
            {"id": "rec456", "fields": {"Topic": "Python Tips", "Status": "Pending"}}
        ]
    }
    responses.add(
        responses.GET,
        re.compile(r"https://api.airtable.com/v0/.*"),
        json=mock_data,
        status=200
    )
    
    records = fetch_pending_records()
    assert len(records) == 2
    assert records[0]["id"] == "rec123"
    assert records[1]["fields"]["Topic"] == "Python Tips"

@responses.activate
def test_correct_grammar():
    mock_resp = {
        "matches": [
            {
                "offset": 0,
                "length": 5,
                "replacements": [{"value": "Hello"}]
            }
        ]
    }
    responses.add(
        responses.POST,
        "https://api.languagetool.org/v2/check",
        json=mock_resp,
        status=200
    )
    
    result = correct_grammar("helo world")
    assert result == "Hello world"
    assert "Hello" in result
    assert len(responses.calls) == 1

def test_restructure_content_formatting():
    input_text = "1. Introduction\nThis is a test. This is sentence two. This is sentence three. This is sentence four."
    restructured = restructure_content(input_text)
    
    # Check H3 conversion
    assert "### 1. Introduction" in restructured
    # Check sentence grouping (3 sentences per paragraph)
    assert "This is a test. This is sentence two. This is sentence three." in restructured
    assert "\n\nThis is sentence four." in restructured

def test_restructure_content_empty_handling():
    assert restructure_content("") == ""
    assert restructure_content("\n\n") == ""
    
    normal_text = "Paragraph one is here.\n\nParagraph two is there."
    result = restructure_content(normal_text)
    assert "Paragraph one is here." in result
    assert "Paragraph two is there." in result