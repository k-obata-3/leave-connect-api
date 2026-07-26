import sys
import math
import openpyxl
from django.conf import settings
from reportlab.platypus import SimpleDocTemplate,Table, TableStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A1, A2, A3, A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

class PdfReport:
  def make(output_data, pdf_file, date_now):
    pdf_canvas = PdfReport.set_info(pdf_file)
    PdfReport.print_string(output_data, pdf_canvas, date_now)
    pdf_canvas.save() # pdfを保存

  def set_info(pdf_file):
    pdf_canvas = canvas.Canvas(pdf_file, pagesize=landscape(A2))
    # ファイル情報の登録（任意）
    pdf_canvas.setAuthor("")  # 作者
    pdf_canvas.setTitle("")   # 表題
    pdf_canvas.setSubject("") # 件名
    return pdf_canvas

  def print_string(output_data, pdf_canvas, date_now):
    # フォント登録
    pdfmetrics.registerFont(TTFont("NotoSansJP","fonts/NotoSansJP-VariableFont_wght.ttf"))
    FONT_NOTO_SANS_JP = 'NotoSansJP'
    PADDING = 20*mm

    # 用紙サイズ定義
    pdf_width, pdf_height = landscape(A2)

    draw_area_height = pdf_height - PADDING
    font_size_title = 14
    font_size_create_date = 10
    table_draw_top_first_page = draw_area_height - font_size_title - 10*mm
    # table_draw_top = draw_area_height - font_size_title - 10*mm

    # # タイトル描画
    # pdf_canvas.setFont(FONT_NOTO_SANS_JP, font_size_title)
    # pdf_canvas.drawString(PADDING, draw_area_height - font_size_title, '年次有給休暇取得管理台帳')
    # # 作成日描画
    # pdf_canvas.setFont(FONT_NOTO_SANS_JP, font_size_create_date)
    # pdf_canvas.drawRightString(pdf_width - PADDING, draw_area_height - font_size_title, text='{0}年{1}月{2}日現在'.format(date_now.year, date_now.month, date_now.day))
    # 氏名/入社日 描画
    user_info_fot_size_header = 12
    user_info_header_height = 10
    user_info = ['氏 名', output_data['user_details']['name'], '入社日', output_data['user_details']['joining_date']]
    table = Table([user_info], colWidths=(20*mm, 100*mm, 20*mm, 30*mm), rowHeights=user_info_header_height*mm)
    table.setStyle(TableStyle([
      ('FONT', (0, 0), (-1, -1), FONT_NOTO_SANS_JP, user_info_fot_size_header),
      ('BOX', (0, 0), (-1, -1), 1, colors.black),
      ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
      ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
      ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]))

    page_num = 1
    chunk = 10
    repeat_num = len(output_data['data'])
    total_page = math.ceil(repeat_num / chunk)
    for chunk_num in range(0, repeat_num):
      if page_num > total_page:
        return

      table_draw_top_first_page = draw_area_height - font_size_title - 10*mm
      # タイトル描画
      pdf_canvas.setFont(FONT_NOTO_SANS_JP, font_size_title)
      pdf_canvas.drawString(PADDING, draw_area_height - font_size_title, '年次有給休暇取得管理台帳')
      # 作成日描画
      pdf_canvas.setFont(FONT_NOTO_SANS_JP, font_size_create_date)
      pdf_canvas.drawRightString(pdf_width - PADDING, draw_area_height - font_size_title, text='{0}年{1}月{2}日現在'.format(date_now.year, date_now.month, date_now.day))

      # table_draw_top_first_page -= user_info_header_height*mm + 5*mm
      if page_num == 1:
        table.wrapOn(pdf_canvas, PADDING, table_draw_top_first_page - user_info_header_height*mm)
        table.drawOn(pdf_canvas, PADDING, table_draw_top_first_page - user_info_header_height*mm)
        table_draw_top_first_page -= user_info_header_height*mm + 5*mm

      start = chunk_num*chunk
      end = start + chunk if chunk_num != repeat_num - 1 else None
      temp_list = output_data['data'][start:end]
      if len(temp_list) > 0:
        # テーブル描画
        # top = table_draw_top_first_page if page_num == 1 else draw_area_height
        top = table_draw_top_first_page
        PdfReport.print_table(temp_list, pdf_canvas, top, pdf_width)

        pdf_canvas.setFont(FONT_NOTO_SANS_JP, font_size_title)
        pdf_canvas.drawString(pdf_width / 2, font_size_title, "{}/{}".format(page_num ,total_page))

        # ページ描画
        pdf_canvas.showPage()
        page_num += 1

  def print_table(output_data, pdf_canvas, table_draw_top, pdf_width):
    FONT_NOTO_SANS_JP = 'NotoSansJP'

    fot_size_header = 12
    header_data = [
      ['勤続\n月数', '対象期間', '付与日数\n全休/半休合計\n時間単位合計', '取得日\n区分\n取得時間'],
    ]

    header_height = 18
    table = Table(header_data, colWidths=(12*mm, 27*mm, 35*mm, 480*mm), rowHeights=header_height*mm)
    table.setStyle(TableStyle([
      ('FONT', (0, 0), (-1, -1), FONT_NOTO_SANS_JP, fot_size_header),
      ('BOX', (0, 0), (-1, -1), 1, colors.black),
      ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
      ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
      ("ALIGN", (0,0), (-1,-1), "CENTER"),
      # ('SPAN', (0, 0), (0, 1)),
      # ('SPAN', (1, 0), (1, 1)),
      # ('SPAN', (2, 0), (2, 1)),
      # ('SPAN', (3, 0), (3, 1)),
    ]))

    table_draw_left = (pdf_width - sum(table._colWidths)) / 2

    table.wrapOn(pdf_canvas, 0, table_draw_top - header_height*mm)
    table.drawOn(pdf_canvas, table_draw_left, table_draw_top - header_height*mm)

    data = []
    acquisition_date_col = [''] * 20
    for row_index, row in enumerate(output_data):
      row_result_1 = [row['elapsed_month'], '{0}\n～\n{1}'.format(row['period']['start_date'], row['period']['end_date']), "{}日".format(row['grant_rule_add_days'])]
      row_result_2 = ['', '', "{}日".format(row['current_year_total_delete_days'])]
      row_result_3 = ['', '', "{}時間".format(row['current_year_total_delete_time_hour_unit'])]
      for col_index, col in enumerate(acquisition_date_col):
        if len(row['acquisition_results']) > col_index:
          row_result_1.append(row['acquisition_results'][col_index]['acquisition_date'])
          classification_name = row['acquisition_results'][col_index]['classification_name']
          if row['acquisition_results'][col_index]['type'] == settings.PAID_HOLIDAY_REGULATE_TYPE_VALUE:
            classification_name = "{}\n(調整)".format(classification_name)
          row_result_2.append(classification_name)
          row_result_3.append("{}時間".format(row['acquisition_results'][col_index]['total_time']))
        else:
          row_result_1.append(col)
          row_result_2.append(col)
          row_result_3.append(col)
      data.append(row_result_1)
      data.append(row_result_2)
      data.append(row_result_3)

    row_height = 10*mm
    table = Table(data, colWidths=(12*mm, 27*mm, 35*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm, 24*mm), rowHeights=row_height)

    table_styles = [
      ('FONT', (0, 0), (-1, -1), FONT_NOTO_SANS_JP, 11),
      ('BOX', (0, 0), (-1, -1), 1, colors.black),
      ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
      ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
      ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]
    for i in range(len(data)):
      if i % 3 == 0:
        table_styles.append(
          ('SPAN', (0, i), (0, i + 2)),
        )
        table_styles.append(
          ('SPAN', (1, i), (1, i + 2)),
        )
      # elif i % 3 == 1:
      #   for j in range(len(data[i])):
      #     if j > 2:
      #       table_styles.append(
      #         ('SPAN', (j, i), (j, i + 1)),
      #       )

    table.setStyle(TableStyle(table_styles))
    table.wrapOn(pdf_canvas, 0, table_draw_top - header_height*mm - row_height * len(data))
    table.drawOn(pdf_canvas, table_draw_left, table_draw_top - header_height*mm - row_height * len(data))


  def excelToPdf(excel_file, pdf_file):
    try:
      workBook = openpyxl.load_workbook('{0}/{1}'.format('test', excel_file))
    except FileNotFoundError:
      print("ファイル読み込みエラー")
      sys.exit()
    sheet = workBook.active 
    document = SimpleDocTemplate(pdf_file, pagesize=A1)
    pdfmetrics.registerFont(TTFont("NotoSansJP","fonts/NotoSansJP-VariableFont_wght.ttf"))

    elements = []
    tableData = []
    for row in sheet.rows:#行ループ
      recordList = []
      for cell in row: #列ループ
        recordList.append(cell.value)
      tableData.append(recordList)
      table=Table(tableData)

      table.setStyle(TableStyle([ 
        ('BACKGROUND',(0,0),(-1,0),colors.lightgreen), #1行目セル背景色変更
        ("ALIGN", (0,0),(-1,0), "CENTER"), #1行目中央寄せ
        ("ALIGN", (0,1), (0,-1), "RIGHT"), #1列目右寄せ
        ("ALIGN", (2,1), (2,-1), "RIGHT"), #3列目右寄せに
        ('TEXTCOLOR',(0,0),(1,-1),colors.black), #1,2列目文字色変更
        # ('FONT', (0, 0), (-1, -1), "GenShinGothic-Normal", 20), #全体のフォントとフォントサイズ設定
        ('FONT', (0, 0), (-1, -1), "NotoSansJP", 20), #全体のフォントとフォントサイズ設定
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),])) #全体のケイ線の設定
      elements.append(table) 
      try:
        document.build(elements) #PDFの書き出し
      except FileNotFoundError:
        print("出力エラー")
        sys.exit()

    return

  def make_test(pdf_file="resume"): # ファイル名の設定
    pdf_canvas = PdfReport.set_info_test(pdf_file) # キャンバス名の設定
    PdfReport.print_string_test(pdf_canvas)
    pdf_canvas.save() # pdfを保存

  def set_info_test(filename):
    pdf_canvas = canvas.Canvas(filename) # 保存先の設定
    # ファイル情報の登録（任意）
    pdf_canvas.setAuthor("") # 作者
    pdf_canvas.setTitle("") # 表題
    pdf_canvas.setSubject("") # 件名
    return pdf_canvas

  def print_string_test(pdf_canvas):
    # フォント登録
    pdfmetrics.registerFont(TTFont("NotoSansJP","fonts/NotoSansJP-VariableFont_wght.ttf"))
    FONT_NOTO_SANS_JP = 'NotoSansJP'

    # 用紙サイズ定義（この場合はA4）
    width, height = A4

    # フォントサイズ定義（この場合は24）
    font_size = 24
    pdf_canvas.setFont(FONT_NOTO_SANS_JP, font_size)

    # (1)履歴書 タイトル
    font_size = 24 # フォントサイズ
    pdf_canvas.setFont(FONT_NOTO_SANS_JP, font_size)
    pdf_canvas.drawString(60, 770, '履  歴  書') # 書き出し(横位置, 縦位置, 文字)
    
    # (2)作成日
    font_size = 10
    pdf_canvas.setFont(FONT_NOTO_SANS_JP, font_size)
    pdf_canvas.drawString(285, 770,  '    年         月         日現在')

    # (3)証明写真
    # tableを作成
    data = [
            ['    証明写真'],
        ]
    table = Table(data, colWidths=30*mm, rowHeights=40*mm) # tableの大きさ
    table.setStyle(TableStyle([                              # tableの装飾
            ('FONT', (0, 0), (0, 0), FONT_NOTO_SANS_JP, 12), # フォントサイズ
            ('BOX', (0, 0), (0, 0), 1, colors.black),        # 罫線
            ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),            # フォント位置
        ]))
    table.wrapOn(pdf_canvas, 145*mm, 235*mm) # table位置
    table.drawOn(pdf_canvas, 145*mm, 235*mm)

    # (4) プロフィール
    data = [
            ['ふりがな','   男  ・  女'],  
            ['氏名',''],
            ['生年月日　　　　　　　　　　　　　　　　　　　　年　　　月　　　日生　（満　　　歳）',''],    
        ]
    table = Table(data, colWidths=(100*mm,20*mm), rowHeights=(7*mm, 20*mm, 7*mm))
    table.setStyle(TableStyle([
            ('FONT', (0, 0), (1, 2), FONT_NOTO_SANS_JP, 8),
            ('BOX', (0, 0), (1, 2), 1, colors.black),
            ('INNERGRID', (0, 0), (1, 2), 1, colors.black),
            ('SPAN',(0, 2), (1, 2)),
            ('SPAN',(1, 0), (1, 1)),
            ('VALIGN', (0, 0), (1, 2), 'MIDDLE'),
            ('VALIGN', (0, 1), (0, 1),'TOP'),
        ]))
    table.wrapOn(pdf_canvas, 20*mm, 232*mm)
    table.drawOn(pdf_canvas, 20*mm, 232*mm)

    # (5)住所
    data = [
            ['ふりがな', '電話'],
            ['連絡先（〒　　　ー　　　　）', 'E-mail'],
            ['ふりがな', '電話'],
            ['連絡先（〒　　　ー　　　　）', 'E-mail'],
        ]
    table = Table(data, colWidths=(120*mm, 40*mm), rowHeights=(7*mm,20*mm,7*mm,20*mm))
    table.setStyle(TableStyle([
            ('FONT', (0, 0), (1, 3), FONT_NOTO_SANS_JP, 9),
            ('BOX', (0, 0), (1, 3), 1, colors.black),
            ('INNERGRID', (0, 0), (1, 3), 1, colors.black),
            ('VALIGN', (0, 0), (1, 2), 'MIDDLE'),
            ('VALIGN', (0, 1), (1, 1), 'TOP'),
            ('VALIGN', (0, 3), (1, 3), 'TOP'),
        ]))
    table.wrapOn(pdf_canvas, 20*mm, 178*mm)
    table.drawOn(pdf_canvas, 20*mm, 178*mm)

    # (6)学歴・職歴
    data = [
            ['        年', '   月', '                                            学歴・職歴'],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' ']
        ]
    table = Table(data, colWidths=(25*mm, 14*mm, 121*mm), rowHeights=7.5*mm)
    table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), FONT_NOTO_SANS_JP, 11),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
    table.wrapOn(pdf_canvas, 20*mm, 20*mm)
    table.drawOn(pdf_canvas, 20*mm, 20*mm)

    # 1枚目終了
    pdf_canvas.showPage()

    # (7)学歴・職歴、免許・資格
    data = [ 
            ['        年', '   月', '                                            学歴・職歴'],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            ['        年', '   月', '                                            免許・資格'],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
            [' ', ' ', ' '],
        ]
    table = Table(data, colWidths=(25*mm, 14*mm, 121*mm), rowHeights=7.5*mm)
    table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), FONT_NOTO_SANS_JP, 11),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
    table.wrapOn(pdf_canvas, 20*mm, 132*mm)
    table.drawOn(pdf_canvas, 20*mm, 132*mm)
   
    # (8)そのほか
    data = [
            ['志望の動機、自己PR、趣味、特技など','通勤時間',''],
            ['','                        約　　　　時間　　　　分',''],
            ['','扶養家族（配偶者を除く）',''],
            ['','                              　　　　    　　　　人',''],
            ['','配偶者','配偶者の扶養義務'],
            ['','       有    ・    無','       有    ・    無'],
            ['本人希望記入欄（特に待遇・職種・勤務時間・その他についての希望などがあれば記入）','',''],
            ['','','']

        ]
    table = Table(data, colWidths=(90*mm, 35*mm, 35*mm), rowHeights=(8*mm, 10*mm, 8*mm, 10*mm, 8*mm, 10*mm, 8*mm, 50*mm))
    table.setStyle(TableStyle([
            ('FONT', (0, 0), (2, 7), FONT_NOTO_SANS_JP, 10),
            ('BOX', (0, 0), (2, 7), 1, colors.black),
            ('LINEBEFORE', (1, 0), (1, 5), 1, colors.black),
            ('LINEBEFORE', (2, 4), (2, 5), 1, colors.black),
            ('LINEABOVE', (1, 2), (2, 2), 1, colors.black),
            ('LINEABOVE', (1, 4), (2, 4), 1, colors.black),
            ('LINEABOVE', (0, 6), (2, 6), 1, colors.black),
            ('LINEABOVE', (0, 7), (2, 7), 1, colors.black),
            ('VALIGN', (0, 0), (2, 5), 'TOP'),
            ('VALIGN', (0, 6), (2, 6), 'MIDDLE'),
        ]))
    table.wrapOn(pdf_canvas, 20*mm, 20*mm)
    table.drawOn(pdf_canvas, 20*mm, 20*mm)

    # 2枚目終了
    pdf_canvas.showPage()
