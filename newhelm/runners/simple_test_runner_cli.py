import os
from typing import Optional
import click
from newhelm.base_test import BasePromptResponseTest
from newhelm.command_line import (
    DATA_DIR_OPTION,
    MAX_TEST_ITEMS_OPTION,
    SUT_OPTION,
    newhelm_cli,
)
from newhelm.general import normalize_filename
from newhelm.runners.simple_test_runner import (
    run_prompt_response_test,
)
from newhelm.sut import PromptResponseSUT
from newhelm.sut_registry import SUTS
from newhelm.test_registry import TESTS


@newhelm_cli.command()
@click.option("--test", help="Which registered TEST to run.", required=True)
@SUT_OPTION
@DATA_DIR_OPTION
@MAX_TEST_ITEMS_OPTION
@click.option(
    "--output-file",
    help="If specified, will override the default location for outputting the TestRecord.",
)
@click.option(
    "--no-caching",
    is_flag=True,
    show_default=True,
    default=False,
    help="Disable caching.",
)
@click.option(
    "--no-progress-bar",
    is_flag=True,
    show_default=True,
    default=False,
    help="Disable displaying the 'Processing TestItems' progress bar.",
)
def run_test(
    test: str,
    sut: str,
    data_dir: str,
    max_test_items: int,
    output_file: Optional[str],
    no_caching: bool,
    no_progress_bar: bool,
):
    """Run the Test on the desired SUT and output the TestRecord."""
    test_obj = TESTS.make_instance(test)
    sut_obj = SUTS.make_instance(sut)
    # Current this only knows how to do prompt response, so assert that is what we have.
    assert isinstance(sut_obj, PromptResponseSUT)
    assert isinstance(test_obj, BasePromptResponseTest)

    if output_file is None:
        os.makedirs("output", exist_ok=True)
        output_file = os.path.join(
            "output", normalize_filename(f"record_for_{test}_{sut}.json")
        )
    test_record = run_prompt_response_test(
        test,
        test_obj,
        sut,
        sut_obj,
        data_dir,
        max_test_items,
        use_caching=not no_caching,
        disable_progress_bar=no_progress_bar,
    )
    with open(output_file, "w") as f:
        print(test_record.model_dump_json(indent=4), file=f)
    # For displaying to the screen, clear out the verbose test_item_records
    test_record.test_item_records = []
    print(test_record.model_dump_json(indent=4))
    print("Full TestRecord json written to", output_file)
