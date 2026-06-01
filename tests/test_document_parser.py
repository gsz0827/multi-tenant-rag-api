from app.services.document_parser import sanitize_extracted_text, parse_document_file


def test_sanitize_extracted_text_removes_nul_characters():
    raw_text = "hello\x00world\x00"

    cleaned_text = sanitize_extracted_text(raw_text)

    assert cleaned_text == "helloworld"
    assert "\x00" not in cleaned_text


def test_sanitize_extracted_text_handles_empty_text():
    assert sanitize_extracted_text("") == ""


def test_parse_txt_file_removes_nul_characters(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("第一段\x00第二段", encoding="utf-8")

    parsed_text = parse_document_file(str(test_file), "text/plain")

    assert parsed_text == "第一段第二段"
    assert "\x00" not in parsed_text