"""LMS atomic blocks and callbacks belong to the LMS database."""
from functools import partial
from django.db import transaction as _transaction

atomic = partial(_transaction.atomic, using="assignment_lms")
on_commit = partial(_transaction.on_commit, using="assignment_lms")
set_rollback = partial(_transaction.set_rollback, using="assignment_lms")
