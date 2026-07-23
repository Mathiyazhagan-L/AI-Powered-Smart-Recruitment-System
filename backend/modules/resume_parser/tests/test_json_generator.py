from modules.resume_parser.models.json_generator import JsonGenerator


def test_json_generator_fills_missing_values():
    output = JsonGenerator().generate({"personal": {"email": "a@example.com"}})

    assert output["personal"]["email"] == "a@example.com"
    assert output["personal"]["full_name"] is None
    assert output["skills"] == []
