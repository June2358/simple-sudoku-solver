"""
스도쿠 해결 기법 모듈

다양한 스도쿠 해결 기법을 구현합니다:
- Naked/Hidden Singles
- Locked Candidates (Pointing & Claiming)
- Naked/Hidden Subsets (Pairs, Triples, Quads)
"""

from typing import List, Tuple
from itertools import combinations
from .board import SudokuBoard


def get_all_units(board: SudokuBoard) -> List[List[Tuple[int, int]]]:
    """모든 유닛(행, 열, 박스)의 셀 좌표 리스트 반환"""
    units = []
    
    # 행들
    for i in range(board.SIZE):
        units.append([(i, j) for j in range(board.SIZE)])
    
    # 열들
    for j in range(board.SIZE):
        units.append([(i, j) for i in range(board.SIZE)])
    
    # 박스들
    for box_row in range(0, board.SIZE, board.BOX_SIZE):
        for box_col in range(0, board.SIZE, board.BOX_SIZE):
            box = []
            for i in range(box_row, box_row + board.BOX_SIZE):
                for j in range(box_col, box_col + board.BOX_SIZE):
                    box.append((i, j))
            units.append(box)
    
    return units


def apply_naked_singles(board: SudokuBoard, steps: List[str]) -> bool:
    """
    Naked Single: 각 칸의 후보가 1개뿐이면 확정
    한 번에 모든 Naked Single을 찾아서 처리
    """
    found_any = False
    filled_cells = []
    
    # 먼저 모든 Naked Single 찾기
    for i in range(board.SIZE):
        for j in range(board.SIZE):
            if board.board[i][j] == 0:
                candidates = board.get_candidates(i, j)
                if len(candidates) == 1:
                    value = list(candidates)[0]
                    filled_cells.append((i, j, value))
    
    # 찾은 모든 Naked Single을 한 번에 처리
    for i, j, value in filled_cells:
        if board.board[i][j] == 0:  # 아직 채워지지 않았는지 확인
            if board.set_value(i, j, value):
                steps.append(f"Naked Single: ({i+1},{j+1}) = {value}")
                found_any = True
    
    return found_any


