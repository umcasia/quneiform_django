from django.db import transaction

from apps.masters.states.models import State
from apps.masters.districts.models import District

from apps.subunits.models import (
    UserHasSuState,
    UserHasSuDistrict,
)


class SubunitService:
    """
    Django equivalent of Laravel SubunitService
    """

    @staticmethod
    @transaction.atomic
    def assign_locations(user_id: int, subunit_id: int):
        """
        Laravel equivalent:

        State::chunk(500, function ($states) { ... })
        """

        # -----------------------------
        # Chunk States (memory safe)
        # -----------------------------
        for state in State.objects.iterator(chunk_size=500):

            # -----------------------------
            # Assign State
            # -----------------------------
            UserHasSuState.objects.update_or_create(
                user_id=user_id,
                subunit_id=subunit_id,
                state_id=state.id,
                defaults={}
            )

            # -----------------------------
            # Chunk Districts of this State
            # -----------------------------
            for district in District.objects.filter(
                state_id=state.id
            ).iterator(chunk_size=500):

                UserHasSuDistrict.objects.update_or_create(
                    user_id=user_id,
                    subunit_id=subunit_id,
                    district_id=district.id,
                    defaults={}
                )
