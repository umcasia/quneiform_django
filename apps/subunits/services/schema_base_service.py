import json
from apps.subunits.models import SubunitTableMapping


class SchemaBaseService:

    @staticmethod
    def str_json_to_dict(raw_json: str) -> dict:
        try:
            return json.loads(raw_json)
        except Exception as e:
            raise ValueError(f"Invalid JSON schema: {e}")

    @staticmethod
    def generate_table_name(project_acronym, subunit_acronym, section_acronym, parent=None):
        base = f"{project_acronym}_{subunit_acronym}_{section_acronym}"
        return f"{parent}_{section_acronym}" if parent else base

    @staticmethod
    def create_subunit_table_mapping(
        subunit_id,
        section_name,
        section_acronym,
        table_name,
        fields,
        acronym_sequence,
        parent_id=None
    ):
        mapping = SubunitTableMapping.objects.create(
            subunit_id=subunit_id,
            section_name=section_name,
            section_acronym=section_acronym,
            table_name=table_name,
            fields=fields,
            acronym_sequence=acronym_sequence,
            parent_id=parent_id,
        )
        return mapping.id

    @staticmethod
    def update_subunit_table_mapping(mapping_id, fields):
        SubunitTableMapping.objects.filter(id=mapping_id).update(fields=fields)
