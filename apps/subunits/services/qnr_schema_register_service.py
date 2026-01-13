from django.db import connection, models
from django.utils import timezone
from apps.subunits.models import Subunit
from apps.subunits.services.schema_base_service import SchemaBaseService


class QnrSchemaRegisterService:

    def __init__(self, user_id, subunit_id, project_acronym, subunit_acronym, have_qc, have_validation):
        self.user_id = user_id
        self.subunit_id = subunit_id
        self.project_acronym = project_acronym
        self.subunit_acronym = subunit_acronym
        self.table_prefix = f"{project_acronym}_{subunit_acronym}"

        self.su_have_qc = have_qc
        self.su_have_validation = have_validation

        self.tables_created = []
        self.view_home_map = {}
        self.filter_home_map = {}

    # 🚫 NO transaction.atomic HERE
    def register_schema(self, schema):
        try:
            self._process_sections(schema["data"])
            self._update_subunit_maps()
            self._create_sysgen_tables()
        except Exception:
            self._rollback()
            raise

    def _process_sections(self, sections):
        for section in sections:
            self._process_section(section, [])

    def _process_section(self, section, acronym_seq, parent_mapping=None, parent_table=None):
        table_name = SchemaBaseService.generate_table_name(
            self.project_acronym,
            self.subunit_acronym,
            section["acronym"],
            parent_table
        )

        if table_name in connection.introspection.table_names():
            raise Exception(f"TABLE_EXISTS_EXCEPTION: {table_name}")

        acronym_seq = acronym_seq + [section["acronym"]]
        fields = []

        mapping_id = SchemaBaseService.create_subunit_table_mapping(
            self.subunit_id,
            section["title"],
            section["acronym"],
            table_name,
            fields,
            acronym_seq,
            parent_mapping
        )

        self._create_section_table(table_name, section, fields)
        self.tables_created.append(table_name)

        SchemaBaseService.update_subunit_table_mapping(mapping_id, fields)

    def _create_section_table(self, table_name, section, fields):
        class Meta:
            db_table = table_name

        attrs = {
            "__module__": "apps.subunits.dynamic",
            "id": models.BigAutoField(primary_key=True),
            "ss_id": models.BigIntegerField(),
            "deleted_at": models.DateTimeField(null=True),
            "Meta": Meta,
        }

        for item in section["children"]:
            if item["type"] == "SECTION":
                self._process_section(item, [], None, table_name)
                continue

            field = item["id"]
            ftype = item["type"]

            if ftype in ["TEXT", "RADIO", "NUMBERS", "LOCATION", "DATE_RANGE"]:
                attrs[field] = models.CharField(max_length=255, null=True)
            elif ftype in ["DROPDOWN", "TEXT_AREA", "AADHAAR"]:
                attrs[field] = models.TextField(null=True)
            elif ftype in ["UPLOAD_IMAGE", "CAPTURE_IMAGE", "AUDIO_RECORD"]:
                attrs[field] = models.JSONField(null=True)
            elif ftype == "DATE":
                attrs[field] = models.DateField(null=True)

            fields.append(field)

            if item.get("viewHome"):
                self.view_home_map[field] = item.get("homeLabel")

            if item.get("filterHome"):
                self.filter_home_map[field] = item.get("homeLabel")

        model = type(table_name, (models.Model,), attrs)
        with connection.schema_editor() as se:
            se.create_model(model)

    def _update_subunit_maps(self):
        Subunit.objects.filter(id=self.subunit_id).update(
            view_home_map=self.view_home_map,
            filter_home_map=self.filter_home_map
        )

    def _create_sysgen_tables(self):
        existing = connection.introspection.table_names()
        prefix = self.table_prefix

        def create(table, fields):
            class Meta:
                db_table = table

            attrs = {
                "__module__": "apps.subunits.dynamic",
                "id": models.BigAutoField(primary_key=True),
                "created_at": models.DateTimeField(default=timezone.now),
                "updated_at": models.DateTimeField(default=timezone.now),
                "deleted_at": models.DateTimeField(null=True),
                "Meta": Meta,
            }
            attrs.update(fields)

            model = type(table, (models.Model,), attrs)
            with connection.schema_editor() as se:
                se.create_model(model)
            self.tables_created.append(table)

        survey = f"{prefix}_SYSGEN_survey_submissions"
        if survey not in existing:
            create(survey, {
                "subunit_id": models.BigIntegerField(),
                "review_status": models.TextField(null=True),
                "submitted_json": models.JSONField(null=True),
            })

    def _rollback(self):
        with connection.cursor() as cursor:
            for table in reversed(self.tables_created):
                cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
