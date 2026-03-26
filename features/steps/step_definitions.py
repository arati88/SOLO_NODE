"""
Step definitions for SoloNode Transaction Audit POC.
All DB calls are mocked so no MySQL connection is required to run these tests.
"""
import inspect
import os
import copy
from decimal import Decimal
from unittest.mock import patch

from behave import given, when, then, use_step_matcher

# Regex matcher lets step patterns match empty strings inside quotes
use_step_matcher("re")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_txn(txn_id, amount_str, merchant_id):
    return {
        "transaction_id": txn_id,
        "amount": Decimal(amount_str),
        "merchant_id": merchant_id,
    }


# ===========================================================================
# ENVIRONMENT SETUP STEPS
# ===========================================================================

@given(u"the API token environment variable is set")
def step_set_api_token(context):
    os.environ["API_TOKEN"] = "SECURE123TOKEN"


@given(u'the API token environment variable is set to "(?P<token>[^"]*)"')
def step_set_api_token_value(context, token):
    os.environ["API_TOKEN"] = token


@given(u"the API token environment variable is not set")
def step_unset_api_token(context):
    os.environ.pop("API_TOKEN", None)


@given(u"the database stored procedure will succeed")
def step_db_success(context):
    context.db_patcher = patch("audit_logger.call_procedure", return_value=None)
    context.mock_db = context.db_patcher.start()


@given(u"the database stored procedure will raise an exception")
def step_db_fail(context):
    context.db_patcher = patch(
        "audit_logger.call_procedure",
        side_effect=Exception("MySQL connection refused: unable to reach solonode_db"),
    )
    context.mock_db = context.db_patcher.start()


# ===========================================================================
# AUDIT LOGGING STEPS  (audit_logging.feature)
# ===========================================================================

@when(u'I call log_transaction with txn_id "(?P<txn_id>[^"]*)" amount "(?P<amount>[^"]*)" fee "(?P<fee>[^"]*)" status "(?P<status>[^"]*)"')
def step_call_log_transaction(context, txn_id, amount, fee, status):
    from audit_logger import log_transaction
    context.raised_exception = None
    context.returned_normally = False
    try:
        log_transaction(txn_id, Decimal(amount), Decimal(fee), status)
        context.returned_normally = True
    except Exception as e:
        context.raised_exception = e
    finally:
        if hasattr(context, "db_patcher"):
            context.db_patcher.stop()


@then(u"no exception is raised")
def step_no_exception(context):
    assert context.raised_exception is None, (
        f"Expected no exception but got: {type(context.raised_exception).__name__}: {context.raised_exception}"
    )


@then(u"an exception is raised")
def step_exception_raised(context):
    assert context.raised_exception is not None, (
        "Expected an exception to be raised, but log_transaction returned normally.\n"
        "This is SN-01: the bare 'except: pass' is swallowing the DB error."
    )


@then(u"the exception message contains database error information")
def step_exception_message(context):
    assert context.raised_exception is not None, "No exception was raised."
    assert len(str(context.raised_exception)) > 0, "Exception message is empty."


@then(u"log_transaction does not return normally")
def step_does_not_return_normally(context):
    assert not context.returned_normally, (
        "log_transaction returned normally despite a DB failure.\n"
        "This is SN-01: the bare 'except: pass' is hiding the error from the caller."
    )


@then(u"a ValueError is raised")
def step_value_error_raised(context):
    assert isinstance(context.raised_exception, ValueError), (
        f"Expected ValueError but got: {type(context.raised_exception).__name__}: {context.raised_exception}"
    )


@then(u"a TypeError is raised")
def step_type_error_raised(context):
    assert isinstance(context.raised_exception, TypeError), (
        f"Expected TypeError but got: {type(context.raised_exception).__name__}: {context.raised_exception}"
    )


@then(u"a PermissionError is raised")
def step_permission_error_raised(context):
    assert isinstance(context.raised_exception, PermissionError), (
        f"Expected PermissionError but got: {type(context.raised_exception).__name__}: {context.raised_exception}"
    )


@then(u"a RuntimeError is raised")
def step_runtime_error_raised(context):
    assert isinstance(context.raised_exception, RuntimeError), (
        f"Expected RuntimeError but got: {type(context.raised_exception).__name__}: {context.raised_exception}"
    )


# ===========================================================================
# TRANSACTION VALIDATION STEPS  (transaction_validation.feature)
# ===========================================================================

