"""
스도쿠 솔버 패키지

고급 논리 기법과 백트래킹을 사용하는 스도쿠 솔버입니다.

주요 클래스:
    SudokuBoard: 스도쿠 보드를 표현하는 클래스
    SudokuSolver: 스도쿠를 해결하는 클래스

주요 함수:
    load_from_string: 문자열로부터 스도쿠 로드
    load_from_file: 파일로부터 스도쿠 로드
    load_from_grid: 2D 리스트로부터 스도쿠 로드
"""

from .board import SudokuBoard
from .solver import SudokuSolver
from .utils import (
    load_from_string, 
    load_from_file, 
    load_from_grid,
    get_all_puzzles,
    get_puzzles_by_difficulty,
    get_available_difficulties,
    get_conflicting_cells
)

__all__ = [
    'SudokuBoard',
    'SudokuSolver',
    'load_from_string',
    'load_from_file',
    'load_from_grid',
    'get_all_puzzles',
    'get_puzzles_by_difficulty',
    'get_available_difficulties',
    'get_conflicting_cells',
]

