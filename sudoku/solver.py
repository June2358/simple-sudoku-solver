"""
스도쿠 솔버 모듈

다양한 논리 기법과 백트래킹을 사용하여 스도쿠를 해결하는 클래스를 제공합니다.
"""

from typing import List, Optional, Callable, Tuple, Dict, Any, Set
from copy import deepcopy
from .board import SudokuBoard
from . import techniques


class SudokuSolver:
    """스도쿠를 푸는 다양한 전략을 가진 솔버"""
    
    def __init__(self, board: SudokuBoard, on_step: Optional[Callable[[Dict[str, Any]], None]] = None,
                 depth: int = 0, assumptions: Optional[List[Tuple[int, int]]] = None):
        self.board = deepcopy(board)
        self.steps: List[str] = []  # 해결 과정 기록
        self.on_step = on_step
        self.depth = depth
        self.assumptions = list(assumptions or [])
    
    def _copy_board_state(self) -> List[List[int]]:
        """보드 상태를 복사하여 반환 (헬퍼 메서드)"""
        return [[self.board.board[i][j] for j in range(self.board.SIZE)] 
                for i in range(self.board.SIZE)]
    
    def _copy_candidates_state(self) -> List[List[Set[int]]]:
        """현재 후보 상태를 깊은 복사로 반환"""
        return [[self.board.candidates[i][j].copy() for j in range(self.board.SIZE)] 
                for i in range(self.board.SIZE)]
    
    def _snapshot_from_board(self, board: SudokuBoard) -> Tuple[List[List[int]], List[List[Set[int]]]]:
        board_state = [[board.board[i][j] for j in range(board.SIZE)] 
                       for i in range(board.SIZE)]
        candidates_state = [[board.candidates[i][j].copy() for j in range(board.SIZE)]
                            for i in range(board.SIZE)]
        return board_state, candidates_state
    
    def _emit_step(self, event_type: str, technique_name: Optional[str] = None,
                   filled_cell: Optional[Tuple[int, int]] = None,
                   highlighted: Optional[List[Tuple[int, int]]] = None,
                   message: Optional[str] = None,
                   value: Optional[int] = None,
                   board_override: Optional[SudokuBoard] = None,
                   assumptions_override: Optional[List[Tuple[int, int]]] = None) -> None:
        """시각화/로그를 위한 이벤트 전파"""
        if not self.on_step:
            return
        
        if board_override is not None:
            board_state, candidates_state = self._snapshot_from_board(board_override)
        else:
            board_state = self._copy_board_state()
            candidates_state = self._copy_candidates_state()
        
        event_assumptions = assumptions_override if assumptions_override is not None else list(self.assumptions)
        
        event = {
            "event_type": event_type,
            "technique_name": technique_name or "",
            "filled_cell": filled_cell,
            "highlighted": highlighted or [],
            "message": message,
            "value": value,
            "depth": self.depth,
            "assumptions": event_assumptions,
            "board_state": board_state,
            "candidates_state": candidates_state,
        }
        self.on_step(event)
    
    @staticmethod
    def _format_cells_message(technique: str, cells: List[Tuple[int, int]]) -> str:
        if not cells:
            return technique
        locations = ", ".join(f"R{r+1}C{c+1}" for r, c in cells[:3])
        if len(cells) > 3:
            locations += f" 외 {len(cells)-3}개"
        return f"{technique}: {locations}"
    
    def solve(self, step_by_step: bool = False, 
              on_step: Optional[Callable[[Dict[str, Any]], None]] = None) -> bool:
        """
        스도쿠를 논리적 기법으로 풀기 (가이드 기반)
        
        Args:
            step_by_step: True면 각 단계마다 콘솔에 상태를 출력 (내부적으로 on_step 콜백 사용)
            on_step: 각 단계마다 호출되는 콜백 함수
                    (event_dict) -> None
        """
        if step_by_step and on_step is None:
            current_iteration = [0]

            def console_step_callback(event: Dict[str, Any]):
                event_type = event.get("event_type", "")
                tech = event.get("technique_name") or event_type
                message = event.get("message", "")
                board_state = event.get("board_state")
                candidates_state = event.get("candidates_state")
                
                def _print_board_snapshot():
                    if not board_state:
                        return
                    preview_board = SudokuBoard(board_state)
                    if candidates_state:
                        for r in range(SudokuBoard.SIZE):
                            for c in range(SudokuBoard.SIZE):
                                preview_board.candidates[r][c] = candidates_state[r][c]
                    print(preview_board)
                    print("\n[현재 후보 상태]")
                    print(preview_board.show_candidates())
                    print("=" * 80)
                
                if event_type == "INITIAL_STATE":
                    print("\n[초기 상태 - 각 칸의 가능한 후보들]")
                    _print_board_snapshot()
                elif event_type == "SOLVED":
                    print("\n[해결 완료]")
                    _print_board_snapshot()
                elif event_type in {"CONTRADICTION", "ERROR"}:
                    print(f"\n[{tech}] {message}")
                elif event_type.startswith("GUESS") or event_type.startswith("BACKTRACK"):
                    indent = "  " * event.get("depth", 0)
                    print(f"\n{indent}{message}")
                    _print_board_snapshot()
                else:
                    current_iteration[0] += 1
                    print(f"\n[라운드 {current_iteration[0]}] {tech}:")
                    _print_board_snapshot()

            on_step = console_step_callback

        if on_step is not None:
            self.on_step = on_step
        
        max_iterations = 1000
        iteration = 0
        
        self._emit_step(
            event_type="INITIAL_STATE",
            technique_name="초기 상태",
            message="초기 후보 상태"
        )
        
        prev_board_state = self._copy_board_state()
        
        while not self.board.is_complete() and iteration < max_iterations:
            iteration += 1
            
            # 핵심 원칙 1: 값 확정 (Singles) - 가장 강력하고 저렴함
            changes_made_in_singles = False
            while True:
                if techniques.apply_naked_singles(self.board, self.steps):
                    changes_made_in_singles = True
                    filled_cells = self._find_filled_cells(prev_board_state)
                    if filled_cells:
                        self._emit_step(
                            event_type="LOGIC",
                            technique_name="Naked Single",
                            highlighted=filled_cells,
                            filled_cell=filled_cells[0] if len(filled_cells) == 1 else None,
                            message=self._format_cells_message("Naked Single", filled_cells)
                        )
                    prev_board_state = self._copy_board_state()
                    if self.board.is_complete():
                        return True
                    continue
                
                if techniques.apply_hidden_singles(self.board, self.steps):
                    changes_made_in_singles = True
                    filled_cells = self._find_filled_cells(prev_board_state)
                    if filled_cells:
                        self._emit_step(
                            event_type="LOGIC",
                            technique_name="Hidden Single",
                            highlighted=filled_cells,
                            filled_cell=filled_cells[0] if len(filled_cells) == 1 else None,
                            message=self._format_cells_message("Hidden Single", filled_cells)
                        )
                    prev_board_state = self._copy_board_state()
                    if self.board.is_complete():
                        return True
                    continue
                
                break
            
            if changes_made_in_singles:
                continue
            
            # 핵심 원칙 2: 후보 제거 (Singles로 풀리지 않을 때만 실행)
            if techniques.apply_locked_candidates(self.board, self.steps):
                if self._apply_candidate_removal_technique("Locked Candidates", prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            if techniques.apply_naked_subsets(self.board, self.steps, 2):
                if self._apply_candidate_removal_technique("Naked Pairs", prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            if techniques.apply_hidden_subsets(self.board, self.steps, 2):
                if self._apply_candidate_removal_technique("Hidden Pairs", prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            if techniques.apply_naked_subsets(self.board, self.steps, 3):
                if self._apply_candidate_removal_technique("Naked Triples", prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            if techniques.apply_hidden_subsets(self.board, self.steps, 3):
                if self._apply_candidate_removal_technique("Hidden Triples", prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            if techniques.apply_naked_subsets(self.board, self.steps, 4):
                if self._apply_candidate_removal_technique("Naked Quads", prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            if techniques.apply_hidden_subsets(self.board, self.steps, 4):
                if self._apply_candidate_removal_technique("Hidden Quads", prev_board_state):
                    return True
                prev_board_state = self._copy_board_state()
                continue
            
            # 종료 조건
            if self.board.is_complete():
                self._emit_step(
                    event_type="SOLVED",
                    technique_name="해결 완료",
                    message="스도쿠 해결 완료"
                )
                return True
            elif self._is_invalid():
                self._emit_step(
                    event_type="CONTRADICTION",
                    technique_name="오류: 유효하지 않은 상태",
                    message="빈 칸에 가능한 후보가 없습니다."
                )
                return False
            else:
                empty_cells = self.board.get_empty_cells()
                if empty_cells:
                    best_cell = min(empty_cells, 
                                   key=lambda cell: len(self.board.get_candidates(cell[0], cell[1])))
                    row, col = best_cell
                    candidates = list(self.board.get_candidates(row, col))
                    self._emit_step(
                        event_type="BACKTRACK_PREP",
                        technique_name="백트래킹 시작",
                        highlighted=[(row, col)],
                        message=f"논리 기법 종료. R{row+1}C{col+1} 후보 {sorted(candidates)}로 백트래킹 진행."
                    )
                return self._backtrack()
        
        return self.board.is_complete()
    
    def _find_filled_cells(self, prev_state: List[List[int]]) -> List[Tuple[int, int]]:
        """이전 상태와 비교하여 새로 채워진 모든 셀 찾기"""
        filled = []
        for i in range(self.board.SIZE):
            for j in range(self.board.SIZE):
                if prev_state[i][j] == 0 and self.board.board[i][j] != 0:
                    filled.append((i, j))
        return filled
    
    def _apply_candidate_removal_technique(self, technique_name: str, 
                                          prev_board_state: List[List[int]]) -> bool:
        """
        후보 제거 기법 적용 후 처리 (후보 제거 결과 저장 + Singles 체크)
        Returns: True if board is complete
        """
        self._emit_step(
            event_type="CANDIDATE_REMOVAL",
            technique_name=technique_name,
            message=f"{technique_name} 적용으로 후보 제거"
        )
        prev_state = self._copy_board_state()
        
        # 후보 제거 후 즉시 Singles 체크 (후보 제거로 인해 값이 채워질 수 있음)
        while True:
            if techniques.apply_naked_singles(self.board, self.steps):
                filled_cells = self._find_filled_cells(prev_state)
                if filled_cells:
                    self._emit_step(
                        event_type="LOGIC",
                        technique_name="Naked Single",
                        highlighted=filled_cells,
                        filled_cell=filled_cells[0] if len(filled_cells) == 1 else None,
                        message=self._format_cells_message("Naked Single", filled_cells)
                    )
                prev_state = self._copy_board_state()
                if self.board.is_complete():
                    return True
                continue
            
            if techniques.apply_hidden_singles(self.board, self.steps):
                filled_cells = self._find_filled_cells(prev_state)
                if filled_cells:
                    self._emit_step(
                        event_type="LOGIC",
                        technique_name="Hidden Single",
                        highlighted=filled_cells,
                        filled_cell=filled_cells[0] if len(filled_cells) == 1 else None,
                        message=self._format_cells_message("Hidden Single", filled_cells)
                    )
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
                        self._emit_step(
                            event_type="CONTRADICTION",
                            technique_name="후보 소진",
                            highlighted=[(i, j)],
                            message=f"R{i+1}C{j+1}에 남은 후보가 없습니다."
                        )
                        return True
        return False
    
    def _backtrack(self) -> bool:
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
            self._emit_step(
                event_type="CONTRADICTION",
                technique_name="백트래킹 실패",
                highlighted=[(row, col)],
                message=f"R{row+1}C{col+1}에 가능한 후보가 없습니다."
            )
            return False
        
        for value in candidates:
            board_copy = deepcopy(self.board)
            if board_copy.set_value(row, col, value):
                self.steps.append(f"백트래킹 시도: ({row+1},{col+1}) = {value}")
                new_assumptions = self.assumptions + [(row, col)]
                self._emit_step(
                    event_type="GUESS_START",
                    technique_name="백트래킹 추측",
                    highlighted=[(row, col)],
                    filled_cell=(row, col),
                    value=value,
                    message=f"{'  ' * self.depth}▶ [추측] R{row+1}C{col+1} = {value}",
                    board_override=board_copy,
                    assumptions_override=new_assumptions
                )
                solver = SudokuSolver(board_copy, on_step=self.on_step, depth=self.depth + 1,
                                      assumptions=new_assumptions)
                if solver.solve():
                    self.board = solver.board
                    self.steps.extend(solver.steps)
                    self.steps.append(f"백트래킹 성공: ({row+1},{col+1}) = {value}가 정답")
                    if self.depth == 0:
                        self._emit_step(
                            event_type="GUESS_SUCCESS",
                            technique_name="백트래킹 확정",
                            highlighted=[(row, col)],
                            filled_cell=(row, col),
                            value=value,
                            message="백트래킹 가정 확정: 모든 추측이 성공적으로 검증되었습니다."
                        )
                    return True
                else:
                    self.steps.append(f"백트래킹 실패: ({row+1},{col+1}) = {value}는 불가능")
                    self._emit_step(
                        event_type="GUESS_FAIL",
                        technique_name="백트래킹 철회",
                        highlighted=[(row, col)],
                        filled_cell=(row, col),
                        value=value,
                        message=f"{'  ' * self.depth}✗ [철회] R{row+1}C{col+1} = {value}는 모순",
                        board_override=board_copy,
                        assumptions_override=new_assumptions
                    )
        
        self._emit_step(
            event_type="BACKTRACK_FAIL",
            technique_name="백트래킹 실패",
            highlighted=[(row, col)],
            message="모든 후보 시도 실패. 상위로 돌아갑니다."
        )
        return False
    
    def get_solution(self) -> SudokuBoard:
        """해결된 스도쿠 판 반환"""
        return self.board
    
    def get_steps(self) -> List[str]:
        """해결 과정 반환"""
        return self.steps