@given(u'a transaction with id "(?P<txn_id>[^"]*)" amount "(?P<amount>[^"]*)" merchant "(?P<merchant_id>[^"]*)"')
def step_make_transaction(context, txn_id, amount, merchant_id):
    context.txn = {
        "transaction_id": txn_id,
        "amount": Decimal(amount),
        "merchant_id": merchant_id,
    }
    context.raised_exception = None


@given(u'a transaction with float amount (?P<amount>[0-9.]+) and id "(?P<txn_id>[^"]*)" merchant "(?P<merchant_id>[^"]*)"')
def step_make_float_transaction(context, amount, txn_id, merchant_id):
    context.txn = {
        "transaction_id": txn_id,
        "amount": float(amount),
        "merchant_id": merchant_id,
    }
    context.raised_exception = None


@when(u"I validate the transaction")
def step_validate_transaction(context):
    from transaction_validator import validate_transaction
    context.raised_exception = None
    context.validation_result = None
    try:
        context.validation_result = validate_transaction(context.txn)
    except Exception as e:
        context.raised_exception = e


@then(u"the result is True")
def step_result_is_true(context):
    assert context.raised_exception is None, f"Unexpected exception: {context.raised_exception}"
    assert context.validation_result is True, f"Expected True but got: {context.validation_result}"


@given(u"a batch of transactions:")
def step_make_batch(context):
    context.original_batch = []
    for row in context.table:
        txn = {
            "transaction_id": row["transaction_id"],
            "amount": Decimal(row["amount"]),
            "merchant_id": row["merchant_id"],
        }
        context.original_batch.append(txn)
    # Store original amounts keyed by transaction_id for mutation detection
    context.batch_before_amounts = {
        t["transaction_id"]: t["amount"] for t in context.original_batch
    }


@when(u"I call validate_batch with the batch")
def step_call_validate_batch(context):
    from transaction_validator import validate_batch
    context.raised_exception = None
    context.valid_transactions = []
    try:
        context.valid_transactions = validate_batch(context.original_batch)
    except Exception as e:
        context.raised_exception = e


@then(u"the original transaction amounts are unchanged")
def step_original_amounts_unchanged(context):
    for txn in context.original_batch:
        tid = txn["transaction_id"]
        original = context.batch_before_amounts[tid]
        current = txn["amount"]
        assert current == original and isinstance(current, Decimal), (
            f"Amount for {tid} was mutated!\n"
            f"  Before: {original} ({type(original).__name__})\n"
            f"  After:  {current} ({type(current).__name__})\n"
            "This is SN-02: validate_batch() sets txn['amount'] = int(txn['amount']), "
            "truncating the value and changing its type from Decimal to int."
        )


@then(u"(?P<txn_id>[A-Z0-9]+) original amount is still \"(?P<expected>[^\"]+)\"")
def step_original_amount_check(context, txn_id, expected):
    expected_dec = Decimal(expected)
    txn = next((t for t in context.original_batch if t["transaction_id"] == txn_id), None)
    assert txn is not None, f"Transaction {txn_id} not found in original batch"
    actual = txn["amount"]
    assert actual == expected_dec and isinstance(actual, Decimal), (
        f"{txn_id} amount was mutated!\n"
        f"  Expected: {expected_dec} (Decimal)\n"
        f"  Got:      {actual} ({type(actual).__name__})\n"
        "This is SN-02: validate_batch() converts amounts to int, truncating decimal parts "
        "and permanently modifying the caller's transaction objects."
    )


@then(u"\"(?P<txn_id>[^\"]+)\" in the valid result has amount \"(?P<expected>[^\"]+)\"")
def step_valid_result_amount(context, txn_id, expected):
    expected_dec = Decimal(expected)
    txn = next((t for t in context.valid_transactions if t["transaction_id"] == txn_id), None)
    assert txn is not None, f"Transaction {txn_id} not found in valid results"
    actual = txn["amount"]
    assert actual == expected_dec, (
        f"{txn_id} in valid result has wrong amount!\n"
        f"  Expected: {expected_dec}\n"
        f"  Got:      {actual}\n"
        "This is SN-02: validate_batch() truncates amounts to int before returning, "
        "so downstream fee calculation receives the wrong value."
    )


