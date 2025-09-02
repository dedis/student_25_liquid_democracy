# bachelors-thesis

The benchmarks, as well as any graph creation and calculation of statistics can be run locally by re-running the corresponding python notebook in the folder [benchmarking](./benchmarking/). The results of these benchmarks can be found in [data](./data/). This data turned into figures can be found in the [figures folder of the thesis paper](./thesis_paper/figures/).

The three solvers are implemented in:
- Linear Systems Solver: [le.py](./le.py)
- Linear Programming Solver: [lp.py](./lp.py)
- Iterative SolveR: [iterative.py](./iterative.py)

Following files also contain relevant code:

- **[graph_tools.py](./graph_tools.py)** contains the preprocessing pipeline to turn any graph into a well-formed delegation graph, inlcuding the code that detects and collapses closed delegation cycles. It also contains other tools to work with graphs like a converters between graph representations (NetworkX graph -> dict-of-dict and dict-of-dict -> NetworkX graph) and a function that inverts edges in a dict-of-dicts graph to make them usable in the algorithms.

- **[graph_gen.py](./graph_gen.py)** contains a function that generates a random, well-formed delegation graph with between 0 and 3 delegations per nodes. This may be useful for benchmarking on synthetic delegation graphs, which *may* resemble realistic delegations.

- **[graph_vis.py](./graph_vis.py)** contains a function to visualize dict-of-dict delegation graphs with some neat features like coloring nodes blue if they are voters.

The final paper is here [main-final.pdf](./main_final.pdf), and the defense presentation here [thesis_presentation.pdf](./thesis-presentation.pdf). The latex codebase for it is here [thesis_paper](./thesis_paper/).