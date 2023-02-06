# Incomplete Debug Information

This repository is the future home of a framework for testing compiler toolchains for *completeness bugs* in debug information. 

The framework can find implementation defects in compilers toolchains that lead to the *unavailability* of source-level variables during symbolic debugging of optimized code. It generates synthetic programs and tests them against three conjectures on the expected availability of debug information: when a violation is detected, the framework can triage the bug by pinpointing the clang or gcc optimization(s) that is most likely behind the issue.

The methodology behind the framework is described in the paper [*Where Did My Variable Go? Poking Holes in Incomplete Debug Information*](https://arxiv.org/abs/2211.09568) that will appear in the [ASPLOS '23](https://asplos-conference.org/) conference. The code will be released by the conference start date.

#### Cite
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
