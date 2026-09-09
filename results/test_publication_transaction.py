from unittest.mock import patch
from django.db import connection
from django.test import TransactionTestCase
from results.application import toggle_publication


class PublicationTransactionTests(TransactionTestCase):
    def test_each_individual_publication_locks_inside_transaction(self):
        class StopBeforeWrite(Exception):
            pass
        def check_transaction(round_id):
            self.assertTrue(connection.in_atomic_block)
            raise StopBeforeWrite
        for key in ('team_winner', 'team_ranking', 'peer_ranking', 'my_score'):
            with self.subTest(key=key), patch('results.application._active_run_for_update', side_effect=check_transaction):
                self.assertFalse(connection.in_atomic_block)
                with self.assertRaises(StopBeforeWrite):
                    toggle_publication(round_id=61, item_key=key, actor=None)
                self.assertFalse(connection.in_atomic_block)
