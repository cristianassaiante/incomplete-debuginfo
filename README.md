# Incomplete Debug Information

This repository is the future home of a framework for testing compiler toolchains for *completeness bugs* in debug information. 

The framework can find implementation defects in compilers toolchains that lead to the *unavailability* of source-level variables during symbolic debugging of optimized code. It generates synthetic programs and tests them against three conjectures on the expected availability of debug information: when a violation is detected, the framework can triage the bug by pinpointing the clang or gcc optimization(s) that is most likely behind the issue.

The methodology behind the framework is described in the paper [*Where Did My Variable Go? Poking Holes in Incomplete Debug Information*](https://arxiv.org/XXX) that will appear in the [ASPLOS '23](https://asplos-conference.org/) conference. The code will be released by the conference start date.

#### Cite
To reference our work, we would be grateful if you could use the following BibTeX code:

```
@inproceedings{incomplete-debuginfo,
    author = {Assaiante, Cristian and D'Elia, Daniele Cono and Di Luna, Giuseppe Antonio and Querzoni, Leonardo},
    title = {Where Did My Variable Go? Poking Holes in Incomplete Debug Information},
    year = {2023},
    publisher = {Association for Computing Machinery},
    booktitle = {Proceedings of the 28th ACM International Conference on Architectural Support for Programming Languages and Operating Systems},
    location = {Vancouver, Canada},
    series = {ASPLOS '23},
}
```