def apply_hidden_singles(board: SudokuBoard, steps: List[str]) -> bool:
    """
    Hidden Single: 유닛(행/열/박스) 내에서 특정 숫자가 들어갈 수 있는 위치가 1개뿐이면 확정
    한 번에 모든 Hidden Single을 찾아서 처리
    """
    units = get_all_units(board)
    unit_names = []
    # 행 이름
    for i in range(9):
        unit_names.append(f"행 {i+1}")
    # 열 이름
    for j in range(9):
        unit_names.append(f"열 {j+1}")
    # 박스 이름
    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            box_num = (box_row // 3) * 3 + (box_col // 3) + 1
            unit_names.append(f"박스 {box_num}")
    
    found_any = False
    filled_cells = []  # (row, col, digit, unit_name) 튜플 리스트
    
    # 먼저 모든 Hidden Single 찾기
    for unit, unit_name in zip(units, unit_names):
        for digit in range(1, 10):
            count = 0
            cell_position = None
            
            for r, c in unit:
                if board.board[r][c] == 0 and digit in board.get_candidates(r, c):
                    count += 1
                    cell_position = (r, c)
            
            if count == 1 and cell_position:
                r, c = cell_position
                if board.board[r][c] == 0:  # 아직 채워지지 않았는지 확인
                    filled_cells.append((r, c, digit, unit_name))
    
    # 찾은 모든 Hidden Single을 한 번에 처리
    for r, c, digit, unit_name in filled_cells:
        if board.board[r][c] == 0:  # 아직 채워지지 않았는지 확인 (중복 방지)
            if board.set_value(r, c, digit):
                steps.append(f"Hidden Single ({unit_name}): ({r+1},{c+1}) = {digit}")
                found_any = True
    
    return found_any


def apply_locked_candidates(board: SudokuBoard, steps: List[str]) -> bool:
    """
    Locked Candidates (Pointing & Claiming 통합)
    """
    progress = False
    
    # Type 1: Pointing (Box-to-Line)
    for box_row in range(0, board.SIZE, board.BOX_SIZE):
        for box_col in range(0, board.SIZE, board.BOX_SIZE):
            for num in range(1, 10):
                positions = []
                for i in range(box_row, box_row + board.BOX_SIZE):
                    for j in range(box_col, box_col + board.BOX_SIZE):
                        if board.board[i][j] == 0 and num in board.get_candidates(i, j):
                            positions.append((i, j))
                
                if len(positions) >= 2:
                    rows = set(pos[0] for pos in positions)
                    if len(rows) == 1:
                        row = list(rows)[0]
                        for j in range(board.SIZE):
                            if j < box_col or j >= box_col + board.BOX_SIZE:
                                if num in board.candidates[row][j]:
                                    board.candidates[row][j].discard(num)
                                    progress = True
                    
                    cols = set(pos[1] for pos in positions)
                    if len(cols) == 1:
                        col = list(cols)[0]
                        for i in range(board.SIZE):
                            if i < box_row or i >= box_row + board.BOX_SIZE:
                                if num in board.candidates[i][col]:
                                    board.candidates[i][col].discard(num)
                                    progress = True
    
    # Type 2: Claiming (Line-to-Box)
    for i in range(board.SIZE):
        for num in range(1, 10):
            positions = []
            for j in range(board.SIZE):
                if board.board[i][j] == 0 and num in board.get_candidates(i, j):
                    positions.append((i, j))
            
            if len(positions) >= 2:
                boxes = set((r // 3, c // 3) for r, c in positions)
                if len(boxes) == 1:
                    box_r, box_c = list(boxes)[0]
                    for r in range(box_r * 3, box_r * 3 + 3):
                        if r != i:
                            for c in range(box_c * 3, box_c * 3 + 3):
                                if num in board.candidates[r][c]:
                                    board.candidates[r][c].discard(num)
                                    progress = True
    
    for j in range(board.SIZE):
        for num in range(1, 10):
            positions = []
            for i in range(board.SIZE):
                if board.board[i][j] == 0 and num in board.get_candidates(i, j):
                    positions.append((i, j))
            
            if len(positions) >= 2:
                boxes = set((r // 3, c // 3) for r, c in positions)
                if len(boxes) == 1:
                    box_r, box_c = list(boxes)[0]
                    for c in range(box_c * 3, box_c * 3 + 3):
                        if c != j:
                            for r in range(box_r * 3, box_r * 3 + 3):
                                if num in board.candidates[r][c]:
                                    board.candidates[r][c].discard(num)
                                    progress = True
    
    return progress


def apply_naked_subsets(board: SudokuBoard, steps: List[str], N: int) -> bool:
    """
    Naked Subsets: N개의 셀이 정확히 N개의 후보 숫자의 부분 집합으로만 이루어진 경우
    """
    for unit in get_all_units(board):
        empty_cells = [(r, c) for r, c in unit if board.board[r][c] == 0]
        
        if len(empty_cells) < N:
            continue
        
        for cell_combination in combinations(empty_cells, N):
            union_candidates = set()
            for r, c in cell_combination:
                union_candidates.update(board.get_candidates(r, c))
            
            if len(union_candidates) == N:
                for other_cell in unit:
                    if other_cell not in cell_combination and board.board[other_cell[0]][other_cell[1]] == 0:
                        old_size = len(board.candidates[other_cell[0]][other_cell[1]])
                        board.candidates[other_cell[0]][other_cell[1]] -= union_candidates
                        if len(board.candidates[other_cell[0]][other_cell[1]]) < old_size:
                            subset_name = {2: "Pairs", 3: "Triples", 4: "Quads"}.get(N, f"{N}-tuple")
                            steps.append(f"Naked {subset_name}: {sorted(union_candidates)} in {cell_combination}")
                            return True
    return False


def apply_hidden_subsets(board: SudokuBoard, steps: List[str], N: int) -> bool:
    """
    Hidden Subsets: N개의 숫자가 오직 N개의 셀에만 나타나는 경우
    """
    for unit in get_all_units(board):
        digit_map = {}
        for r, c in unit:
            if board.board[r][c] == 0:
                for digit in board.get_candidates(r, c):
                    if digit not in digit_map:
                        digit_map[digit] = []
                    digit_map[digit].append((r, c))
        
        for digit_combination in combinations(range(1, 10), N):
            union_cells = set()
            for digit in digit_combination:
                if digit in digit_map:
                    union_cells.update(digit_map[digit])
            
            if len(union_cells) == N:
                digit_set = set(digit_combination)
                for r, c in union_cells:
                    old_candidates = board.candidates[r][c].copy()
                    # 교집합만 남김 (기존 후보에서 digit_set에 없는 것만 제거, 새로운 후보 추가 안 함)
                    new_candidates = old_candidates & digit_set
                    if new_candidates != old_candidates:
                        board.candidates[r][c] = new_candidates
                        subset_name = {2: "Pairs", 3: "Triples", 4: "Quads"}.get(N, f"{N}-tuple")
                        steps.append(f"Hidden {subset_name}: {sorted(digit_combination)} in {sorted(union_cells)}")
                        return True
    return False


