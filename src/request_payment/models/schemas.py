"""Pydantic schemas for the RequestPayment application."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator
import re


class HealthResponse(BaseModel):
    """健康檢查回應模型"""
    status: str
    version: str
    timestamp: Optional[datetime] = None


class PaymentMethod(str, Enum):
    """付款方式枚舉"""
    CASH = "現金"
    TRANSFER = "匯款" 
    DONATION = "轉捐款"
    ADVANCE = "預支"
    OTHER = "其他"


class RequestingUnit(str, Enum):
    """請款單位枚舉"""
    GUIDANCE = "輔導活動執委會"
    ADMIN_FINANCE = "行政財務執委會"
    INFO_MEDIA = "資訊媒體執委會"
    OTHER = "其他"


class ProjectType(str, Enum):
    """專案類型枚舉"""
    MEETING = "A.會議(理監事會議、審查會議、幹事會議等)"
    ACTIVITY = "B.活動(含年會、各項座談會、年度志工激勵活動、各區學生輔導活動等)"
    VOLUNTEER_TRAINING = "C.志工培訓(含志工會議)"
    SCHOOL_INTERVIEW = "D.學校訪談"
    PROJECT_SUBSIDY = "E.專案補助"
    OTHER = "F.其他"


class ExpenseType(str, Enum):
    """費用類型枚舉"""
    TRANSPORTATION = "1.交通費"
    VENUE_RENTAL = "2.場地租借"
    MEAL_FEE = "3.餐費"
    PUBLICITY = "4.文宣"
    PHONE_FEE = "5.電話費"
    SUBSIDY = "6.補助"
    VOLUNTEER_ALLOWANCE = "7.志工津貼"
    EQUIPMENT = "8.設備器材(含軟硬體)"
    MISCELLANEOUS = "9.雜支"


class PaymentDetailItem(BaseModel):
    """請款明細項目"""
    project_type: ProjectType = Field(..., description="專案類型")
    expense_type: ExpenseType = Field(..., description="費用類型")
    execution_time: Optional[str] = Field(None, description="執行時間")
    execution_content: str = Field(..., description="執行內容")
    amount: Decimal = Field(..., description="金額", ge=0)
    receipt_note: Optional[str] = Field(None, description="備註憑證")


class RequestFormCreate(BaseModel):
    """創建請款單的請求模型"""
    application_date: Optional[str] = Field(None, description="申請日期 (民國年格式)")
    payee: str = Field(..., description="受款人")
    payment_method: PaymentMethod = Field(..., description="付款方式")
    payment_method_other: Optional[str] = Field(None, description="其他付款方式說明")
    requesting_unit: RequestingUnit = Field(..., description="請款單位")
    requesting_unit_other: Optional[str] = Field(None, description="其他請款單位說明")
    payment_details: List[PaymentDetailItem] = Field(..., description="請款明細", min_items=1)
    bank_book_image: Optional[str] = Field(None, description="存摺影本 base64 編碼")

    @field_validator('application_date')
    @classmethod
    def validate_application_date(cls, v):
        if v and not re.match(r'^\d{1,3}\.\d{1,2}\.\d{1,2}$', v):
            raise ValueError('申請日期格式應為 xxx.xx.xx (民國年)')
        return v

    def model_post_init(self, __context) -> None:
        """在模型初始化後進行額外驗證"""
        # 驗證付款方式其他說明
        if self.payment_method == PaymentMethod.OTHER and not self.payment_method_other:
            raise ValueError('選擇其他付款方式時必須填寫說明')
        
        # 驗證請款單位其他說明
        if self.requesting_unit == RequestingUnit.OTHER and not self.requesting_unit_other:
            raise ValueError('選擇其他請款單位時必須填寫說明')
        
        # 驗證存摺影本
        if self.payment_method in [PaymentMethod.TRANSFER, PaymentMethod.ADVANCE] and not self.bank_book_image:
            raise ValueError('匯款或預支付款方式需要上傳存摺影本')


class RequestFormResponse(BaseModel):
    """請款單回應模型"""
    id: str
    application_date: Optional[str]
    payee: str
    payment_method: PaymentMethod
    payment_method_other: Optional[str]
    requesting_unit: RequestingUnit
    requesting_unit_other: Optional[str]
    total_amount: Decimal
    payment_details: List[PaymentDetailItem]
    created_at: datetime
    pdf_url: Optional[str] = None

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """檔案上傳回應模型"""
    filename: str
    size: int
    content_type: str
    file_id: str


class FileInfoResponse(BaseModel):
    """檔案資訊回應模型"""
    file_id: str
    file_path: str
    file_size: int
    file_type: str
    created_at: str
    modified_at: str 