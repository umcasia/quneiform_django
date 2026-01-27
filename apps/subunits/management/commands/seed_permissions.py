# apps/subunits/management/commands/seed_permissions.py

from django.core.management.base import BaseCommand
from apps.subunits.models import Permission
from apps.subunits.utils.permission_utils import PermissionUtils


class Command(BaseCommand):
    help = "Seed permissions like Laravel seeder"

    def handle(self, *args, **kwargs):
        all_permissions = set()

        for role, perms in PermissionUtils.role_permissions().items():
            for perm in perms:
                all_permissions.add(perm)

        for perm in sorted(all_permissions):
            Permission.objects.get_or_create(name=perm)
            self.stdout.write(self.style.SUCCESS(f"Added permission: {perm}"))

        self.stdout.write(self.style.SUCCESS("✅ Permission seeding completed"))
