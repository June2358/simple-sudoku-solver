# 스도쿠 솔버 (Sudoku Solver)

고급 논리 기법과 백트래킹을 사용하는 스도쿠 솔버입니다. 단계별 해결 과정을 시각화할 수 있는 pygame 기반 GUI를 제공합니다.

## 주요 기능

- 🧩 **핵심 해결 기법**: Naked Single, Hidden Single, Locked Candidates, Naked/Hidden Pairs/Triples/Quads
- 🎯 **백트래킹**: 논리 기법으로 풀리지 않는 경우 자동으로 백트래킹 사용
- 📊 **단계별 시각화**: pygame을 사용한 인터랙티브 GUI로 해결 과정을 단계별로 확인
- 🎮 **인터랙티브 편집**: GUI에서 직접 스도쿠 문제를 입력하고 수정 가능


이 프로젝트는 다음 환경에서 개발 및 테스트되었습니다:

- **Python**: 3.12.7 (Anaconda)
- **pygame**: 2.6.1 (SDL 2.28.4)
- **OS**: Windows 11

## 사용 방법

### GUI 사용 (권장)

가장 간단하고 직관적인 방법입니다:

```bash
python sudoku_visualizer.py
```

**GUI 조작법:**
- **마우스 클릭**: 칸 선택
- **숫자 키 (1-9)**: 선택한 칸에 숫자 입력
- **0 또는 Delete**: 선택한 칸 삭제
- **화살표 키**: 선택한 칸 이동
- **난이도 버튼**: 예제 문제 불러오기 (쉬움, 보통, 어려움, 전문가, 마스터, 극한)
- **Enter 또는 S 키**: 해결 시작
- **← → 키**: 단계별 탐색 (해결 과정을 단계별로 확인)
- **ESC 키**: 수정 모드로 돌아가기

GUI를 사용하면 스도쿠 해결 과정을 시각적으로 확인할 수 있으며, 각 단계에서 어떤 기법이 사용되었는지 확인할 수 있습니다.

## 프로젝트 구조

```
sudoku/
├── sudoku/              # 메인 패키지
│   ├── __init__.py      # 패키지 초기화
│   ├── board.py         # 스도쿠 보드 클래스
│   ├── solver.py        # 솔버 클래스
│   ├── techniques.py    # 해결 기법 구현
│   ├── utils.py         # 유틸리티 함수 (보드 로드, 퍼즐 데이터)
│   ├── puzzles.json     # 예제 퍼즐 데이터 (JSON)
│   └── gui_constants.py # GUI 상수 정의
├── sudoku_visualizer.py # pygame GUI 애플리케이션
├── requirements.txt     # 의존성 목록
└── README.md           # 이 파일
```

## 구현된 해결 기법

### 1단계: 필수 핵심 엔진 (Easy/Medium 난이도 해결)

- **Naked Single**: 후보가 1개인 셀 확정
- **Hidden Single**: 유닛(행/열/박스) 내에서 유일한 위치에 숫자 확정
- **Locked Candidates**: Pointing & Claiming (박스-라인 상호작용)

### 2단계: 효율적인 마지노선 (Hard 난이도 해결)

- **Naked Pairs/Triples/Quads**: N개의 셀이 N개의 후보만 가짐 (2-4 튜플)
- **Hidden Pairs/Triples/Quads**: N개의 숫자가 N개의 셀에만 나타남 (2-4 튜플)

### 최후의 수단

- **Backtracking**: 논리 기법으로 풀리지 않을 때 백트래킹 사용 (MRV 휴리스틱)
