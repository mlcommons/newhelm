from typing import List
from newhelm.benchmark import BaseBenchmark
from newhelm.load_plugins import load_plugins
from newhelm.general import get_concrete_subclasses, get_or_create_json_file, to_json
from newhelm.plugins.runners.simple_benchmark_runner import SimpleBenchmarkRunner
from newhelm.sut import SUT
from newhelm.sut_registry import SUTS


if __name__ == "__main__":
    load_plugins()
    all_benchmarks: List[BaseBenchmark] = [
        cls() for cls in get_concrete_subclasses(BaseBenchmark)  # type: ignore[type-abstract]
    ]
    all_suts: List[SUT] = [sut.make_instance() for _, sut in SUTS.items()]
    secrets_dict = get_or_create_json_file("secrets", "default.json")
    runner = SimpleBenchmarkRunner("run_data", secrets_dict)
    for benchmark in all_benchmarks:
        print("\n\nStarting:", benchmark.__class__.__name__)
        benchmark_records = runner.run(benchmark, all_suts)
        for record in benchmark_records:
            # make it print pretty
            print(to_json(record, indent=4))
