import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('decision', ROOT / 'startup_decision.py')
decision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decision)


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.serial = '1234567890abcdef'
        self.state = {'status': 'none'}
        self.calls = []

    def identity(self): self.calls.append('identity'); return {'serial': self.serial}
    def read_state(self): self.calls.append('state'); return self.state
    def profile(self, serial):
        self.calls.append('profile')
        return {'action': 'check_completion', 'hostname': 'destination.example.com'}
    def run_decision(self): return decision.decide(self.identity, self.read_state, self.profile)

    def test_first_board_exits_without_reading_state_or_config(self):
        self.serial = decision.FIRST_SERIAL
        self.assertEqual(self.run_decision()['action'], 'exit_first_board')
        self.assertEqual(self.calls, ['identity'])

    def test_new_board_selects_profile(self):
        self.assertEqual(self.run_decision()['action'], 'prepare_conversion')
        self.assertEqual(self.calls, ['identity', 'state', 'profile'])

    def test_completed_board_does_not_reapply_or_read_profile(self):
        self.state = {'status': 'complete', 'serial': self.serial}
        self.assertEqual(self.run_decision()['action'], 'exit_completed')
        self.assertNotIn('profile', self.calls)

    def test_interruption_recovers_even_when_profile_unavailable(self):
        self.state = {'status': 'applying', 'serial': self.serial}
        self.assertEqual(self.run_decision()['action'], 'recover_incomplete_transaction')
        self.assertNotIn('profile', self.calls)

    def test_committed_release_is_resumed_without_reapplying_conversion(self):
        self.state = {'status': 'committed_pending_release', 'serial': self.serial}
        self.assertEqual(self.run_decision()['action'], 'resume_committed_release')
        self.assertNotIn('profile', self.calls)

    def test_pending_release_from_another_board_is_rejected(self):
        self.state = {'status': 'committed_pending_release', 'serial': 'abcdef1234567890'}
        with self.assertRaises(ValueError): self.run_decision()
        self.assertNotIn('profile', self.calls)

    def test_rollback_waits(self):
        self.state = {'status': 'rolled_back', 'serial': self.serial}
        self.assertEqual(self.run_decision()['action'], 'report_rollback_and_wait')

    def test_incomplete_other_board_stops(self):
        self.state = {'status': 'applying', 'serial': 'abcdef1234567890'}
        with self.assertRaises(ValueError): self.run_decision()

    def test_invalid_serial_stops_before_state(self):
        self.serial = 'invalid'
        with self.assertRaises(ValueError): self.run_decision()
        self.assertEqual(self.calls, ['identity'])

    def test_copied_completed_marker_stops_for_review(self):
        self.state = {'status': 'complete', 'serial': 'abcdef1234567890'}
        with self.assertRaises(ValueError): self.run_decision()
        self.assertNotIn('profile', self.calls)


if __name__ == '__main__': unittest.main()
