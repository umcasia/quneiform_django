# services/qnr_schema_validate_service.py

class QnrSchemaValidateService:

    def __init__(self, schema: dict):
        self.schema = schema

    def validate_form_schema(self):
        if "data" not in self.schema:
            raise Exception("Schema missing `data` key")

        if not isinstance(self.schema["data"], list):
            raise Exception("Schema `data` must be an array")

        for section in self.schema["data"]:
            self._validate_section(section)

    def _validate_section(self, section):
        required_keys = ["type", "title", "acronym", "children"]
        for key in required_keys:
            if key not in section:
                raise Exception(f"Section missing `{key}`")

        for child in section["children"]:
            if child["type"] == "SECTION":
                self._validate_section(child)
