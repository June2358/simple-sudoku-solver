"""
스도쿠 유틸리티 모듈

스도쿠 보드를 다양한 형식에서 로드하는 함수와 퍼즐 데이터를 제공합니다.
"""

import json
import os
from typing import List, Dict, Tuple
from .board import SudokuBoard

# ============================================================================
# 보드 로드 함수
# ============================================================================

def load_from_string(s: str) -> SudokuBoard:
    """
    문자열로부터 스도쿠 판 로드
    형식: 숫자는 그대로, 빈 칸은 0 또는 . 또는 공백
    예: "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79"
    """
    # 공백과 줄바꿈 제거
    s = ''.join(s.split())
    # .을 0으로 변환
    s = s.replace('.', '0')
    
    expected_length = SudokuBoard.SIZE * SudokuBoard.SIZE
    if len(s) != expected_length:
        raise ValueError(f"입력 문자열 길이가 {expected_length}이 아닙니다: {len(s)}")
    
    board = []
    for i in range(SudokuBoard.SIZE):
        row = []
        for j in range(SudokuBoard.SIZE):
            char = s[i * SudokuBoard.SIZE + j]
            if char.isdigit():
                row.append(int(char))
            else:
                row.append(0)
        board.append(row)
    
    return SudokuBoard(board)


def load_from_file(filename: str) -> SudokuBoard:
    """파일로부터 스도쿠 판 로드"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    return load_from_string(content)


def load_from_grid(grid: List[List[int]]) -> SudokuBoard:
    """2D 리스트로부터 스도쿠 판 로드"""
    return SudokuBoard(grid)


# ============================================================================
# 퍼즐 데이터 함수
# ============================================================================

# JSON 파일 경로
_PUZZLES_FILE = os.path.join(os.path.dirname(__file__), 'puzzles.json')

# 캐시된 퍼즐 데이터
_puzzles_cache: Dict[str, List[List[List[int]]]] = None


def _load_puzzles() -> Dict[str, List[List[List[int]]]]:
    """JSON 파일에서 퍼즐 데이터 로드"""
    global _puzzles_cache
    if _puzzles_cache is None:
        try:
            with open(_PUZZLES_FILE, 'r', encoding='utf-8') as f:
                _puzzles_cache = json.load(f)
        except FileNotFoundError:
            # 파일이 없으면 빈 딕셔너리 반환
            _puzzles_cache = {}
    return _puzzles_cache


def get_all_puzzles() -> List[List[List[int]]]:
    """모든 난이도의 퍼즐을 하나의 리스트로 반환"""
    all_puzzles = []
    puzzles_dict = _load_puzzles()
    for puzzles in puzzles_dict.values():
        all_puzzles.extend(puzzles)
    return all_puzzles


def get_puzzles_by_difficulty(difficulty: str) -> List[List[List[int]]]:
    """
    특정 난이도의 퍼즐 리스트 반환
    
    Args:
        difficulty: 난이도 ("쉬움", "보통", "어려움", "전문가", "마스터", "극한")
    
    Returns:
        해당 난이도의 퍼즐 리스트
    """
    puzzles_dict = _load_puzzles()
    return puzzles_dict.get(difficulty, [])


def get_available_difficulties() -> List[str]:
    """사용 가능한 난이도 목록 반환"""
    puzzles_dict = _load_puzzles()
    return list(puzzles_dict.keys())


# ============================================================================
# 보드 검증 함수
# ============================================================================

def get_conflicting_cells(board: List[List[int]]) -> List[Tuple[int, int]]:
    """
    스도쿠 보드에서 모순이 있는 셀들을 찾아서 반환
    
    Args:
        board: 9x9 리스트 (0은 빈 칸)
    
    Returns:
        모순이 있는 셀의 (row, col) 좌표 리스트
    """
    conflicting = []
    grid_size = SudokuBoard.SIZE
    box_size = SudokuBoard.BOX_SIZE
    
    # 각 셀에 대해 같은 행/열/박스에 중복된 숫자가 있는지 확인
    for i in range(grid_size):
        for j in range(grid_size):
            val = board[i][j]
            if val == 0:
                continue
            
            # 같은 행에서 중복 확인
            row_conflict = False
            for c in range(grid_size):
                if c != j and board[i][c] == val:
                    row_conflict = True
                    break
            
            # 같은 열에서 중복 확인
            col_conflict = False
            for r in range(grid_size):
                if r != i and board[r][j] == val:
                    col_conflict = True
                    break
            
            # 같은 박스에서 중복 확인
            box_conflict = False
            box_row = (i // box_size) * box_size
            box_col = (j // box_size) * box_size
            for r in range(box_row, box_row + box_size):
                for c in range(box_col, box_col + box_size):
                    if (r != i or c != j) and board[r][c] == val:
                        box_conflict = True
                        break
                if box_conflict:
                    break
            
            # 모순이 있으면 추가
            if row_conflict or col_conflict or box_conflict:
                conflicting.append((i, j))
    
    return conflicting
