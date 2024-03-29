import pytest
from newhelm.annotation import Annotation
from newhelm.records import TestItemRecord
from newhelm.runners.simple_test_runner import run_prompt_response_test
from newhelm.single_turn_prompt_response import (
    PromptInteraction,
)
from newhelm.sut import SUTCompletion, SUTResponse
from newhelm.sut_capabilities import ProducesPerTokenLogProbabilities
from newhelm.test_decorator import newhelm_test
from tests.fake_annotator import FakeAnnotator
from tests.fake_sut import FakeSUT
from tests.fake_test import FakeTest, FakeTestResult, fake_test_item


def test_run_prompt_response_test_output(tmpdir):
    item_1 = fake_test_item("1")
    item_2 = fake_test_item("2")
    fake_measurement = {"some-measurement": 0.5}
    record = run_prompt_response_test(
        FakeTest(
            test_items=[item_1, item_2],
            annotators={"some-annotator": FakeAnnotator()},
            measurement=fake_measurement,
        ),
        FakeSUT(),
        tmpdir,
    )

    assert record.test_item_records == [
        TestItemRecord(
            test_item=item_1,
            interactions=[
                PromptInteraction(
                    prompt=item_1.prompts[0],
                    response=SUTResponse(completions=[SUTCompletion(text="1")]),
                )
            ],
            annotations={
                "some-annotator": Annotation(
                    module="tests.fake_annotator",
                    class_name="FakeAnnotation",
                    data={"sut_text": "1"},
                )
            },
            measurements=fake_measurement,
        ),
        TestItemRecord(
            test_item=item_2,
            interactions=[
                PromptInteraction(
                    prompt=item_2.prompts[0],
                    response=SUTResponse(completions=[SUTCompletion(text="2")]),
                )
            ],
            annotations={
                "some-annotator": Annotation(
                    module="tests.fake_annotator",
                    class_name="FakeAnnotation",
                    data={"sut_text": "2"},
                )
            },
            measurements=fake_measurement,
        ),
    ]
    assert record.result.to_instance() == FakeTestResult(count_test_items=2.0)


def test_run_prompt_response_test_caching(tmpdir):
    test_items = [fake_test_item("1")]
    fake_measurement = {"some-measurement": 0.5}
    annotator_1 = FakeAnnotator()
    sut_1 = FakeSUT()
    # First run is in empty directory
    record_1 = run_prompt_response_test(
        FakeTest(
            test_items=test_items,
            annotators={"some-annotator": annotator_1},
            measurement=fake_measurement,
        ),
        sut_1,
        tmpdir,
    )
    assert sut_1.evaluate_calls == 1
    assert annotator_1.annotate_test_item_calls == 1
    # Second run should be fully cached
    annotator_2 = FakeAnnotator()
    sut_2 = FakeSUT()
    record_2 = run_prompt_response_test(
        FakeTest(
            test_items=test_items,
            annotators={"some-annotator": annotator_2},
            measurement=fake_measurement,
        ),
        sut_2,
        tmpdir,
    )
    assert sut_2.evaluate_calls == 0
    assert annotator_2.annotate_test_item_calls == 0
    # Fields like timestamp and initialization differ, so ignore them.
    assert record_1.test_item_records == record_2.test_item_records
    assert record_1.result == record_2.result


def test_run_prompt_response_test_ignore_caching(tmpdir):
    test_items = [fake_test_item("1")]
    fake_measurement = {"some-measurement": 0.5}
    annotator_1 = FakeAnnotator()
    sut_1 = FakeSUT()
    # First run is in empty directory, turn off caching.
    record_1 = run_prompt_response_test(
        FakeTest(
            test_items=test_items,
            annotators={"some-annotator": annotator_1},
            measurement=fake_measurement,
        ),
        sut_1,
        tmpdir,
        use_caching=False,
    )
    assert sut_1.evaluate_calls == 1
    assert annotator_1.annotate_test_item_calls == 1
    # Second run even with the same objects should call again.
    record_2 = run_prompt_response_test(
        FakeTest(
            test_items=test_items,
            annotators={"some-annotator": annotator_1},
            measurement=fake_measurement,
        ),
        sut_1,
        tmpdir,
    )
    assert sut_1.evaluate_calls == 2
    assert annotator_1.annotate_test_item_calls == 2
    # Fields like timestamp and initialization differ, so ignore them.
    assert record_1.test_item_records == record_2.test_item_records
    assert record_1.result == record_2.result


