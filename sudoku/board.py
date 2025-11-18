"""
스도쿠 보드 모듈

스도쿠 보드를 표현하고 관리하는 클래스를 제공합니다.
후보 추적, 제약 조건 전파 등의 기능을 포함합니다.
"""

from typing import List, Optional, Set, Tuple
from copy import deepcopy


class SudokuBoard:
    """스도쿠 판을 표현하는 클래스"""
    
    SIZE = 9
    BOX_SIZE = 3
    
    def __init__(self, board: Optional[List[List[int]]] = None):
        """
        Args:
            board: 9x9 리스트. 0은 빈 칸을 의미
        """
        if board is None:
            self.board = [[0] * self.SIZE for _ in range(self.SIZE)]
        else:
            self.board = deepcopy(board)
        
        # 각 칸의 가능한 숫자 후보를 저장 (제약 조건 전파용)
        self.candidates = [[set(range(1, 10)) for _ in range(self.SIZE)] 
                          for _ in range(self.SIZE)]
        self._initialize_candidates()
    
    def _initialize_candidates(self):
        """이미 채워진 숫자에 따라 후보 초기화"""
        for i in range(self.SIZE):
            for j in range(self.SIZE):
                if self.board[i][j] != 0:
                    self.candidates[i][j] = {self.board[i][j]}
                    self._remove_candidate_from_peers(i, j, self.board[i][j])
    
    def _remove_candidate_from_peers(self, row: int, col: int, value: int):
        """특정 칸의 숫자가 정해지면, 같은 행/열/박스의 다른 칸에서 해당 숫자 제거"""
        # 같은 행
        for c in range(self.SIZE):
            if c != col and value in self.candidates[row][c]:
                self.candidates[row][c].discard(value)
        
        # 같은 열
        for r in range(self.SIZE):
            if r != row and value in self.candidates[r][col]:
                self.candidates[r][col].discard(value)
        
        # 같은 박스
        box_row = (row // self.BOX_SIZE) * self.BOX_SIZE
        box_col = (col // self.BOX_SIZE) * self.BOX_SIZE
        for r in range(box_row, box_row + self.BOX_SIZE):
            for c in range(box_col, box_col + self.BOX_SIZE):
                if (r != row or c != col) and value in self.candidates[r][c]:
                    self.candidates[r][c].discard(value)
    
    def set_value(self, row: int, col: int, value: int) -> bool:
        """칸에 값을 설정하고 제약 조건 전파"""
        if not self.is_valid_move(row, col, value):
            return False
        
        self.board[row][col] = value
        self.candidates[row][col] = {value}
        self._remove_candidate_from_peers(row, col, value)
        return True
    
    def is_valid_move(self, row: int, col: int, value: int) -> bool:
        """특정 위치에 값을 넣을 수 있는지 검증"""
        if self.board[row][col] != 0:
            return False
        
        # 같은 행 확인
        for c in range(self.SIZE):
            if self.board[row][c] == value:
                return False
        
        # 같은 열 확인
        for r in range(self.SIZE):
            if self.board[r][col] == value:
                return False
        
        # 같은 박스 확인
        box_row = (row // self.BOX_SIZE) * self.BOX_SIZE
        box_col = (col // self.BOX_SIZE) * self.BOX_SIZE
        for r in range(box_row, box_row + self.BOX_SIZE):
            for c in range(box_col, box_col + self.BOX_SIZE):
                if self.board[r][c] == value:
                    return False
        
        return True
    
    def is_complete(self) -> bool:
        """스도쿠가 완성되었는지 확인"""
        for i in range(self.SIZE):
            for j in range(self.SIZE):
                if self.board[i][j] == 0:
                    return False
        return self.is_valid()
    
    def is_valid(self) -> bool:
        """현재 상태가 유효한 스도쿠인지 확인"""
        # 각 행 확인
        for i in range(self.SIZE):
            seen = set()
            for j in range(self.SIZE):
                val = self.board[i][j]
                if val != 0:
                    if val in seen:
                        return False
                    seen.add(val)
        
        # 각 열 확인
        for j in range(self.SIZE):
            seen = set()
            for i in range(self.SIZE):
                val = self.board[i][j]
                if val != 0:
                    if val in seen:
                        return False
                    seen.add(val)
        
        # 각 박스 확인
        for box_row in range(0, self.SIZE, self.BOX_SIZE):
            for box_col in range(0, self.SIZE, self.BOX_SIZE):
                seen = set()
                for i in range(box_row, box_row + self.BOX_SIZE):
                    for j in range(box_col, box_col + self.BOX_SIZE):
                        val = self.board[i][j]
                        if val != 0:
                            if val in seen:
                                return False
                            seen.add(val)
        
        return True
    
    def get_empty_cells(self) -> List[Tuple[int, int]]:
        """빈 칸들의 좌표 리스트 반환"""
        return [(i, j) for i in range(self.SIZE) 
                for j in range(self.SIZE) if self.board[i][j] == 0]
    
    def get_candidates(self, row: int, col: int) -> Set[int]:
        """특정 칸의 가능한 숫자 후보 반환"""
        return self.candidates[row][col].copy()
    
    def __str__(self) -> str:
        """스도쿠 판을 보기 좋게 출력"""
        lines = []
        for i in range(self.SIZE):
            if i % 3 == 0 and i > 0:
                lines.append("------+-------+------")
            
            row_str = ""
            for j in range(self.SIZE):
                if j % 3 == 0 and j > 0:
                    row_str += "| "
                val = self.board[i][j]
                row_str += str(val) if val != 0 else "."
                row_str += " "
            lines.append(row_str)
        
        return "\n".join(lines)
    
    def show_candidates(self, max_candidates: int = 9) -> str:
        """각 칸의 가능한 후보들을 보기 좋게 출력"""
        lines = []
        for i in range(self.SIZE):
            if i % 3 == 0 and i > 0:
                lines.append("------+-------+------")
            
            row_str = ""
            for j in range(self.SIZE):
                if j % 3 == 0 and j > 0:
                    row_str += "| "
                
                val = self.board[i][j]
                if val != 0:
                    # 이미 채워진 칸
                    row_str += f" {val} "
                else:
                    # 후보 표시
                    candidates = sorted(list(self.candidates[i][j]))
                    if len(candidates) == 0:
                        # 불가능한 상태
                        row_str += " X "
                    elif len(candidates) <= max_candidates:
                        # 후보가 적으면 모두 표시 (예: 123, 45, 9)
                        cand_str = "".join(str(c) for c in candidates)
                        row_str += f"{cand_str:^9}"[:9]  # 최대 9자리
                    else:
                        # 후보가 많으면 개수만 표시
                        row_str += f"({len(candidates)})"
            
            lines.append(row_str)
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"SudokuBoard({self.board})"

