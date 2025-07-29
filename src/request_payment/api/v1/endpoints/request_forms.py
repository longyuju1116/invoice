"""請款單相關的 API endpoints."""

import base64
import io
import uuid
import urllib.parse
import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Response
from fastapi.responses import StreamingResponse

from ....models.schemas import (
    RequestFormCreate,
    RequestFormResponse,
    PaymentDetailItem,
    FileUploadResponse,
    PaymentMethod,
    RequestingUnit
)
from ....services.pdf_service import PDFService
from ....services import file_manager, FileType
from ....utils.validators import validate_image_file

router = APIRouter()

# 儲存請款單的記憶體數據 (簡化版本，適合 Hugging Face Spaces 部署)
payment_requests_storage = {}


@router.post("/upload-image", response_model=FileUploadResponse)
async def upload_bank_book_image(file: UploadFile = File(...)):
    """上傳存摺影本圖片"""
    try:
        # 使用檔案管理服務保存圖片
        file_info = await file_manager.save_image(file, prefix="bankbook")
        
        # 讀取檔案內容並轉換為 base64（為了保持與前端的相容性）
        file_content = await file_manager.get_file(file_info["file_id"], FileType.IMAGE)
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        return FileUploadResponse(
            filename=file_info["original_filename"],
            size=file_info["file_size"],
            content_type=file_info["content_type"],
            file_id=file_base64  # 回傳 base64 編碼的圖片資料
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檔案上傳失敗: {str(e)}")


@router.post("/", response_model=RequestFormResponse)
async def create_payment_request(request: RequestFormCreate):
    """創建請款單"""
    try:
        # 計算總金額
        total_amount = sum(item.amount for item in request.payment_details)
        
        # 生成請款單 ID
        request_id = str(uuid.uuid4())
        
        # 儲存請款單數據
        payment_request_data = {
            "id": request_id,
            "application_date": request.application_date,
            "payee": request.payee,
            "payment_method": request.payment_method,
            "payment_method_other": request.payment_method_other,
            "requesting_unit": request.requesting_unit,
            "requesting_unit_other": request.requesting_unit_other,
            "total_amount": total_amount,
            "payment_details": request.payment_details,
            "bank_book_image": request.bank_book_image,
            "created_at": datetime.now(),
            "pdf_url": f"/api/v1/request-forms/{request_id}/pdf"
        }
        
        payment_requests_storage[request_id] = payment_request_data
        
        return RequestFormResponse(**payment_request_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"創建請款單失敗: {str(e)}")


@router.get("/{request_id}", response_model=RequestFormResponse)
async def get_payment_request(request_id: str):
    """取得請款單詳情"""
    if request_id not in payment_requests_storage:
        raise HTTPException(status_code=404, detail="找不到指定的請款單")
    
    return RequestFormResponse(**payment_requests_storage[request_id])


@router.get("/{request_id}/pdf")
async def download_payment_request_pdf(request_id: str):
    """下載請款單 PDF"""
    if request_id not in payment_requests_storage:
        raise HTTPException(status_code=404, detail="找不到指定的請款單")
    
    try:
        payment_data = payment_requests_storage[request_id]
        
        # 添加日誌記錄
        print(f"開始生成PDF，請款單ID: {request_id}")
        print(f"請款單數據: {payment_data}")
        
        # 使用 PDF 服務生成 PDF
        pdf_service = PDFService()
        pdf_buffer = pdf_service.generate_payment_request_pdf(payment_data)
        
        # 生成詳細的檔案名稱（只使用時間戳）
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.pdf"
        
        # 獲取PDF內容
        pdf_content = pdf_buffer.getvalue()
        print(f"PDF生成成功，大小: {len(pdf_content)} bytes")
        
        # URL編碼中文檔名以避免編碼問題
        encoded_filename = urllib.parse.quote(filename, safe='')
        
        # 回傳 PDF 檔案
        headers = {
            'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}',
            'Content-Type': 'application/pdf'
        }
        
        print(f"PDF下載準備完成，檔名: {filename}")
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers=headers
        )
    
    except Exception as e:
        print(f"PDF生成失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 提供更詳細的錯誤信息
        error_detail = f"PDF生成失敗: {str(e)}"
        if "Permission denied" in str(e):
            error_detail = "PDF生成失敗: 文件權限問題，請檢查目錄權限"
        elif "font" in str(e).lower():
            error_detail = "PDF生成失敗: 字體載入問題，請檢查字體文件"
        
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/")
async def list_payment_requests():
    """列出所有請款單"""
    return {
        "items": list(payment_requests_storage.values()),
        "total": len(payment_requests_storage)
    }


@router.get("/enums/payment-methods")
async def get_payment_methods():
    """取得付款方式選項"""
    return [{"value": method.value, "label": method.value} for method in PaymentMethod]


@router.get("/enums/requesting-units")
async def get_requesting_units():
    """取得請款單位選項"""
    return [{"value": unit.value, "label": unit.value} for unit in RequestingUnit]


 