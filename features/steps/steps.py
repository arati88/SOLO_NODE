import sys
import os
from decimal import Decimal
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from behave import given, when, then
from validation import validate_transaction
from security import authenticate
from fee import calculate_fee
from audit import log_transaction
from main import process_transaction


# ─────────────────────────────────────────
# VALIDATION STEPS
# ─────────────────────────────────────────

@given('a transaction with id "{txn_id}" amount {amount:f} and merchant "{merchant}"')
def step_valid_transaction(context, txn_id, amount, merchant):
    context.txn = {
        "transaction_id": txn_id,
        "amount": Decimal(str(amount)),
        "merchant_id": merchant
    }
    context.exception = None

@given('a transaction with no transaction_id')
def step_missing_transaction_id(context):
    context.txn = {"amount": Decimal("500.0"), "merchant_id": "M101"}
    context.exception = None

@given('a transaction with no amount')
def step_missing_amount(context):
    context.txn = {"transaction_id": "TXN1001", "merchant_id": "M101"}
    context.exception = None

@given('a transaction with no merchant_id')
def step_missing_merchant_id(context):
    context.txn = {"transaction_id": "TXN1001", "amount": Decimal("500.0")}
    context.exception = None

@given('a transaction with amount as string "{value}"')
def step_amount_as_string(context, value):
    context.txn = {"transaction_id": "TXN1001", "amount": value, "merchant_id": "M101"}
    context.exception = None

@given('a transaction with amount {amount:g}')
def step_invalid_amount(context, amount):
    context.txn = {"transaction_id": "TXN1001", "amount": Decimal(str(amount)), "merchant_id": "M101"}
    context.exception = None

@when('I validate the transaction')
def step_run_validation(context):
    try:
        context.result = validate_transaction(context.txn)
        context.exception = None
    except (ValueError, TypeError) as e:
        context.exception = e
        context.result = None

@then('validation should pass')
def step_validation_passes(context):
    assert context.exception is None, f"Unexpected exception: {context.exception}"
    assert context.result is True

@then('it should raise a ValueError with "{message}"')
def step_raises_value_error(context, message):
    assert isinstance(context.exception, ValueError), \
        f"Expected ValueError but got {type(context.exception)}"
    assert message in str(context.exception), \
        f"Expected '{message}' in '{context.exception}'"

@then('it should raise a TypeError')
def step_raises_type_error(context):
    assert isinstance(context.exception, TypeError), \
        f"Expected TypeError but got {type(context.exception)}"


# ─────────────────────────────────────────
# SECURITY STEPS
# ─────────────────────────────────────────

@given('the API token is "{token}"')
def step_set_api_token(context, token):
    context.expected_token = token
    context.exception = None

@when('I authenticate with token "{token}"')
def step_run_authentication(context, token):
    with patch.dict(os.environ, {'API_TOKEN': context.expected_token}):
        try:
            authenticate(token)
            context.auth_result = True
            context.exception = None
        except (PermissionError, RuntimeError) as e:
            context.exception = e
            context.auth_result = None

@when(u'I authenticate with token ""')
def step_run_authentication_empty(context):
    with patch.dict(os.environ, {'API_TOKEN': context.expected_token}):
        try:
            authenticate("")
            context.auth_result = True
            context.exception = None
        except (PermissionError, RuntimeError) as e:
            context.exception = e
            context.auth_result = None

@then('authentication should pass')
def step_auth_passes(context):
    assert context.exception is None, f"Unexpected exception: {context.exception}"

@then('it should raise a PermissionError with "{message}"')
def step_raises_permission_error(context, message):
    assert isinstance(context.exception, PermissionError), \
        f"Expected PermissionError but got {type(context.exception)}"
    assert message in str(context.exception), \
        f"Expected '{message}' in '{context.exception}'"


# ─────────────────────────────────────────
# FEE STEPS
# ─────────────────────────────────────────

@given('a transaction amount of {amount:f}')
def step_set_amount(context, amount):
    context.amount = Decimal(str(amount))
    context.exception = None

@when('I calculate the fee')
def step_run_fee_calculation(context):
    context.fee = calculate_fee(context.amount)

