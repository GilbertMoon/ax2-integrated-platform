"""Keep LMS uploads separate from Core profile images."""
from django.core.files.storage import storages
from django.utils.functional import SimpleLazyObject

default_storage = SimpleLazyObject(lambda: storages["lms"])
