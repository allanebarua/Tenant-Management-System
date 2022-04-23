"""Shared User Utilities."""
from rest_framework import exceptions


def get_db_object(model, pk):
    try:
        return model.objects.get(id=pk)
    except model.DoesNotExist:
        raise exceptions.NotFound(f'{model.__name__} with id {pk} not found')
