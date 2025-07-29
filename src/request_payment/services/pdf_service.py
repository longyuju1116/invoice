"""PDF 生成服務."""

import io
import base64
import os
import platform
from typing import Dict, Any, Optional
from decimal import Decimal
from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image as ReportLabImage, Frame, PageTemplate
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from ..models.schemas import PaymentMethod
from ..utils.validators import format_currency


class PDFService:
    """PDF 生成服務類別"""
    
    def __init__(self):
        self.chinese_font = self.setup_fonts()
        
    def setup_fonts(self):
        """設定中文字體"""
        try:
            # 嘗試註冊中文字體
            system = platform.system()
            font_registered = False
            font_name = "Chinese-Font"
            
            # 優先使用用戶提供的標楷體字體
            custom_font_paths = ["./edukai-5.0.ttf", "/app/edukai-5.0.ttf"]
            for custom_font_path in custom_font_paths:
                if os.path.exists(custom_font_path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, custom_font_path))
                        font_registered = True
                        print(f"成功註冊標楷體字體: {custom_font_path}")
                        break
                    except Exception as e:
                        print(f"標楷體字體註冊失敗: {e}")
                        continue
            
            # 如果標楷體註冊失敗，使用系統字體
            if not font_registered:
                if system == "Windows":
                    font_paths = [
                        "C:/Windows/Fonts/msyh.ttc",  # 微軟雅黑
                        "C:/Windows/Fonts/simsun.ttc",  # 宋體
                        "C:/Windows/Fonts/simkai.ttf",  # 楷體
                    ]
                elif system == "Darwin":  # macOS
                    font_paths = [
                        "/System/Library/Fonts/PingFang.ttc",  # 蘋方
                        "/System/Library/Fonts/STHeiti Light.ttc",  # 華文黑體
                        "/System/Library/Fonts/STSong.ttc",  # 華文宋體
                    ]
                else:  # Linux
                    font_paths = [
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    ]
                
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont(font_name, font_path))
                            font_registered = True
                            print(f"成功註冊系統字體: {font_path}")
                            break
                        except Exception as e:
                            print(f"系統字體註冊失敗: {e}")
                            continue
            
            # 如果所有字體都註冊失敗，使用預設字體
            if not font_registered:
                print("警告：無法註冊中文字體，將使用預設字體")
                font_name = "Helvetica"
            
            return font_name
            
        except Exception as e:
            print(f"字體設定失敗: {e}")
            return "Helvetica"
    
    def generate_payment_request_pdf(self, payment_data: Dict[str, Any]) -> io.BytesIO:
        """生成請款單 PDF
        
        Args:
            payment_data: 請款單數據
            
        Returns:
            io.BytesIO: PDF 檔案流
        """
        buffer = io.BytesIO()
        
        # 建立 PDF 文件
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=6*cm  # 增加底部邊距以容納簽名區域
        )
        
        # 建立內容
        story = []
        
        # 計算請款明細表格需要的頁數
        required_pages = self._calculate_required_pages(payment_data)
        
        if required_pages > 1:
            # 如果表格需要多頁，生成多頁請款單
            story.extend(self._build_multi_page_payment_request(payment_data, required_pages))
        else:
            # 第一頁：請款單
            story.extend(self._build_payment_request_page(payment_data))
        
        # 第二頁：單據憑證黏貼單
        story.append(PageBreak())
        story.extend(self._build_receipt_attachment_page(payment_data))
        
        # 第三頁：存摺影本 (條件性)
        if self._needs_bank_book_page(payment_data):
            story.append(PageBreak())
            story.extend(self._build_bank_book_page(payment_data))
        
        # 建立頁碼和簽名區域模板
        def add_page_elements(canvas, doc):
            """添加頁碼和簽名區域到每頁底部"""
            page_num = canvas.getPageNumber()
            canvas.saveState()
            canvas.setFont(self.chinese_font, 12)
            canvas.setFillColor(colors.black)
            
            # 在頁面底部中央添加頁碼
            canvas.drawCentredString(A4[0]/2, 1.5*cm, str(page_num))
            
            # 在右上角添加費用申請單號
            canvas.setFont(self.chinese_font, 10)
            canvas.drawRightString(A4[0] - 2*cm, A4[1] - 2*cm, "費用申請單號：")
            canvas.drawRightString(A4[0] - 2*cm, A4[1] - 2.3*cm, "(財務組填寫)")
            
            # 在左上角添加mark.jpg圖片（等比例調整為高度2cm）
            try:
                mark_paths = ["./mark.jpg", "/app/mark.jpg"]
                mark_path = None
                for path in mark_paths:
                    if os.path.exists(path):
                        mark_path = path
                        break
                
                if mark_path:
                    # 載入圖片並獲取原始尺寸
                    pil_image = PILImage.open(mark_path)
                    original_width, original_height = pil_image.size
                    
                    # 計算等比例縮放，高度固定為2cm
                    target_height_cm = 2
                    target_height_pt = target_height_cm * 28.35  # 1cm = 28.35 points
                    
                    # 計算等比例寬度
                    aspect_ratio = original_width / original_height
                    target_width_pt = target_height_pt * aspect_ratio
                    
                    # 載入並使用調整後的大小
                    img = ReportLabImage(mark_path, width=target_width_pt, height=target_height_pt)
                    img.drawOn(canvas, 2*cm, A4[1] - 2.5*cm)
            except Exception as e:
                print(f"載入mark.jpg失敗: {e}")
            
            # 在所有請款單頁面都添加簽名區域
            # 修正：直接計算實際的請款單頁數
            details = payment_data.get("payment_details", [])
            if len(details) == 0:
                payment_pages = 1
            else:
                # 計算分頁點來確定實際頁數
                split_indices = self._calculate_split_indices(payment_data, self._calculate_required_pages(payment_data))
                payment_pages = len(split_indices)
            
            if page_num <= payment_pages:
                self._draw_signature_area(canvas, payment_data)
            
            canvas.restoreState()
        
        # 生成 PDF
        doc.build(story, onFirstPage=add_page_elements, onLaterPages=add_page_elements)
        buffer.seek(0)
        
        return buffer
    
    def _draw_signature_area(self, canvas, data: Dict[str, Any]):
        """在頁面底部繪製有框線的簽名區域：2格、5格、5格結構。"""
        # 簽名區域距離底部2cm
        signature_y_start = 2*cm
        # 簽名表格：5欄，總寬度18cm，每欄平均分配
        signature_col_width = 18*cm / 5  # 每欄3.6cm
        total_width = 18*cm
        # 計算起始位置，確保與請款明細表格左對齊
        start_x = 1.5*cm  # 與請款明細表格相同的左邊距
        x_starts = [start_x]
        for i in range(5):
            x_starts.append(start_x + (i+1) * signature_col_width)
        # 行高
        row_heights = [0.8*cm, 0.8*cm, 1.0*cm]
        signature_height = sum(row_heights)
        
        # 繪製外框
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1)
        canvas.rect(start_x, signature_y_start, total_width, signature_height)
        
        # 第一行：2格（付款單位、請款單位）
        # 左大格（前3欄）
        canvas.rect(x_starts[0], signature_y_start + row_heights[1] + row_heights[2], 3 * signature_col_width, row_heights[0])
        # 右大格（後2欄）
        canvas.rect(x_starts[3], signature_y_start + row_heights[1] + row_heights[2], 2 * signature_col_width, row_heights[0])
        # 第一行文字
        canvas.setFont(self.chinese_font, 14)
        canvas.drawCentredString(x_starts[0] + 1.5 * signature_col_width, signature_y_start + row_heights[1] + row_heights[2] + 0.25*cm, "付款單位")
        canvas.drawCentredString(x_starts[3] + signature_col_width, signature_y_start + row_heights[1] + row_heights[2] + 0.25*cm, "請款單位")
        
        # 第二行：5格（職稱）
        for i in range(5):
            canvas.rect(x_starts[i], signature_y_start + row_heights[2], signature_col_width, row_heights[1])
        positions = ["執行秘書", "財務主管", "財務經辦", "請款單位主管", "請款人"]
        canvas.setFont(self.chinese_font, 13)
        for i, pos in enumerate(positions):
            center = x_starts[i] + signature_col_width / 2
            canvas.drawCentredString(center, signature_y_start + row_heights[2] + 0.25*cm, pos)
        
        # 第三行：5格（空白）
        for i in range(5):
            canvas.rect(x_starts[i], signature_y_start, signature_col_width, row_heights[2])
        # 不畫任何第三行文字
        
        # 在簽名區域正上方繪製總計金額
        canvas.setFont(self.chinese_font, 14)
        canvas.setFillColor(colors.black)
        total_text = f"總計：NT$ {format_currency(float(data.get('total_amount', 0)))}"
        canvas.drawRightString(x_starts[5], signature_y_start + signature_height + 0.5*cm, total_text)
    
    def _build_payment_request_page(self, data: Dict[str, Any]) -> list:
        """建立請款單頁面內容"""
        story = []
        styles = getSampleStyleSheet()
        
        # 標題 - 去掉黑框，改為簡約風格
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            alignment=TA_CENTER,
            spaceAfter=15,  # 大幅減少間距
            fontName=self.chinese_font,
            textColor=colors.black
        )
        story.append(Paragraph("請款單", title_style))
        story.append(Spacer(1, 10))  # 大幅減少間距
        
        # 基本資訊表格 - 移除建立時間欄位
        basic_info_data = [
            ["申請日期", data.get("application_date", "") or "（未填寫）", "請款單位", self._get_requesting_unit_display(data)],
            ["受款人", data.get("payee", ""), "付款方式", self._get_payment_method_display(data)],
            ["請款金額", f"NT$ {format_currency(float(data.get('total_amount', 0)))}", "", ""]
        ]
        
        basic_info_table = Table(basic_info_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm], rowHeights=[0.8*cm]*3)
        basic_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # 改為左對齊，更清晰
            ('FONTSIZE', (0, 0), (0, -1), 13),  # 標題字體稍大
            ('FONTSIZE', (2, 0), (2, -1), 13),  # 標題字體稍大
            ('TOPPADDING', (0, 0), (-1, -1), 6),  # 減少內邊距
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # 減少內邊距
            ('LEFTPADDING', (0, 0), (-1, -1), 8),  # 減少內邊距
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),  # 減少內邊距
        ]))
        story.append(basic_info_table)
        story.append(Spacer(1, 8))  # 大幅減少間距
        
        # 請款明細標題
        heading2_style = ParagraphStyle(
            'Heading2Chinese',
            parent=styles['Heading2'],
            fontName=self.chinese_font,
            fontSize=18,
            textColor=colors.black,
            alignment=TA_LEFT,  # 改為左對齊
            spaceAfter=8,  # 大幅減少間距
            spaceBefore=5  # 大幅減少間距
        )
        story.append(Paragraph("請款明細", heading2_style))
        story.append(Spacer(1, 5))  # 大幅減少間距
        
        # 新增說明文字（在標題底下，表格之前）
        note_style = ParagraphStyle(
            'NoteStyle',
            parent=styles['Normal'],
            fontName=self.chinese_font,
            fontSize=11,  # 與表格內文字相同大小
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=5,  # 大幅減少間距
            spaceBefore=2  # 大幅減少間距
        )
        
        # 專案說明
        project_note = "專案：A.會議(理監事會議、審查會議、幹事會議等) B.活動(含年會、各項座談會、年度志工激勵活動、各區學生輔導活動等) C.志工培訓(含志工會議) D.學校訪談 E.專案補助 F.其他"
        story.append(Paragraph(project_note, note_style))
        
        # 費用類型說明
        expense_note = "費用類型：1.交通費 2.場地租借 3.餐費 4.文宣 5.電話費 6.補助 7.志工津貼 8.設備器材(含軟硬體) 9.雜支"
        story.append(Paragraph(expense_note, note_style))
        
        story.append(Spacer(1, 8))  # 大幅減少表格前的間距
        
        # 請款明細表格（移除總計行）
        detail_headers = ["專案", "費用類型", "執行時間", "執行內容", "金額", "備註憑證"]
        detail_data = [detail_headers]
        
        for item in data.get("payment_details", []):
            # 處理 Pydantic 模型或字典，使用簡化顯示
            if hasattr(item, 'project_type'):
                # Pydantic 模型
                project_text = self._get_simplified_display(item.project_type)
                expense_text = self._get_simplified_display(item.expense_type)
                row = [
                    project_text,  # 簡化後不需要換行
                    expense_text,  # 簡化後不需要換行
                    item.execution_time or "",
                    self._wrap_text(item.execution_content, 9),  # 執行內容超過9個字自動換行
                    f"NT$ {format_currency(float(item.amount))}",
                    ""  # 備註憑證留空
                ]
            else:
                # 字典
                project_text = self._get_simplified_display(item["project_type"])
                expense_text = self._get_simplified_display(item["expense_type"])
                row = [
                    project_text,  # 簡化後不需要換行
                    expense_text,  # 簡化後不需要換行
                    item.get("execution_time", ""),
                    self._wrap_text(item["execution_content"], 9),  # 執行內容超過9個字自動換行
                    f"NT$ {format_currency(float(item['amount']))}",
                    ""  # 備註憑證留空
                ]
            detail_data.append(row)
        
        # 動態計算每行的高度
        row_heights = []
        for i, row in enumerate(detail_data):
            if i == 0:  # 標題行
                row_heights.append(1.2*cm)
            else:  # 資料行
                # 計算每行文字的最大行數
                max_lines = 1
                for cell_text in row:
                    if cell_text:
                        lines = cell_text.count('\n') + 1
                        max_lines = max(max_lines, lines)
                # 根據行數調整高度，每行至少 0.8cm
                row_height = max(0.8*cm, max_lines * 0.6*cm)
                row_heights.append(row_height)
        
        detail_table = Table(detail_data, colWidths=[3*cm, 3*cm, 2.5*cm, 4*cm, 2.5*cm, 2.5*cm], rowHeights=row_heights)
        detail_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # 改為左對齊，更清晰
            ('FONTSIZE', (0, 0), (-1, 0), 12),  # 表頭字體稍大
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            # 添加黑線框
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(detail_table)
        story.append(Spacer(1, 20))  # 減少間距
        
        # 移除總計欄位，因為現在會顯示在簽名區域上方
        
        return story
    
    def _build_receipt_attachment_page(self, data: Dict[str, Any]) -> list:
        """建立單據憑證黏貼單頁面內容"""
        story = []
        styles = getSampleStyleSheet()
        
        # 標題 - 統一樣式，置中對齊
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=5,  # 進一步減少間距
            fontName=self.chinese_font,
            textColor=colors.black
        )
        story.append(Paragraph("單據憑證黏貼單", title_style))
        story.append(Spacer(1, 5))  # 進一步減少間距
        
        # 基本資訊 - 改成左右排放
        info_data = [
            ["請款人", data.get("payee", ""), "申請日期", data.get("application_date", "")]
        ]
        
        info_table = Table(info_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm], rowHeights=[2*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # 改為左對齊，更清晰
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 5))  # 進一步減少間距
        
        # 空白區域說明 - 字體大小跟上面的請款人一樣大
        normal_style = ParagraphStyle(
            'NormalChinese',
            parent=styles['Normal'],
            fontName=self.chinese_font,
            fontSize=14,  # 跟請款人字體大小一致
            spaceAfter=3  # 進一步減少間距
        )
        story.append(Paragraph("請將收據、發票等憑證黏貼於下方空白處", normal_style))
        story.append(Spacer(1, 200))  # 大空白區域
        
        return story
    
    def _build_bank_book_page(self, data: Dict[str, Any]) -> list:
        """建立存摺影本頁面內容"""
        story = []
        styles = getSampleStyleSheet()
        
        # 標題 - 統一樣式，置中對齊
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName=self.chinese_font,
            textColor=colors.black
        )
        story.append(Paragraph("存摺影本", title_style))
        story.append(Spacer(1, 30))
        
        # 如果有上傳圖片，嘗試顯示
        bank_book_image = data.get("bank_book_image")
        if bank_book_image:
            try:
                # 解碼 base64 圖片
                image_data = base64.b64decode(bank_book_image)
                image_buffer = io.BytesIO(image_data)
                
                # 使用 PIL 處理圖片並調整大小
                pil_image = PILImage.open(image_buffer)
                
                # 計算與請款明細表格相同的寬度
                col_widths = [3*cm, 3*cm, 2.5*cm, 4*cm, 2.5*cm, 2.5*cm]
                target_width = sum(col_widths)  # 與請款明細表格同寬
                
                # 獲取原始尺寸
                original_width, original_height = pil_image.size
                
                # 計算等比例縮放
                aspect_ratio = original_width / original_height
                target_height = target_width / aspect_ratio
                
                # 重新打開圖片緩衝區
                image_buffer.seek(0)
                
                # 添加圖片到 PDF，使用固定寬度等比例調整
                img = ReportLabImage(image_buffer, width=target_width, height=target_height)
                story.append(img)
                
            except Exception as e:
                # 如果圖片處理失敗，顯示佔位符
                normal_style = ParagraphStyle(
                    'NormalChinese',
                    parent=styles['Normal'],
                    fontName=self.chinese_font
                )
                story.append(Paragraph(f"存摺影本圖片載入失敗：{str(e)}", normal_style))
        else:
            normal_style = ParagraphStyle(
                'NormalChinese',
                parent=styles['Normal'],
                fontName=self.chinese_font
            )
            story.append(Paragraph("請黏貼存摺影本", normal_style))
        
        return story
    
    def _get_enum_value(self, value) -> str:
        """安全獲取枚舉值的字符串表示"""
        if hasattr(value, 'value'):
            return str(value.value)
        elif isinstance(value, str):
            return value
        return str(value) if value else ""
    
    def _get_simplified_display(self, value) -> str:
        """獲取簡化的顯示文字（用於表格內顯示）"""
        if hasattr(value, 'value'):
            value_str = str(value.value)
        elif isinstance(value, str):
            value_str = value
        else:
            value_str = str(value) if value else ""
        
        # 專案類型簡化
        if "A.會議" in value_str:
            return "A"
        elif "B.活動" in value_str:
            return "B"
        elif "C.志工培訓" in value_str:
            return "C"
        elif "D.學校訪談" in value_str:
            return "D"
        elif "E.專案補助" in value_str:
            return "E"
        elif "F.其他" in value_str:
            return "F"
        
        # 費用類型簡化
        elif "1.交通費" in value_str:
            return "1"
        elif "2.場地租借" in value_str:
            return "2"
        elif "3.餐費" in value_str:
            return "3"
        elif "4.文宣" in value_str:
            return "4"
        elif "5.電話費" in value_str:
            return "5"
        elif "6.補助" in value_str:
            return "6"
        elif "7.志工津貼" in value_str:
            return "7"
        elif "8.設備器材" in value_str:
            return "8"
        elif "9.雜支" in value_str:
            return "9"
        
        # 如果沒有匹配，返回原值
        return value_str
    
    def _get_payment_method_display(self, data: Dict[str, Any]) -> str:
        """取得付款方式顯示文字"""
        method = data.get("payment_method")
        method_value = self._get_enum_value(method)
        if method_value == "其他":
            return f"{method_value} ({data.get('payment_method_other', '')})"
        return method_value
    
    def _get_requesting_unit_display(self, data: Dict[str, Any]) -> str:
        """取得請款單位顯示文字"""
        unit = data.get("requesting_unit")
        unit_value = self._get_enum_value(unit)
        if unit_value == "其他":
            return f"{unit_value} ({data.get('requesting_unit_other', '')})"
        return unit_value
    
    def _needs_bank_book_page(self, data: Dict[str, Any]) -> bool:
        """判斷是否需要存摺影本頁面"""
        payment_method = data.get("payment_method")
        return payment_method in [PaymentMethod.TRANSFER.value, PaymentMethod.ADVANCE.value] 

    def _wrap_text(self, text: str, max_chars: int) -> str:
        """將文字按指定字數換行"""
        if len(text) <= max_chars:
            return text
        
        # 每 max_chars 個字插入換行符
        wrapped_text = ""
        for i in range(0, len(text), max_chars):
            wrapped_text += text[i:i+max_chars] + "\n"
        
        return wrapped_text.strip()
    
    def _calculate_required_pages(self, data: Dict[str, Any]) -> int:
        """計算請款明細表格需要的頁數"""
        # 計算表格的實際高度
        details = data.get("payment_details", [])
        if len(details) == 0:
            return 1
        
        # 計算表格高度：標題行 + 資料行 + 說明文字
        header_height = 1.2 * cm  # 標題行高度
        note_height = 2 * cm  # 說明文字高度
        
        # 計算每行的實際高度（考慮文字換行）
        total_row_height = 0
        for item in details:
            if hasattr(item, 'execution_content'):
                content = item.execution_content
            else:
                content = item["execution_content"] if isinstance(item, dict) else ""
            
            # 計算執行內容的行數（每9個字換一行）
            content_lines = (len(content) + 8) // 9  # 向上取整
            max_lines = max(1, content_lines)
            
            # 每行至少0.8cm，每多一行增加0.6cm
            row_height = max(0.8*cm, max_lines * 0.6*cm)
            total_row_height += row_height
        
        table_height = header_height + total_row_height + note_height
        
        # 可用頁面高度（扣除頁面邊距和簽名區域）
        available_height = A4[1] - 4*cm - 6*cm  # 頁面高度 - 上邊距 - 下邊距
        
        # 計算需要的頁數
        required_pages = max(1, int((table_height + available_height - 1) // available_height))
        return required_pages
    
    def _build_multi_page_payment_request(self, data: Dict[str, Any], required_pages: int) -> list:
        """建立多頁請款單內容"""
        story = []
        
        # 計算所有分頁點
        split_indices = self._calculate_split_indices(data, required_pages)
        
        # 檢查分頁點數量
        if len(split_indices) < 2:
            # 如果只有一個分頁點，說明內容不需要分頁
            story.extend(self._build_payment_request_page_part1(data, split_indices[0]))
            return story
        
        # 第一頁：標題、基本資訊、表格第一部分
        story.extend(self._build_payment_request_page_part1(data, split_indices[0]))
        
        # 後續頁面：每頁都包含表格部分、總計和簽名區域
        for i in range(1, len(split_indices)):
            story.append(PageBreak())
            if i == len(split_indices) - 1:
                # 最後一頁：表格最後部分
                story.extend(self._build_payment_request_page_continuation(data, split_indices[i-1], split_indices[i], is_last=True))
            else:
                # 中間頁面：表格中間部分
                story.extend(self._build_payment_request_page_continuation(data, split_indices[i-1], split_indices[i], is_last=False))
        
        return story
    
    def _calculate_split_indices(self, data: Dict[str, Any], required_pages: int) -> list:
        """計算所有分頁點"""
        details = data.get("payment_details", [])
        if len(details) == 0:
            return [0]
        
        # 可用頁面高度（扣除頁面邊距和簽名區域）
        available_height = A4[1] - 4*cm - 6*cm
        
        # 第一頁已用高度：標題 + 基本資訊 + 請款明細標題 + 說明文字
        first_page_used_height = 28*cm + 2.4*cm + 1.8*cm + 2*cm + 2*cm  # 預估已用高度
        
        # 中間頁面可用高度（只有表格）
        middle_page_available_height = available_height - 4*cm  # 扣除上方4cm間距
        
        split_indices = []
        current_index = 0
        current_height = 0
        is_first_page = True
        
        for i, item in enumerate(details):
            if hasattr(item, 'execution_content'):
                content = item.execution_content
            else:
                content = item["execution_content"] if isinstance(item, dict) else ""
            
            # 計算執行內容的行數（每9個字換一行）
            content_lines = (len(content) + 8) // 9  # 向上取整
            max_lines = max(1, content_lines)
            
            # 每行至少0.8cm，每多一行增加0.6cm
            row_height = max(0.8*cm, max_lines * 0.6*cm)
            
            # 如果是第一行，還要加上標題行高度
            if current_index == 0:
                row_height += 1.2*cm
            
            current_height += row_height
            
            # 檢查是否需要分頁
            max_height = first_page_used_height if is_first_page else middle_page_available_height
            if current_height > max_height:
                split_indices.append(i)
                current_index = i
                current_height = row_height
                is_first_page = False
        
        # 添加最後一個分頁點
        split_indices.append(len(details))
        
        return split_indices
    
    def _build_paginated_payment_request(self, data: Dict[str, Any]) -> list:
        """建立分頁的請款單內容"""
        story = []
        
        # 計算分頁點
        split_index = self._calculate_split_index(data)
        
        # 第一頁：標題、基本資訊、表格前半部分
        story.extend(self._build_payment_request_page_part1(data, split_index))
        
        # 第二頁：表格後半部分、總計、簽名區域
        story.append(PageBreak())
        story.extend(self._build_payment_request_page_part2(data, split_index))
        
        return story
    
    def _build_payment_request_page_continuation(self, data: Dict[str, Any], start_index: int, end_index: int, is_last: bool = False) -> list:
        """建立請款單延續頁面內容（表格部分、總計、簽名區域）"""
        story = []
        
        # 表格距離上方邊緣4cm
        story.append(Spacer(1, 4*cm))
        
        # 表格部分
        details = data.get("payment_details", [])
        page_details = details[start_index:end_index]
        
        if page_details:
            detail_headers = ["專案", "費用類型", "執行時間", "執行內容", "金額", "備註憑證"]
            detail_data = [detail_headers]
            
            for item in page_details:
                if hasattr(item, 'project_type'):
                    project_text = self._get_simplified_display(item.project_type)
                    expense_text = self._get_simplified_display(item.expense_type)
                    row = [
                        project_text,
                        expense_text,
                        item.execution_time or "",
                        self._wrap_text(item.execution_content, 9),
                        f"NT$ {format_currency(float(item.amount))}",
                        ""
                    ]
                else:
                    project_text = self._get_simplified_display(item["project_type"])
                    expense_text = self._get_simplified_display(item["expense_type"])
                    row = [
                        project_text,
                        expense_text,
                        item["execution_time"] if isinstance(item, dict) else "",
                        self._wrap_text(item["execution_content"], 9),
                        f"NT$ {format_currency(float(item['amount']))}",
                        ""
                    ]
                detail_data.append(row)
            
            # 計算行高
            row_heights = []
            for i, row in enumerate(detail_data):
                if i == 0:
                    row_heights.append(1.2*cm)
                else:
                    max_lines = 1
                    for cell_text in row:
                        if cell_text:
                            lines = cell_text.count('\n') + 1
                            max_lines = max(max_lines, lines)
                    row_height = max(0.8*cm, max_lines * 0.6*cm)
                    row_heights.append(row_height)
            
            detail_table = Table(detail_data, colWidths=[3*cm, 3*cm, 2.5*cm, 4*cm, 2.5*cm, 2.5*cm], rowHeights=row_heights)
            detail_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(detail_table)
        
        # 每頁都添加總計和簽名區域（通過canvas繪製）
        # 注意：總計和簽名區域會在add_page_elements中自動繪製
        
        return story
    

    
    def _calculate_split_index(self, data: Dict[str, Any]) -> int:
        """計算表格分頁點"""
        details = data.get("payment_details", [])
        if len(details) == 0:
            return 0
        
        # 可用頁面高度（扣除頁面邊距和簽名區域）
        available_height = A4[1] - 4*cm - 6*cm
        
        # 第一頁已用高度：標題 + 基本資訊 + 請款明細標題 + 說明文字
        used_height = 28*cm + 2.4*cm + 1.8*cm + 2*cm + 2*cm  # 預估已用高度
        
        # 計算每行的實際高度
        current_height = 0
        for i, item in enumerate(details):
            if hasattr(item, 'execution_content'):
                content = item.execution_content
            else:
                content = item.get("execution_content", "")
            
            # 計算執行內容的行數（每9個字換一行）
            content_lines = (len(content) + 8) // 9  # 向上取整
            max_lines = max(1, content_lines)
            
            # 每行至少0.8cm，每多一行增加0.6cm
            row_height = max(0.8*cm, max_lines * 0.6*cm)
            
            # 如果是第一行，還要加上標題行高度
            if i == 0:
                row_height += 1.2*cm
            
            current_height += row_height
            
            # 如果超過可用高度，返回分頁點
            if current_height > (available_height - used_height):
                return i
        
        # 如果所有行都能放在第一頁，返回最後一行的索引
        return len(details)
    
    def _build_payment_request_page_part1(self, data: Dict[str, Any], split_index: int) -> list:
        """建立請款單第一頁內容（標題、基本資訊、表格前半部分）"""
        story = []
        styles = getSampleStyleSheet()
        
        # 標題
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            alignment=TA_CENTER,
            spaceAfter=15,
            fontName=self.chinese_font,
            textColor=colors.black
        )
        story.append(Paragraph("請款單", title_style))
        story.append(Spacer(1, 10))
        
        # 基本資訊表格 - 移除建立時間欄位
        basic_info_data = [
            ["申請日期", data.get("application_date", "") or "（未填寫）", "請款單位", self._get_requesting_unit_display(data)],
            ["受款人", data.get("payee", ""), "付款方式", self._get_payment_method_display(data)],
            ["請款金額", f"NT$ {format_currency(float(data.get('total_amount', 0)))}", "", ""]
        ]
        
        basic_info_table = Table(basic_info_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm], rowHeights=[0.8*cm]*3)
        basic_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (0, -1), 13),
            ('FONTSIZE', (2, 0), (2, -1), 13),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(basic_info_table)
        story.append(Spacer(1, 8))
        
        # 請款明細標題
        heading2_style = ParagraphStyle(
            'Heading2Chinese',
            parent=styles['Heading2'],
            fontName=self.chinese_font,
            fontSize=18,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=8,
            spaceBefore=5
        )
        story.append(Paragraph("請款明細", heading2_style))
        story.append(Spacer(1, 5))
        
        # 說明文字
        note_style = ParagraphStyle(
            'NoteStyle',
            parent=styles['Normal'],
            fontName=self.chinese_font,
            fontSize=11,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=5,
            spaceBefore=2
        )
        
        project_note = "專案：A.會議(理監事會議、審查會議、幹事會議等) B.活動(含年會、各項座談會、年度志工激勵活動、各區學生輔導活動等) C.志工培訓(含志工會議) D.學校訪談 E.專案補助 F.其他"
        story.append(Paragraph(project_note, note_style))
        
        expense_note = "費用類型：1.交通費 2.場地租借 3.餐費 4.文宣 5.電話費 6.補助 7.志工津貼 8.設備器材(含軟硬體) 9.雜支"
        story.append(Paragraph(expense_note, note_style))
        
        story.append(Spacer(1, 8))
        
        # 表格前半部分（根據分頁點）
        details = data.get("payment_details", [])
        first_page_details = details[:split_index]
        
        detail_headers = ["專案", "費用類型", "執行時間", "執行內容", "金額", "備註憑證"]
        detail_data = [detail_headers]
        
        for item in first_page_details:
            if hasattr(item, 'project_type'):
                project_text = self._get_simplified_display(item.project_type)
                expense_text = self._get_simplified_display(item.expense_type)
                row = [
                    project_text,
                    expense_text,
                    item.execution_time or "",
                    self._wrap_text(item.execution_content, 9),
                    f"NT$ {format_currency(float(item.amount))}",
                    ""
                ]
            else:
                project_text = self._get_simplified_display(item["project_type"])
                expense_text = self._get_simplified_display(item["expense_type"])
                row = [
                    project_text,
                    expense_text,
                    item.get("execution_time", ""),
                    self._wrap_text(item["execution_content"], 9),
                    f"NT$ {format_currency(float(item['amount']))}",
                    ""
                ]
            detail_data.append(row)
        
        # 計算行高
        row_heights = []
        for i, row in enumerate(detail_data):
            if i == 0:
                row_heights.append(1.2*cm)
            else:
                max_lines = 1
                for cell_text in row:
                    if cell_text:
                        lines = cell_text.count('\n') + 1
                        max_lines = max(max_lines, lines)
                row_height = max(0.8*cm, max_lines * 0.6*cm)
                row_heights.append(row_height)
        
        detail_table = Table(detail_data, colWidths=[3*cm, 3*cm, 2.5*cm, 4*cm, 2.5*cm, 2.5*cm], rowHeights=row_heights)
        detail_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(detail_table)
        
        return story
    
 