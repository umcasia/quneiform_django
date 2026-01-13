from .models import State

class StateService:

    @staticmethod
    def list():
        return State.objects.filter(is_active=True)

    @staticmethod
    def get(pk):
        return State.objects.get(pk=pk)

    @staticmethod
    def create(data):
        return State.objects.create(name=data['name'])

    @staticmethod
    def update(pk, data):
        state = State.objects.get(pk=pk)
        state.name = data['name']
        state.save()
        return state

    @staticmethod
    def delete(pk):
        State.objects.filter(pk=pk).update(is_active=False)