@then('the fee should be {expected:f}')
def step_check_fee(context, expected):
    assert context.fee == Decimal(str(expected)), \
        f"Expected fee {expected} but got {context.fee}"


# ─────────────────────────────────────────
# AUDIT STEPS
# ─────────────────────────────────────────

@given('the database is available')
def step_db_available(context):
    context.db_available = True
    context.exception = None
    context.log_called = False

@given('the database is unavailable')
def step_db_unavailable(context):
    context.db_available = False
    context.exception = None
    context.log_called = False

@when('I log transaction "{txn_id}" with amount {amount:f} fee {fee:f} and status "{status}"')
def step_log_transaction(context, txn_id, amount, fee, status):
    if context.db_available:
        with patch('audit.call_procedure') as mock_proc:
            mock_proc.return_value = None
            try:
                log_transaction(txn_id, amount, fee, status)
                context.log_called = mock_proc.called
                context.exception = None
            except Exception as e:
                context.exception = e
    else:
        with patch('audit.call_procedure') as mock_proc:
            mock_proc.side_effect = Exception("DB connection failed")
            try:
                log_transaction(txn_id, amount, fee, status)
                context.exception = None
            except Exception as e:
                context.exception = e

@then('the audit log should be saved without errors')
def step_audit_saved(context):
    assert context.exception is None, \
        f"Unexpected exception raised: {context.exception}"
    assert context.log_called is True, \
        "call_procedure was never called — log was not saved"

@then('it should raise a database exception')
def step_audit_raises(context):
    assert context.exception is not None, \
        "Expected an exception but none was raised"
    assert "DB connection failed" in str(context.exception), \
        f"Unexpected exception message: {context.exception}"

@then('the error should be logged before raising')
def step_audit_logs_before_raising(context):
    with patch('audit.call_procedure') as mock_proc:
        with patch('audit.logger') as mock_logger:
            mock_proc.side_effect = Exception("DB connection failed")
            try:
                log_transaction("TXN9999", 100.0, 2.0, "SUCCESS")
            except Exception:
                pass
            mock_logger.exception.assert_called_once()


# ─────────────────────────────────────────
# MAIN PIPELINE STEPS
# ─────────────────────────────────────────

@given('a valid transaction "{txn_id}" with amount {amount:g} and merchant "{merchant}" and token "{token}"')
def step_set_pipeline_transaction(context, txn_id, amount, merchant, token):
    context.txn = {
        "transaction_id": txn_id,
        "amount": Decimal(str(amount)),
        "merchant_id": merchant
    }
    context.token = token
    context.audit_status = None

@given('an incomplete transaction missing the amount field')
def step_incomplete_transaction(context):
    context.txn = {
        "transaction_id": "TXN_BAD",
        "merchant_id": "M101"
    }
    context.token = "SECURE123TOKEN"
    context.audit_status = None

@when('I run the transaction through the pipeline')
def step_run_pipeline(context):
    with patch.dict(os.environ, {'API_TOKEN': 'SECURE123TOKEN'}):
        with patch('main.log_transaction') as mock_log:
            def capture_log(txn_id, amount, fee, status):
                context.audit_status = status
            mock_log.side_effect = capture_log
            context.result = process_transaction(context.txn, context.token)

@then('the result status should be "{expected_status}"')
def step_check_pipeline_status(context, expected_status):
    assert context.result["status"] == expected_status, \
        f"Expected status '{expected_status}' but got '{context.result['status']}'"

@then('the result should contain a fee')
def step_check_fee_present(context):
    assert "fee" in context.result, "Fee key missing from result"
    assert Decimal(context.result["fee"]) > 0, \
        f"Expected fee > 0 but got {context.result['fee']}"

@then('the result should contain an error message')
def step_check_error_present(context):
    assert "error" in context.result, "Error key missing from result"
    assert len(str(context.result["error"])) > 0, "Error message is empty"

@then('the audit log should be called with status "{expected_status}"')
def step_check_audit_status(context, expected_status):
    assert context.audit_status == expected_status, \
        f"Expected audit status '{expected_status}' but got '{context.audit_status}'"
