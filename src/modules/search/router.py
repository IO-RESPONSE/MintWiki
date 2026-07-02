"""검색 모듈의 HTTP 어댑터: 검색 라우터 골격."""
from fastapi import APIRouter

# 검색 API 라우터. 접두사는 main.py에 등록할 때 지정한다.
# 실제 검색/색인 라우트는 이후 태스크에서 이 라우터에 연결한다.
router = APIRouter()