@then(u"the returned valid list contains (?P<count>[0-9]+) transactions")
def step_valid_list_count(context, count):
    expected = int(count)
    actual = len(context.valid_transactions)
    assert actual == expected, (
        f"Expected {expected} valid transactions but got {actual}: "
        f"{[t['transaction_id'] for t in context.valid_transactions]}"
    )


# ===========================================================================
# AUTHENTICATION STEPS  (authentication.feature)
# ===========================================================================

@when(u'I authenticate with token "(?P<token>[^"]*)"')
def step_authenticate(context, token):
    from authentication import authenticate
    context.raised_exception = None
    try:
        authenticate(token)
    except Exception as e:
        context.raised_exception = e


@when(u"I authenticate with a non-string token")
def step_authenticate_non_string(context):
    from authentication import authenticate
    context.raised_exception = None
    try:
        authenticate(12345)
    except Exception as e:
        context.raised_exception = e


@then(u"the authenticate function uses hmac.compare_digest for token comparison")
def step_check_hmac_usage(context):
    import authentication
    source = inspect.getsource(authentication.authenticate)
    assert "hmac.compare_digest" in source, (
        "authenticate() does not use hmac.compare_digest().\n"
        "This is SN-03: the current implementation uses plain '!=' which leaks token "
        "information through timing differences.\n"
        "Fix: replace 'if token != api_token:' with 'if not hmac.compare_digest(token, api_token):'"
    )


# ===========================================================================
# FEE CALCULATION STEPS  (fee_calculation.feature)
# ===========================================================================

@given(u'a transaction amount of "(?P<amount>[^"]*)"')
def step_set_amount(context, amount):
    context.amount = Decimal(amount)
    context.raised_exception = None
    context.calculated_fee = None


@when(u"I calculate the fee")
def step_calculate_fee(context):
    from fee_calculator import calculate_fee
    context.raised_exception = None
    context.calculated_fee = None
    try:
        context.calculated_fee = calculate_fee(context.amount)
    except Exception as e:
        context.raised_exception = e


@when(u"I calculate the fee for a float amount (?P<amount>[0-9.]+)")
def step_calculate_fee_float(context, amount):
    from fee_calculator import calculate_fee
    context.raised_exception = None
    context.calculated_fee = None
    try:
        context.calculated_fee = calculate_fee(float(amount))
    except Exception as e:
        context.raised_exception = e


@then(u'the fee should be "(?P<expected_fee>[^"]*)"')
def step_fee_should_be(context, expected_fee):
    assert context.raised_exception is None, f"Unexpected exception: {context.raised_exception}"
    expected = Decimal(expected_fee)
    actual = context.calculated_fee
    assert actual == expected, (
        f"Fee mismatch for amount {context.amount}:\n"
        f"  Expected: {expected}\n"
        f"  Got:      {actual}\n"
        "This is SN-04: int(amount * rate * 100) / 100 truncates instead of rounding.\n"
        "Fix: use (amount * _FEE_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)"
    )


@given(u"the sample transaction dataset")
def step_load_dataset(context):
    import json
    with open("data/sample_transactions.json") as f:
        data = json.load(f)
    context.dataset = data["transactions"]


@when(u"I calculate fees for all transactions")
def step_calculate_all_fees(context):
    from fee_calculator import calculate_fee
    context.fee_results = []
    for txn in context.dataset:
        amount = Decimal(str(txn["amount"]))
        expected = Decimal(str(txn["expected_fee"]))
        actual = calculate_fee(amount)
        context.fee_results.append({
            "transaction_id": txn["transaction_id"],
            "expected": expected,
            "actual": actual,
            "match": actual == expected,
        })


@then(u"at least (?P<threshold>[0-9]+) out of (?P<total>[0-9]+) transactions should have the correct fee")
def step_fee_accuracy_threshold(context, threshold, total):
    threshold = int(threshold)
    total = int(total)
    correct = sum(1 for r in context.fee_results if r["match"])
    wrong = [r for r in context.fee_results if not r["match"]]
    assert correct >= threshold, (
        f"Only {correct}/{total} transactions have the correct fee (threshold: {threshold}).\n"
        f"Wrong fees on {len(wrong)} transactions:\n" +
        "\n".join(
            f"  {r['transaction_id']}: expected={r['expected']} got={r['actual']}"
            for r in wrong[:10]
        ) +
        (f"\n  ... and {len(wrong) - 10} more" if len(wrong) > 10 else "") +
        "\nThis is SN-04: int() truncation is under-charging fees on fractional cent amounts."
    )


