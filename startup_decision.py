#!/usr/bin/env python3
"""Pure startup decision model, not a startup service or installer.

Callbacks are injectable so tests can verify which state is accessed. An actual
implementation must authenticate and durably journal state, lock concurrent
runs, perform recovery, and integrate all application adapters.
"""
import re

# Example only: replace with the source board's validated hardware serial.
FIRST_SERIAL = '1111111111111111'
FIRST_HOST = 'source.example.com'


def decide(read_identity, read_state, select_profile):
    identity = read_identity()
    if not isinstance(identity, dict) or not isinstance(identity.get('serial'), str):
        raise ValueError('Validated identity is required')
    serial = identity['serial']
    if not re.fullmatch('[0-9a-f]{16}', serial) or serial == '0000000000000000':
        raise ValueError('Validated identity is required')
    if serial == FIRST_SERIAL:
        return {'action': 'exit_first_board', 'hostname': FIRST_HOST}
    state = read_state()
    if not isinstance(state, dict) or state.get('status') not in ('none', 'applying', 'rolling_back', 'committed_pending_release', 'complete', 'rolled_back'):
        raise ValueError('Invalid transaction state')
    status = state['status']
    if status in ('applying', 'rolling_back'):
        if state.get('serial') != serial:
            raise ValueError('Interrupted transaction belongs to another board')
        return {'action': 'recover_incomplete_transaction'}
    if status == 'committed_pending_release':
        if state.get('serial') != serial:
            raise ValueError('Pending release belongs to another board')
        return {'action': 'resume_committed_release'}
    if status == 'rolled_back':
        if state.get('serial') != serial:
            raise ValueError('Rollback belongs to another board')
        return {'action': 'report_rollback_and_wait'}
    if status == 'complete':
        if state.get('serial') != serial:
            raise ValueError('Completed conversion belongs to another board; review source state')
        return {'action': 'exit_completed'}
    profile = select_profile(serial)
    if not isinstance(profile, dict) or profile.get('action') != 'check_completion':
        raise ValueError('Invalid profile selection')
    return {'action': 'prepare_conversion', 'hostname': profile['hostname']}