def test_run_prompt_response_test_max_test_items(tmpdir):
    # Lots of test items
    test_items = [fake_test_item(str(i)) for i in range(100)]
    fake_measurement = {"some-measurement": 0.5}
    record = run_prompt_response_test(
        FakeTest(
            test_items=test_items,
            annotators={"some-annotator": FakeAnnotator()},
            measurement=fake_measurement,
        ),
        FakeSUT(),
        tmpdir,
        # Limit to just 3 test items
        max_test_items=3,
    )
    assert len(record.test_item_records) == 3
    assert record.result.to_instance() == FakeTestResult(count_test_items=3.0)


def test_run_prompt_response_test_max_test_items_zero(tmpdir):
    # Lots of test items
    test_items = [fake_test_item(str(i)) for i in range(100)]
    with pytest.raises(AssertionError) as err_info:
        run_prompt_response_test(
            FakeTest(
                test_items=test_items,
                annotators={"some-annotator": FakeAnnotator()},
                measurement={},
            ),
            FakeSUT(),
            tmpdir,
            max_test_items=0,
        )
    assert str(err_info.value) == "Cannot run a test using 0."


def test_run_prompt_response_test_sut_exception(tmpdir):
    item_1 = fake_test_item("1")
    fake_measurement = {"some-measurement": 0.5}
    sut = FakeSUT()

    def _raise_exception(*args, **kwargs):
        raise Exception("some-exception")

    sut.evaluate = _raise_exception

    with pytest.raises(Exception) as err_info:
        run_prompt_response_test(
            FakeTest(
                test_items=[item_1],
                annotators={"some-annotator": FakeAnnotator()},
                measurement=fake_measurement,
            ),
            sut,
            tmpdir,
        )
    err_text = str(err_info.value)
    assert "SUT request `text='1' num_completions=1`" in err_text
    assert "TestItem `prompts=[PromptWithContext(" in err_text
    # Ensure it forwards the original issue
    assert str(err_info.value.__cause__) == "some-exception"


def test_run_prompt_response_test_annotator_exception(tmpdir):
    item_1 = fake_test_item("1")
    fake_measurement = {"some-measurement": 0.5}
    annotator = FakeAnnotator()

    def _raise_exception(*args, **kwargs):
        raise Exception("some-exception")

    annotator.annotate_test_item = _raise_exception

    with pytest.raises(Exception) as err_info:
        run_prompt_response_test(
            FakeTest(
                test_items=[item_1],
                annotators={"some-annotator": annotator},
                measurement=fake_measurement,
            ),
            FakeSUT(),
            tmpdir,
        )
    err_text = str(err_info.value)
    assert "Exception while handling annotation for some-annotator" in err_text
    assert (
        "SUTResponse(completions=[SUTCompletion(text='1', top_logprobs=None)]"
        in err_text
    )
    assert str(err_info.value.__cause__) == "some-exception"


class NotATestOrSut:
    pass


def test_run_prompt_response_test_invalid_test(tmpdir):
    with pytest.raises(AssertionError) as err_info:
        run_prompt_response_test(
            NotATestOrSut(),
            FakeSUT(),
            tmpdir,
        )
    assert (
        str(err_info.value) == "NotATestOrSut should be decorated with @newhelm_test."
    )


def test_run_prompt_response_test_invalid_sut(tmpdir):
    with pytest.raises(AssertionError) as err_info:
        run_prompt_response_test(
            FakeTest(),
            NotATestOrSut(),
            tmpdir,
        )
    assert str(err_info.value) == "NotATestOrSut should be decorated with @newhelm_sut."


@newhelm_test(requires_sut_capabilities=[ProducesPerTokenLogProbabilities])
class FakeTestWithReqs(FakeTest):
    pass


def test_run_prompt_response_test_missing_capabilities(tmpdir):
    with pytest.raises(AssertionError) as err_info:
        run_prompt_response_test(
            FakeTestWithReqs(),
            FakeSUT(),
            tmpdir,
        )
    assert "Test test-uid cannot run on fake-sut" in str(err_info.value)
    assert "ProducesPerTokenLogProbabilities" in str(err_info.value)
