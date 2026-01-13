from django.core.management.base import BaseCommand
from apps.masters.states.models import State

class Command(BaseCommand):
    help = "Seed Indian States"

    def handle(self, *args, **options):
        states = [
            (1, 'Jammu & Kashmir', 'JK'),
            (2, 'HIMACHAL PRADESH', 'HP'),
            (3, 'Punjab', 'PB'),
            (4, 'Chandigarh', 'CD'),
            (5, 'Uttarakhand', 'UK'),
            (6, 'Haryana', 'HR'),
            (7, 'Delhi', 'DL'),
            (8, 'RAJASTHAN', 'RJ'),
            (9, 'UTTAR PRADESH', 'UP'),
            (10, 'BIHAR', 'BH'),
            (11, 'Sikkim', 'SK'),
            (12, 'Arunachal Pradesh', 'AP'),
            (13, 'Nagaland', 'NG'),
            (14, 'Manipur', 'MN'),
            (15, 'Mizoram', 'MZ'),
            (16, 'Tripura', 'TP'),
            (17, 'Meghalaya', 'MG'),
            (18, 'Assam', 'AM'),
            (19, 'West Bengal', 'WB'),
            (20, 'Jharkhand', 'JH'),
            (21, 'Odisha', 'OD'),
            (22, 'Chhattisgarh', 'CG'),
            (23, 'Madhya Pradesh', 'MP'),
            (24, 'Gujarat', 'GJ'),
            (27, 'MAHARASHTRA', 'MH'),
            (28, 'Andhra Pradesh', 'AD'),
            (29, 'KARNATAKA', 'KN'),
            (30, 'Goa', 'GA'),
            (32, 'Kerala', 'KL'),
            (33, 'Tamil Nadu', 'TN'),
            (34, 'Puducherry', 'PD'),
            (35, 'Andaman & Nicobar Islands', 'AN'),
            (36, 'TELANGANA', 'TL'),
            (37, 'Ladakh', 'LD'),
            (38, 'Daman & Diu Nagar Haveli', 'DD'),
        ]

        created, skipped = 0, 0

        for state_id, name, short_name in states:
            obj, is_created = State.objects.get_or_create(
                state_id=state_id,
                defaults={
                    'name': name.strip(),
                    'short_name': short_name,
                    'is_active': True
                }
            )
            if is_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"States seeded successfully | Created: {created}, Skipped: {skipped}"
        ))
