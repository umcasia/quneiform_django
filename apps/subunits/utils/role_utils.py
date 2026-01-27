# apps/subunits/utils/role_utils.py

from apps.subunits.utils.permission_utils import PermissionUtils


class RoleUtils:

    @staticmethod
    def roles():
        return [
            {
                "name": "Admin",
                "description": None,
                "superiority": 5,
                "permissions": PermissionUtils.get_permissions_for_role("Admin"),
            },
            {
                "name": "Surveyor",
                "description": None,
                "superiority": 10,
                "permissions": PermissionUtils.get_permissions_for_role("Surveyor"),
            },
            {
                "name": "Nodal Officer",
                "description": None,
                "superiority": 20,
                "permissions": PermissionUtils.get_permissions_for_role("Nodal Officer"),
            },
            {
                "name": "Validator",
                "description": None,
                "superiority": 25,
                "permissions": PermissionUtils.get_permissions_for_role("Validator"),
            },
            {
                "name": "QC",
                "description": None,
                "superiority": 30,
                "permissions": PermissionUtils.get_permissions_for_role("QC"),
            },
            {
                "name": "Viewer",
                "description": None,
                "superiority": 35,
                "permissions": PermissionUtils.get_permissions_for_role("Viewer"),
            },
        ]