# ===========================================================================
# PIPELINE STEPS  (pipeline.feature)
# ===========================================================================

@given(u'the pipeline environment is configured with token "(?P<token>[^"]*)"')
def step_pipeline_env(context, token):
    os.environ["API_TOKEN"] = token
    os.environ["PIPELINE_API_TOKEN"] = token


@given(u'a pipeline transaction with id "(?P<txn_id>[^"]*)" amount "(?P<amount>[^"]*)" merchant "(?P<merchant_id>[^"]*)" token "(?P<token>[^"]*)"')
def step_pipeline_txn(context, txn_id, amount, merchant_id, token):
    context.pipeline_txn = {
        "transaction_id": txn_id,
        "amount": Decimal(amount),
        "merchant_id": merchant_id,
    }
    context.pipeline_token = token


@given(u"an incomplete pipeline transaction missing the merchant_id")
def step_pipeline_txn_missing_merchant(context):
    context.pipeline_txn = {
        "transaction_id": "TXN001",
        "amount": Decimal("500.00"),
    }
    context.pipeline_token = os.environ.get("API_TOKEN", "SECURE123TOKEN")


@when(u"I process the transaction through the pipeline")
def step_process_pipeline_txn(context):
    from pipeline import process_transaction
    with patch("audit_logger.call_procedure", return_value=None):
        context.pipeline_result = process_transaction(
            context.pipeline_txn, context.pipeline_token
        )


@then(u'the result status is "(?P<status>[^"]*)"')
def step_result_status(context, status):
    actual = context.pipeline_result.get("status")
    assert actual == status, f"Expected status '{status}' but got '{actual}'"


@then(u"the result contains a fee")
def step_result_has_fee(context):
    assert "fee" in context.pipeline_result, "Result does not contain a 'fee' key"
    assert context.pipeline_result["fee"] is not None, "Fee is None"


@then(u'the error message is "(?P<message>[^"]*)"')
def step_result_error_message(context, message):
    actual = context.pipeline_result.get("error")
    assert actual == message, f"Expected error '{message}' but got '{actual}'"


@given(u"the sample transaction dataset file")
def step_load_pipeline_dataset(context):
    context.dataset_file = "data/sample_transactions.json"


@when(u"I run the full pipeline")
def step_run_full_pipeline(context):
    import json
    from pipeline import process_transaction

    with open(context.dataset_file) as f:
        data = json.load(f)

    token = os.environ.get("API_TOKEN", "SECURE123TOKEN")
    context.pipeline_run_results = {}
    success = 0
    failed = 0

    with patch("audit_logger.call_procedure", return_value=None):
        for row in data["transactions"]:
            txn = {
                "transaction_id": row["transaction_id"],
                "amount": Decimal(str(row["amount"])),
                "merchant_id": row["merchant_id"],
            }
            txn_token = row.get("token", token)
            result = process_transaction(txn, txn_token)
            context.pipeline_run_results[row["transaction_id"]] = result
            if result["status"] == "SUCCESS":
                success += 1
            else:
                failed += 1

    context.pipeline_success_count = success
    context.pipeline_failed_count = failed
    context.pipeline_total_count = len(data["transactions"])


@then(u"the total transactions processed is (?P<total>[0-9]+)")
def step_pipeline_total(context, total):
    assert context.pipeline_total_count == int(total), (
        f"Expected {total} total transactions but got {context.pipeline_total_count}"
    )


@then(u"the number of successful transactions is (?P<count>[0-9]+)")
def step_pipeline_success_count(context, count):
    assert context.pipeline_success_count == int(count), (
        f"Expected {count} successes but got {context.pipeline_success_count}"
    )


@then(u"the number of failed transactions is (?P<count>[0-9]+)")
def step_pipeline_failed_count(context, count):
    assert context.pipeline_failed_count == int(count), (
        f"Expected {count} failures but got {context.pipeline_failed_count}"
    )


@then(u'transaction "(?P<txn_id>[^"]+)" has status "(?P<status>[^"]+)"')
def step_transaction_status(context, txn_id, status):
    result = context.pipeline_run_results.get(txn_id)
    assert result is not None, f"Transaction {txn_id} not found in pipeline results"
    assert result["status"] == status, (
        f"Expected {txn_id} to have status '{status}' but got '{result['status']}'"
    )
