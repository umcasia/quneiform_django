# apps/roles/services/auto_role_creator_service.py

from apps.subunits.models import Permission, SuRole, SuRoleHasPermission, UserHasSuRole
from apps.subunits.utils.role_utils import RoleUtils


class AutoRoleCreatorService:

    @staticmethod
    def create_roles_for_subunit(subunit, creator_user):
        roles_data = RoleUtils.roles()

        for role_data in roles_data:
            role = SuRole.objects.create(
                subunit=subunit,
                name=role_data["name"],
                description=role_data["description"],
                superiority=role_data["superiority"],
                created_by=creator_user,
            )

            print(f"✅ Role {role.name} created")

            # Assign permissions
            permissions = Permission.objects.filter(name__in=role_data["permissions"])

            for perm in permissions:
                SuRoleHasPermission.objects.create(
                    role=role,
                    permission=perm
                )

            print(f"✅ Permissions added for {role.name}")

            # Auto assign Admin role to creator
            if role.name == "Admin":
                UserHasSuRole.objects.create(
                    subunit=subunit,
                    user=creator_user,
                    role=role
                )

                print(f"🔥 Admin role assigned to {creator_user.email}")
