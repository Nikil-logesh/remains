import io
import json

from app.batch import process_jsonl
from app.financial import FinancialDataset, lookup_financial_record


def test_financial_lookup_streams_and_preserves_zero(tmp_path):
    path = tmp_path / "financial.jsonl.txt"
    path.write_text(
        '{"organisation_number":"984851006","name":"Test AS","employees":0}\n',
        encoding="utf-8",
    )
    record, line = lookup_financial_record(path, "984 851 006")
    assert record["employees"] == 0
    assert line == 1
    assert FinancialDataset(path).lookup("984851007") == (None, None)


def test_batch_emits_one_fail_closed_envelope_per_input(tmp_path):
    dataset = tmp_path / "financial.jsonl"
    dataset.write_text(
        '{"organisation_number":"984851006","name":"Test AS","employees":0}\n',
        encoding="utf-8",
    )
    output = io.StringIO()
    count = process_jsonl(
        io.StringIO(
            '{"organisation_number":"984851006"}\n'
            '{"organisation_number":"123"}\n'
            'not-json\n'
        ),
        output,
        financial_dataset=dataset,
        run_id="test-run",
    )
    rows = [json.loads(line) for line in output.getvalue().splitlines()]
    assert count == len(rows) == 3
    assert rows[0]["terminal_status"] == "completed"
    assert rows[0]["claims"][0]["value"] == "Test AS"
    assert rows[1]["terminal_status"] == "failed"
    assert rows[2]["terminal_status"] == "failed"
    assert rows[0]["evidence"][0]["content_sha256"]


def test_batch_rejects_bad_checksum(tmp_path):
    output = io.StringIO()
    process_jsonl(
        io.StringIO('{"organisation_number":"984851007"}\n'),
        output,
        run_id="checksum-test",
    )
    row = json.loads(output.getvalue())
    assert row["terminal_status"] == "failed"
    assert row["errors"][0]["code"] == "invalid_organisation_number"


def test_batch_preserves_each_non_empty_input_row_and_abstains(tmp_path):
    output = io.StringIO()
    inputs = [
        '{"organisation_number":"984851006","label":"first"}',
        '{"organisation_number":"984851007","label":"second"}',
        'not-json',
    ]
    count = process_jsonl(io.StringIO("\n".join(inputs) + "\n"), output, run_id="contract")
    rows = [json.loads(line) for line in output.getvalue().splitlines()]
    assert count == len(rows) == len(inputs)
    assert [row["input"] for row in rows[:2]] == [
        {"organisation_number": "984851006", "label": "first"},
        {"organisation_number": "984851007", "label": "second"},
    ]
    assert rows[0]["claims"][0]["availability"] == "not_applicable"
    assert rows[0]["claims"][0]["value"] is None
    assert rows[2]["claims"][0]["availability"] == "failed"
    assert rows[2]["input"] == "not-json"
