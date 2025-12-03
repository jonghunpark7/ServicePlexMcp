# mock_api.py
from fastapi import FastAPI, Response
import uvicorn

app = FastAPI()

@app.get("/contracts/{contract_id}")
def get_contract(contract_id: str):
    if contract_id == "C-1001":
        return {"id": contract_id, "name": "Standard Plan", "billingType": "usage"}
    return Response(status_code=404)

@app.get("/contracts/{contract_id}/invoices")
def list_invoices(contract_id: str, month: str = None):
    if contract_id == "C-1001":
        if month == "2024-10":
            # 10월 인보이스가 이미 존재하는 상황을 시뮬레이션
            return [{"id": "I-123", "month": "2024-10", "amount": 5000}]
        return [] # 다른 달은 인보이스 없음
    return Response(status_code=404)

@app.get("/contracts/{contract_id}/usage")
def get_usage(contract_id: str, month: str = None):
    if contract_id == "C-1001":
        if month == "2024-10":
            return {"month": month, "total": 100, "unit": "GB"}
        return {"month": month, "total": 0, "unit": "GB"} # 사용량 없는 상황
    return Response(status_code=404)

# ✨ 이 부분이 가장 중요합니다! ✨
# 스크립트가 직접 실행되었을 때 uvicorn 서버를 실행시키는 코드입니다.
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9000)