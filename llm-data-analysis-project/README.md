# LLM Data Analysis Project

데이터 분석 강의를 위한 실습·프로젝트 작업 공간입니다.

## Directory Structure

```text
llm-data-analysis-project/
├─ data/
│  ├─ raw/          # 원본 데이터: 가공하지 않은 입력 데이터
│  ├─ processed/    # 분석용으로 전처리된 데이터
│  └─ external/     # 외부 출처에서 수집한 데이터
├─ notebooks/       # 탐색적 분석(EDA), 실습 및 실험용 Jupyter Notebook
├─ src/             # 재사용 가능한 데이터 처리·분석 코드
├─ outputs/
│  ├─ figures/      # 그래프 및 시각화 결과
│  ├─ tables/       # 분석 결과 테이블
│  └─ reports/      # 분석 보고서 및 산출물
├─ README.md
└─ requirements.txt
```

## Recommended Workflow

1. `data/raw/`에 원본 데이터를 보관합니다.
2. `notebooks/`에서 데이터 탐색 및 분석을 수행합니다.
3. 반복적으로 사용할 전처리·분석 로직은 `src/`로 이동합니다.
4. 전처리 결과는 `data/processed/`에 저장합니다.
5. 시각화, 테이블, 보고서는 `outputs/` 하위에 저장합니다.

## Data Management Rules

- 원본 데이터(`data/raw/`)는 가능한 한 수정하지 않습니다.
- 개인정보·비밀정보·API Key 등 민감정보는 Git에 업로드하지 않습니다.
- 대용량 데이터는 Git 저장소에 직접 커밋하지 않고 별도 저장소 또는 다운로드 절차를 사용합니다.
- 분석 과정과 결과가 재현될 수 있도록 Notebook과 `requirements.txt`를 함께 관리합니다.
