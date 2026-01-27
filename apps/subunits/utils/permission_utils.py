# apps/subunits/utils/permission_utils.py

class PermissionUtils:

    @staticmethod
    def role_permissions():
        return {

            # ================= ADMIN =================
            "Admin": [
                "create user", "read user", "update user", "delete user",
                "create role", "read role", "update role", "delete role",
                "create survey", "read survey", "update survey", "delete survey",

                "create qc", "read qc", "update qc", "delete qc", "resolve qc",

                "create validation", "read validation", "update validation", "delete validation",

                "create district validation", "read district validation", "update district validation", "delete district validation",
                "create state validation", "read state validation", "update state validation", "delete state validation",
                "create block validation", "read block validation", "update block validation", "delete block validation",

                "create dynamic page", "read dynamic page", "update dynamic page", "delete dynamic page",

                "download survey", "restore survey",

                "create state", "read state", "update state", "delete state",
                "create district", "read district", "update district", "delete district",
                "create city", "read city", "update city", "delete city",
                "create block", "read block", "update block", "delete block",
                "create gp", "read gp", "update gp", "delete gp",
                "create village", "read village", "update village", "delete village",

                "qc download realese",
                "qc assigne to user",
                "validation assigned to user",
                "validation release",

                "reset password",
                "change status",

                "create designation", "read designation", "update designation", "delete designation",
                "create reports", "read reports", "update reports", "delete reports",

                "create organization", "read organization", "update organization", "delete organization", "approve organization",
            ],

            # ================= SURVEYOR =================
            "Surveyor": [
                "create survey", "read survey", "update survey", "delete survey",
                "create qc", "read qc", "update qc", "delete qc", "resolve qc",
            ],

            # ================= NODAL OFFICER =================
            "Nodal Officer": [
                "read survey", "read reports", "read qc",
                "create user", "read user", "update user",
                "qc download realese", "qc assigne to user",
                "validation assigned to user", "validation release",
            ],

            # ================= VALIDATOR =================
            "Validator": [
                "create validation", "read validation", "update validation",
                "create qc", "read qc", "update qc", "delete qc",
                "read survey", "update survey",
            ],

            # ================= QC =================
            "QC": [
                "create qc", "read qc", "update qc", "delete qc",
                "read survey",
            ],

            # ================= VIEWER =================
            "Viewer": [
                "read user", "read survey", "read qc", "read validation",
                "download survey", "read reports",
            ],
        }

    @staticmethod
    def get_permissions_for_role(role_name: str):
        return PermissionUtils.role_permissions().get(role_name, [])
