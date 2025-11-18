"""
스도쿠 솔버 모듈

다양한 논리 기법과 백트래킹을 사용하여 스도쿠를 해결하는 클래스를 제공합니다.
"""

from typing import List, Optional, Callable, Tuple
from copy import deepcopy
from .board import SudokuBoard
from . import techniques


class SudokuSolver:
    """스도쿠를 푸는 다양한 전략을 가진 솔버"""
    
    def __init__(self, board: SudokuBoard):
        self.board = deepcopy(board)
        self.steps: List[str] = []  # 해결 과정 기록
    
    def _copy_board_state(self) -> List[List[int]]:
        """보드 상태를 복사하여 반환 (헬퍼 메서드)"""
        return [[self.board.board[i][j] for j in range(self.board.SIZE)] 
                for i in range(self.board.SIZE)]
    
    def solve(self, step_by_step: bool = False, 
              on_step: Optional[Callable[[str, Optional[Tuple[int, int]], List[Tuple[int, int]]], None]] = None) -> bool:
        """
        스도쿠를 논리적 기법으로 풀기 (가이드 기반)
        
        Args:
            step_by_step: True면 각 단계마다 콘솔에 상태를 출력 (내부적으로 on_step 콜백 사용)
            on_step: 각 단계마다 호출되는 콜백 함수
                    (technique_name, filled_cell, highlighted_cells) -> None
        """
        # step_by_step이 True면 콘솔 출력용 on_step 콜백 생성
        if step_by_step and on_step is None:
            current_iteration = [0]  # 클로저를 위한 리스트 사용
            
            def console_step_callback(technique_name: str, filled_cell: Optional[Tuple[int, int]], 
                                     highlighted: List[Tuple[int, int]]):
                if technique_name == "초기 상태":
                    print("\n[초기 상태 - 각 칸의 가능한 후보들]")
                    print(self.board.show_candidates())
                    print("\n" + "="*80)
                elif technique_name == "해결 완료":
                    print("\n[해결 완료]")
                elif technique_name.startswith("오류"):
                    print(f"\n[{technique_name}]")
                elif technique_name == "백트래킹 시작":
                    print("\n[논리적 기법 한계 도달] 백트래킹 시작")
                else:
                    # 일반적인 기법 적용 (iteration 증가는 실제 기법 적용 시에만)
                    if not technique_name.endswith("(후보 제거)"):
                        current_iteration[0] += 1
                    filled_cells = highlighted if highlighted else ([filled_cell] if filled_cell else [])
                    if filled_cells:
                        print(f"\n[라운드 {current_iteration[0]}] {technique_name} 적용 후 ({len(filled_cells)}개 셀 채움):")
                        print(self.board)
                        print("\n[현재 후보 상태]")
                        print(self.board.show_candidates())
                        print("="*80)
                    else:
                        # 후보 제거만 한 경우
                        print(f"\n[라운드 {current_iteration[0]}] {technique_name} 적용 후 (후보 제거):")
                        print(self.board)
                        print("\n[현재 후보 상태]")
                        print(self.board.show_candidates())
                        print("="*80)
            
            on_step = console_step_callback
        
        max_iterations = 1000
        iteration = 0
        
        if on_step:
            on_step("초기 상태", None, [])
        
        prev_board_state = self._copy_board_state()
        
        while not self.board.is_complete() and iteration < max_iterations:
            iteration += 1
            
            # 핵심 원칙 1: 값 확정 (Singles) - 가장 강력하고 저렴함
            changes_made_in_singles = False
            while True:
                if techniques.apply_naked_singles(self.board, self.steps):
                    changes_made_in_singles = True
                    filled_cells = self._find_filled_cells(prev_board_state)
                    if on_step:
                        # 여러 개의 셀을 한 번에 하나의 단계로 표시
                        on_step("Naked Single", None, filled_cells)
                    prev_board_state = self._copy_board_state()
                    if self.board.is_complete():
                        return True
                    continue
                
                if techniques.apply_hidden_singles(self.board, self.steps):
                    changes_made_in_singles = True
                    filled_cells = self._find_filled_cells(prev_board_state)
                    if on_step:
                        # 여러 개의 셀을 한 번에 하나의 단계로 표시
                        on_step("Hidden Single", None, filled_cells)
                    prev_board_state = self._copy_board_state()
                    if self.board.is_complete():
                        return True
                    continue
                
                break
            
            if changes_made_in_singles:
                continue
            
            # 핵심 원칙 2: 후보 제거 (Singles로 풀리지 않을 때만 실행)
            if techniques.apply_locked_candidates(self.board, self.steps):
                if self._apply_candidate_removal_technique("Locked Candidates", iteration, 
                                                          on_step, prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            if techniques.apply_naked_subsets(self.board, self.steps, 2):
                if self._apply_candidate_removal_technique("Naked Pairs", iteration, 
                                                          on_step, prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            if techniques.apply_hidden_subsets(self.board, self.steps, 2):
                if self._apply_candidate_removal_technique("Hidden Pairs", iteration, 
                                                          on_step, prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            if techniques.apply_naked_subsets(self.board, self.steps, 3):
                if self._apply_candidate_removal_technique("Naked Triples", iteration, 
                                                          on_step, prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            if techniques.apply_hidden_subsets(self.board, self.steps, 3):
                if self._apply_candidate_removal_technique("Hidden Triples", iteration, 
                                                          on_step, prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            if techniques.apply_naked_subsets(self.board, self.steps, 4):
                if self._apply_candidate_removal_technique("Naked Quads", iteration, 
                                                          on_step, prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            if techniques.apply_hidden_subsets(self.board, self.steps, 4):
                if self._apply_candidate_removal_technique("Hidden Quads", iteration, 
                                                          on_step, prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            # 종료 조건
            if self.board.is_complete():
                if on_step:
                    on_step("해결 완료", None, [])
                return True
            elif self._is_invalid():
                if on_step:
                    on_step("오류: 유효하지 않은 상태", None, [])
                return False
            else:
                empty_cells = self.board.get_empty_cells()
                if empty_cells:
                    best_cell = min(empty_cells, 
                                   key=lambda cell: len(self.board.get_candidates(cell[0], cell[1])))
                    row, col = best_cell
                    candidates = list(self.board.get_candidates(row, col))
                    if on_step:
                        on_step("백트래킹 시작", None, [(row, col)])
                return self._backtrack(on_step=on_step)
        
        return self.board.is_complete()
    
    def _find_filled_cells(self, prev_state: List[List[int]]) -> List[Tuple[int, int]]:
        """이전 상태와 비교하여 새로 채워진 모든 셀 찾기"""
        filled = []
        for i in range(self.board.SIZE):
            for j in range(self.board.SIZE):
                if prev_state[i][j] == 0 and self.board.board[i][j] != 0:
                    filled.append((i, j))
        return filled
    
    def _apply_candidate_removal_technique(self, technique_name: str, iteration: int, 
                                          on_step: Optional[Callable],
                                          prev_board_state: List[List[int]]) -> bool:
        """
        후보 제거 기법 적용 후 처리 (후보 제거 결과 저장 + Singles 체크)
        Returns: True if board is complete
        """
        # 후보 제거 결과를 먼저 단계로 저장
        if on_step:
            on_step(f"{technique_name} (후보 제거)", None, [])
        prev_state = self._copy_board_state()
        
        # 후보 제거 후 즉시 Singles 체크 (후보 제거로 인해 값이 채워질 수 있음)
        while True:
            if techniques.apply_naked_singles(self.board, self.steps):
                filled_cells = self._find_filled_cells(prev_state)
                if on_step:
                    on_step("Naked Single", None, filled_cells)
                prev_state = self._copy_board_state()
                if self.board.is_complete():
                    return True
                continue
            
            if techniques.apply_hidden_singles(self.board, self.steps):
                filled_cells = self._find_filled_cells(prev_state)
                if on_step:
                    on_step("Hidden Single", None, filled_cells)
                prev_state = self._copy_board_state()
                if self.board.is_complete():
                    return True
                continue
            
            break
        
        return False
    
    def _is_invalid(self) -> bool:
        """퍼즐 상태가 유효하지 않은지 확인 (후보가 0개인 빈 셀이 있는지)"""
        for i in range(self.board.SIZE):
            for j in range(self.board.SIZE):
                if self.board.board[i][j] == 0:
                    if len(self.board.candidates[i][j]) == 0:
                        return True
        return False
    
    def _backtrack(self, on_step: Optional[Callable[[str, Optional[Tuple[int, int]], List[Tuple[int, int]]], None]] = None) -> bool:
        """백트래킹으로 남은 부분 해결"""
        empty_cells = self.board.get_empty_cells()
        if not empty_cells:
            return self.board.is_complete()
        
        # 가장 적은 후보를 가진 칸 선택 (MRV)
        best_cell = min(empty_cells, 
                       key=lambda cell: len(self.board.get_candidates(cell[0], cell[1])))
        row, col = best_cell
        
        candidates = list(self.board.get_candidates(row, col))
        if not candidates:
            return False
        
        for value in candidates:
            board_copy = deepcopy(self.board)
            if board_copy.set_value(row, col, value):
                self.steps.append(f"백트래킹 시도: ({row+1},{col+1}) = {value}")
                solver = SudokuSolver(board_copy)
                if solver.solve(on_step=on_step):
                    self.board = solver.board
                    self.steps.extend(solver.steps)
                    self.steps.append(f"백트래킹 성공: ({row+1},{col+1}) = {value}가 정답")
                    if on_step:
                        on_step("백트래킹 완료", None, [])
                    return True
                else:
                    self.steps.append(f"백트래킹 실패: ({row+1},{col+1}) = {value}는 불가능")
        
        if on_step:
            on_step("백트래킹 실패", None, [])
        return False
    
    def get_solution(self) -> SudokuBoard:
        """해결된 스도쿠 판 반환"""
        return self.board
    
    def get_steps(self) -> List[str]:
        """해결 과정 반환"""
        return self.steps

