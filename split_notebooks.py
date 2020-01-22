#!/usr/bin/env python3
from os.path import join
import sys
from glob import glob
import copy
import re
from typing import Sequence, List, Dict, Callable, Any
from functools import partial
from operator import attrgetter
from operator import not_
import nbformat


# Types

MetadataT = Dict
CellT = Dict
NotebookT = Dict

UnaryFuncT = Callable[[Any], Any]

PredicateT = Callable[..., bool]
CellPredicateT = Callable[[CellT], bool]

SequenceTransformerT = Callable[[Sequence], Sequence]
MetadataTransformerT = Callable[[MetadataT], MetadataT]
CellTransformerT = Callable[[CellT], CellT]
NotebookTransformerT = Callable[[NotebookT], NotebookT]


# Functional basics

# Stdlib functions in this category: partial, attrgetter, itemgetter

def pipe(*funcs) -> UnaryFuncT:
    def _pipe(x):
        for f in funcs:
            x = f(x)
        return x
    return _pipe


def compose(*funcs) -> UnaryFuncT:
    def _compose(x):
        for f in reversed(funcs):
            x = f(x)
        return x
    return _compose


def always(value: Any) -> UnaryFuncT:
    def _always(arg):
        return value
    return _always


def negate(pred: PredicateT) -> PredicateT:
    return lambda x: not pred(x)


# Utilities for immutable object updates

def update_with(**newvalues) -> UnaryFuncT:
    def _update_with(obj):
        tmp = copy.copy(obj)
        tmp.update(newvalues)
        return tmp
    return _update_with


def map_with(**funcs) -> UnaryFuncT:
    def _map_with(obj):
        tmp = copy.copy(obj)
        for name, func in funcs.items():
            if name in obj:
                tmp[name] = func(obj[name])
        return tmp
    return _map_with


# Cell getters

def get_cell_tags(cell: CellT) -> List[str]:
    return cell.metadata.get("tags", [])


# Predicates

def cell_tags_include(tag: str) -> CellPredicateT:
    return lambda cell: tag in get_cell_tags(cell)


def cell_type_is(celltype: str) -> CellPredicateT:
    return lambda cell: cell.cell_type == celltype


def cell_type_is_code() -> CellPredicateT:
    return cell_type_is("code")


def cell_type_is_markdown() -> CellPredicateT:
    return cell_type_is("markdown")


# Utilities for generic filtering and mapping of notebooks

def filter_by(func: PredicateT) -> SequenceTransformerT:
    return partial(filter, func)


def filter_cells_by(func: PredicateT) -> NotebookTransformerT:
    return map_with(cells=compose(list, filter_by(func)))


def map_cells_with(func: CellTransformerT) -> NotebookTransformerT:
    return map_with(cells=compose(list, partial(map, func)))


def map_metadata_with(func: MetadataTransformerT) -> NotebookTransformerT:
    return map_with(metadata=func)


# Specific cell filters

def typed_cells(celltype: str) -> Callable[[NotebookT], List[CellT]]:
    return compose(
        partial(filter, cell_type_is(celltype)),
        attrgetter("cells")
    )


# Utilities for specific notebook transformations

clear_cell_transients = map_with(
    execution_count=always(None),
    outputs=always([])
)


def keep_cells_tagged(tag: str) -> NotebookTransformerT:
    return filter_cells_by(cell_tags_include(tag))


def drop_cells_tagged(tag: str) -> NotebookTransformerT:
    return filter_cells_by(negate(cell_tags_include(tag)))


# Utilities for specific notebook transformations

def notebook_without_transients(nb: NotebookT) -> NotebookT:
    return map_cells_with(clear_cell_transients)(nb)


def notebook_with_cleaned_metadata(nb: NotebookT) -> NotebookT:
    return map_with(metadata=map_with(celltoolbar=always(None)))(nb)


def notebook_with_solutions(nb: NotebookT) -> NotebookT:
    return drop_cells_tagged("nosolution")(nb)


def notebook_without_solutions(nb: NotebookT) -> NotebookT:
    return drop_cells_tagged("solution")(nb)


# Specific workflows

def count_initial_hashes(line: str) -> int:
    return len(re.split("[^#]", line, maxsplit=1)[0])


def check_ex_numbering(nb: NotebookT) -> None:
    print()
    for cell in typed_cells("markdown")(nb):
        # TODO: Use regex to get ex number and letter
        # and check that they're incremental.
        # Even better lets write back correct counts.
        if cell.source.startswith("#"):
            firstline = cell.source.split('\n')[0]
            level = count_initial_hashes(firstline)
            print(firstline, level)

        # if cell.source.startswith("### Ex"):
        #     print(cell.source.split('\n')[0])
        # if cell.source.startswith("#### Ex"):
        #     print(cell.source.split('\n')[0])
    print()


def process_notebook(
        filename: str,
        sol_filename: str,
        ex_filename: str
) -> None:
    # See nbformat.readthedocs.io for format specs
    notebook = nbformat.read(filename, nbformat.NO_CONVERT)

    # Strip things that change by running the notebook cells
    notebook = notebook_without_transients(notebook)

    # Write back  # TODO: Trigger this separately from cmdline
    nbformat.write(notebook, filename)

    # Remove cell tag bar etc. for public display
    notebook = notebook_with_cleaned_metadata(notebook)

    # Remove cells with hide tags
    notebook = drop_cells_tagged("hide")(notebook)

    # TODO: Skip unwanted sections
    # TODO: Renumber exercises

    check_ex_numbering(notebook)

    # Store with only solutions
    nbformat.write(notebook_with_solutions(notebook), sol_filename)

    # Store with only solutions
    nbformat.write(notebook_without_solutions(notebook), ex_filename)


def source_filenames() -> List[str]:
    return glob(join("sources", "sources-*.ipynb"))


def main(args: List[str]) -> int:
    filenames = args or source_filenames()
    for filename in filenames:
        assert filename.startswith("sources/sources-")

        basename = filename.replace("sources/sources-", "")
        sol_filename = join("solutions", "solutions-" + basename)
        ex_filename = join("exercises", "exercises-" + basename)

        process_notebook(filename, sol_filename, ex_filename)

        print("Read sources from {}".format(filename))
        print(" -> Wrote solutions to {}".format(sol_filename))
        print(" -> Wrote exercises to {}".format(ex_filename))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
