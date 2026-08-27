from sample_puzzles import UNIQUE_SOLUTION, grid_from_string

from sudoku.board import Puzzle
from sudoku.solve_types import SolveStatus, StepKind
from sudoku.solver import SudokuSolver

REFUTATION_THEN_SOLUTION = (
    "48.3............71.2.......7.5....6....2..8.............1.76...3.....4......5...."
)
ALL_BRANCHES_STALL = (
    "078100000400030000003500007090000100700801005006000020600002900000050006000009350"
)


def test_refutation_removes_the_proven_candidate() -> None:
    result = SudokuSolver(Puzzle(grid_from_string(REFUTATION_THEN_SOLUTION))).solve()
    refutation = next(step for step in result.steps if step.kind is StepKind.REFUTATION)
    contradictions = tuple(
        step for step in result.steps if step.kind is StepKind.CONTRADICTION
    )

    assert result.status is SolveStatus.SOLVED_UNIQUE
    assert contradictions
    assert all(step.contradiction is not None for step in contradictions)
    assert refutation.assumption is not None
    row, col = refutation.assumption.cell
    assert refutation.assumption.value not in refutation.candidates[row][col]
    assert StepKind.SEARCH_FALLBACK not in {step.kind for step in result.steps}


def test_all_stalled_assumptions_trigger_search_fallback() -> None:
    result = SudokuSolver(Puzzle(grid_from_string(ALL_BRANCHES_STALL))).solve()
    kinds = [step.kind for step in result.steps]
    assert kinds.count(StepKind.ASSUMPTION) == kinds.count(StepKind.ASSUMPTION_STALLED)
    assert StepKind.ASSUMPTION in kinds
    assert StepKind.REFUTATION not in kinds
    assert StepKind.SEARCH_FALLBACK in kinds
    assert kinds[-1] is StepKind.SOLVED
    assert max(step.depth for step in result.steps) == 1


def test_assumption_solution_is_still_checked_for_a_second_solution() -> None:
    grid = [list(row) for row in UNIQUE_SOLUTION]
    for row, col in ((0, 3), (0, 4), (3, 3), (3, 4)):
        grid[row][col] = 0

    result = SudokuSolver(Puzzle(grid)).solve()
    kinds = [step.kind for step in result.steps]
    branch_solution = next(
        step.grid for step in result.steps if step.kind is StepKind.ASSUMPTION_SOLVED
    )

    assert StepKind.ASSUMPTION_SOLVED in kinds
    assert StepKind.SEARCH_FALLBACK not in kinds
    assert result.status is SolveStatus.SOLVED_MULTIPLE
    assert result.solution == branch_solution == result.steps[-1].grid
