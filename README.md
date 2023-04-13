# Incomplete Debug Information

This repository is the home of a framework for testing compiler toolchains for *completeness bugs* in debug information. 

The framework can find implementation defects in compiler toolchains that lead to the *unavailability* of source-level variables during symbolic debugging of optimized code. It generates synthetic programs and tests them against three conjectures on the expected availability of debug information: when a violation is detected, the framework can triage the bug by pinpointing the clang or gcc optimization(s) that is most likely behind the issue.

The methodology behind the framework is described in the paper [*Where Did My Variable Go? Poking Holes in Incomplete Debug Information*](https://dl.acm.org/doi/10.1145/3575693.3575720) that will appear in the [ASPLOS '23](https://asplos-conference.org/) conference.

## Framework

Our testing framework for finding completeness bugs in modern compiler toolchains is a pipeline made of the following stages:

### Testcase Generation and Debug Tracing

The testcase generation stage is built on top of `csmith`. It generates synthetic programs using random seeds, and the seeds are also used to select a random set of customization arguments from a selected pool of csmith flags. Once the synthetic programs are generated, these are compiled at different optimizations levels with `gcc` and `clang`, and eventually multiple versions of them that can be provided by the user via command line arguments.

The compiled programs are then run within debuggers (`gdb` for `gcc` compiled program and `lldb` for `clang` compiled programs) and for each stepped source line, we store the set of available variables (i.e., with shown value) during debugging.

### Conjecture Checking

The conjecture checking stage analyzes the debug traces previously computed looking for violations of the conjectures. For each violation, we store information (e.g., source line, involved variables) to identify it and later triage it more easily and in an automated way.

### Bug Triaging

The bug triaging stage is used to reduce to minimum the number of duplicated bugs that one may report. To do so, we identify the optimization pass(es) that are most likely to be the root cause behind incomplete debug information. Here, we follow two different approaches for each compiler:

- `clang`: we run a binary search algorithm using the `--opt-bisect-limit` flag that enable the user to stop the optimization pipeline at a given point;
- `gcc`: we extracted the optimization flags enabled at each optimization level, and we remove them one-by-one, checking where the violation is not present anymore.

### Example

We provide to the users 3 bash scripts to easily run a bug finding session.

- `./generate_and_trace.sh N <--metrics>`: it generates N testcases, compiles them at different optimization levels in both gcc and clang, and extracts from debugging runs the variables available at each source line that can be stepped; eventually it can also compute the incompleteness metrics defined in the paper.

- `./conjecture_checking.sh`: it analyzes the debug traces and checks whether the conjectures are violated; for conjecture 1, the first run also injects the unoptimizable function call as described in the paper.

- `./pass_discovery.sh`: it tries to find the culprit optimization pass(es) for each conjecture violation previously found (it may not work on older compiler version since we have tested it only with the trunk version used in our evalution experiments).

The following dependencies are needed to run the scripts:
```
python3 csmith compcert gcc clang gdb lldb llvm
```

If you want to customize these scripts (e.g., by enabling multiprocess computations), each python script has its own documentation available with the `--help` flag.

### Test your own Conjectures

We provide to the users a [template file](conjecture-checking/template.py) for writing their own conjecture checkers.
Feel free to use it to test your ideas and make a pull request if you think that it can be helpful for improving the framework.

In order to run the pass discovery you need to write an online version of the checker too, i.e., a checker that takes the source code, compiles it, runs it within a debugger and returns the conjecture violations. We provide a [template](pass-discovery/checkers.py#L218) for it too. Last, you need to add the new checker in the dictionaries in both the [clang pass discovery script](pass-discovery/clang_pass_discovery.py#L34) and in the [gcc pass discovery script](pass-discovery/gcc_pass_discovery.py#L30).

## Cite
To reference our work, we would be grateful if you could use the following BibTeX code:

```
@inproceedings{10.1145/3575693.3575720,
    author = {Assaiante, Cristian and D'Elia, Daniele Cono and Di Luna, Giuseppe Antonio and Querzoni, Leonardo},
    title = {Where Did My Variable Go? Poking Holes in Incomplete Debug Information},
    year = {2023},
    isbn = {9781450399166},
    publisher = {Association for Computing Machinery},
    address = {New York, NY, USA},
    url = {https://doi.org/10.1145/3575693.3575720},
    doi = {10.1145/3575693.3575720},
    booktitle = {Proceedings of the 28th ACM International Conference on Architectural Support for Programming Languages and Operating Systems, Volume 2},
    pages = {935–947},
    numpages = {13},
    keywords = {compiler optimizations, compiler bugs, Debuggers},
    location = {Vancouver, BC, Canada},
    series = {ASPLOS 2023}
}
```
