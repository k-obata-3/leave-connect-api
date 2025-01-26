import os
import openpyxl
import datetime

from config.utils import Utils
from config.enum import CareerItemKey

class ExcelReportWithOpenpyxl:
  tag_row_start = '%row_start%'
  tag_row_end = '%row_end%'
  tag_ud_date = '%ud_date%'
  tag_name_kana = '%name_kana%'
  tag_name = '%name%'
  tag_birthday = '%birthday%'
  tag_age = '%age%'
  tag_seq = '%seq%'
  tag_project_name = '%project_name%'
  tag_overview = '%overview%'
  tag_model = '%model%'
  tag_os = '%os%'
  tag_db = '%db%'
  tag_lang_tool = '%lang_tool%'
  tag_cn = '%cn%'
  tag_sa = '%sa%'
  tag_sd = '%sd%'
  tag_pd = '%pd%'
  tag_pg = '%pg%'
  tag_st = '%st%'
  tag_op = '%op%'
  tag_other = '%other%'
  tag_pm = '%pm%'
  tag_pl = '%pl%'
  tag_tl = '%tl%'
  tag_start_date = '%start_date%'
  tag_end_date = '%end_date%'
  tag_period = '%period%'
  tag_memo = '%memo%'

  def write(output_data, career_item_dic, user_details, temp_dir_path):
    output_date = Utils.get_now_to_datetime()

    # テンプレートファイルを読み込む
    workbook = openpyxl.load_workbook(os.getcwd() + '/' + 'template.xlsx')
    # 作成者
    workbook.properties.creator = '株式会社メディアプロ'
    # 前回保存者
    workbook.properties.lastModifiedBy = '株式会社メディアプロ'

    # Excelのプロパティ情報書き換え時のみsettings.pyのタイムゾーン設定が効かないのでnowで日本時間が取得できない
    DIFF_JST_FROM_UTC = -9
    properties_date = datetime.datetime.now() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)

    # コンテンツの作成日時
    workbook.properties.created = properties_date
    # 前回保存日時
    workbook.properties.modified = properties_date
    # 前回印刷日
    workbook.properties.lastPrinted = properties_date

    # 編集対象のシートを取得
    ws = workbook.active

    row_index = 0
    current_data = None
    for row in ws.iter_rows():
      for cell in row:
        if cell.value is not None:
          tag = ExcelReportWithOpenpyxl.getOutputTag(cell)
          text = None
          if tag == ExcelReportWithOpenpyxl.tag_ud_date:
            text = output_date.strftime('%Y年%m月%d日')
          elif tag == ExcelReportWithOpenpyxl.tag_name_kana:
            text = user_details.last_name_kana + '  ' + user_details.first_name_kana
          elif tag == ExcelReportWithOpenpyxl.tag_name:
            text = user_details.last_name + '  ' + user_details.first_name
          elif tag == ExcelReportWithOpenpyxl.tag_birthday:
            text = user_details.date_of_birth.strftime('%Y年%m月%d日')
          elif tag == ExcelReportWithOpenpyxl.tag_age:
            text = Utils.get_age(user_details.date_of_birth)
          elif tag == ExcelReportWithOpenpyxl.tag_row_start:
            if len(output_data) > row_index: 
              current_data = output_data[row_index]
          elif tag == ExcelReportWithOpenpyxl.tag_row_end:
            row_index += 1
            current_data = None
          elif tag == ExcelReportWithOpenpyxl.tag_seq:
            text = str(row_index + 1)

          if(text is None):
            row_output_data = ExcelReportWithOpenpyxl.getRowOutputData(tag, current_data, career_item_dic)
            text = row_output_data

          if text:
            # テキストがNoneでも空文字でもない場合
            cell.value = cell.value.replace(tag, text)
          elif tag and not text:
            # タグがNoneでも空でもない および テキストがNoneまたは空文字の場合
            cell.value = ''

    file_name = 'スキル表_{0}_{1}.xlsx'.format(user_details.last_name + user_details.first_name, output_date.strftime("%Y%m%d"))
    workbook.save('{0}/{1}'.format(temp_dir_path, file_name))
    workbook.close()

    return file_name

  def getOutputTag(cell):
    tag = None
    if ExcelReportWithOpenpyxl.tag_row_start == cell.value:
      tag = ExcelReportWithOpenpyxl.tag_row_start
    elif ExcelReportWithOpenpyxl.tag_row_end == cell.value:
      tag = ExcelReportWithOpenpyxl.tag_row_end
    elif ExcelReportWithOpenpyxl.tag_ud_date in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_ud_date
    elif ExcelReportWithOpenpyxl.tag_name_kana in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_name_kana
    elif ExcelReportWithOpenpyxl.tag_name in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_name
    elif ExcelReportWithOpenpyxl.tag_birthday in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_birthday
    elif ExcelReportWithOpenpyxl.tag_age in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_age
    elif ExcelReportWithOpenpyxl.tag_seq in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_seq
    elif ExcelReportWithOpenpyxl.tag_project_name in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_project_name
    elif ExcelReportWithOpenpyxl.tag_overview in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_overview
    elif ExcelReportWithOpenpyxl.tag_model in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_model
    elif ExcelReportWithOpenpyxl.tag_os in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_os
    elif ExcelReportWithOpenpyxl.tag_db in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_db
    elif ExcelReportWithOpenpyxl.tag_lang_tool in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_lang_tool
    elif ExcelReportWithOpenpyxl.tag_cn in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_cn
    elif ExcelReportWithOpenpyxl.tag_sa in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_sa
    elif ExcelReportWithOpenpyxl.tag_sd in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_sd
    elif ExcelReportWithOpenpyxl.tag_pd in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_pd
    elif ExcelReportWithOpenpyxl.tag_pg in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_pg
    elif ExcelReportWithOpenpyxl.tag_st in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_st
    elif ExcelReportWithOpenpyxl.tag_op  in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_op
    elif ExcelReportWithOpenpyxl.tag_other in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_other
    elif ExcelReportWithOpenpyxl.tag_pm in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_pm
    elif ExcelReportWithOpenpyxl.tag_pl in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_pl
    elif ExcelReportWithOpenpyxl.tag_tl in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_tl
    elif ExcelReportWithOpenpyxl.tag_start_date in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_start_date
    elif ExcelReportWithOpenpyxl.tag_end_date in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_end_date
    elif ExcelReportWithOpenpyxl.tag_period in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_period
    elif ExcelReportWithOpenpyxl.tag_memo in cell.value:
      tag = ExcelReportWithOpenpyxl.tag_memo

    return tag

  def getRowOutputData(tag, data, careerInfoItemDic):
    text = None
    if data is None:
      return

    dic_key = str(data.id)

    if(tag is not None and data is not None):
        if tag == ExcelReportWithOpenpyxl.tag_project_name:
          text = data.project_name
        elif tag == ExcelReportWithOpenpyxl.tag_overview:
          text = data.overview
        elif tag == ExcelReportWithOpenpyxl.tag_model:
          text = careerInfoItemDic[dic_key][CareerItemKey.MODEL.value]
        elif tag == ExcelReportWithOpenpyxl.tag_os:
          text = careerInfoItemDic[dic_key][CareerItemKey.OS.value]
        elif tag == ExcelReportWithOpenpyxl.tag_db:
          text = careerInfoItemDic[dic_key][CareerItemKey.DATA_BASE.value]
        elif tag == ExcelReportWithOpenpyxl.tag_lang_tool:
          language = careerInfoItemDic[dic_key][CareerItemKey.LANGUAGE.value]
          tool = careerInfoItemDic[dic_key][CareerItemKey.TOOL.value]
          if(language is not None and tool is None):
            text = language
          elif(language is None and tool is not None):
            text = tool
          elif(language is not None and tool is not None):
            text = language + '\n' + tool
        elif tag == ExcelReportWithOpenpyxl.tag_cn:
          text = ExcelReportWithOpenpyxl.getOutputTextFromSelectedData(careerInfoItemDic[dic_key][CareerItemKey.INCHARGE.value], 1)
        elif tag == ExcelReportWithOpenpyxl.tag_sa:
          text = ExcelReportWithOpenpyxl.getOutputTextFromSelectedData(careerInfoItemDic[dic_key][CareerItemKey.INCHARGE.value], 2)
        elif tag == ExcelReportWithOpenpyxl.tag_sd:
          text = ExcelReportWithOpenpyxl.getOutputTextFromSelectedData(careerInfoItemDic[dic_key][CareerItemKey.INCHARGE.value], 3)
        elif tag == ExcelReportWithOpenpyxl.tag_pd:
          text = ExcelReportWithOpenpyxl.getOutputTextFromSelectedData(careerInfoItemDic[dic_key][CareerItemKey.INCHARGE.value], 4)
        elif tag == ExcelReportWithOpenpyxl.tag_pg:
          text = ExcelReportWithOpenpyxl.getOutputTextFromSelectedData(careerInfoItemDic[dic_key][CareerItemKey.INCHARGE.value], 5)
        elif tag == ExcelReportWithOpenpyxl.tag_st:
          text = ExcelReportWithOpenpyxl.getOutputTextFromSelectedData(careerInfoItemDic[dic_key][CareerItemKey.INCHARGE.value], 6)
        elif tag == ExcelReportWithOpenpyxl.tag_op:
          text = ExcelReportWithOpenpyxl.getOutputTextFromSelectedData(careerInfoItemDic[dic_key][CareerItemKey.INCHARGE.value], 7)
        elif tag == ExcelReportWithOpenpyxl.tag_other:
          text = ExcelReportWithOpenpyxl.getOutputTextFromSelectedData(careerInfoItemDic[dic_key][CareerItemKey.INCHARGE.value], 8)
        elif tag == ExcelReportWithOpenpyxl.tag_pm:
          text = ExcelReportWithOpenpyxl.getOutputTextFromSelectedData(careerInfoItemDic[dic_key][CareerItemKey.ROLE.value], 1)
        elif tag == ExcelReportWithOpenpyxl.tag_pl:
          text = ExcelReportWithOpenpyxl.getOutputTextFromSelectedData(careerInfoItemDic[dic_key][CareerItemKey.ROLE.value], 2)
        elif tag == ExcelReportWithOpenpyxl.tag_tl:
          text = ExcelReportWithOpenpyxl.getOutputTextFromSelectedData(careerInfoItemDic[dic_key][CareerItemKey.ROLE.value], 3)
        elif tag == ExcelReportWithOpenpyxl.tag_start_date:
          if data.start_date is None:
            return
          text = data.start_date.strftime('%Y年%m月%d日')
        elif tag == ExcelReportWithOpenpyxl.tag_end_date:
          if data.end_date is None:
            return
          text = data.end_date.strftime('%Y年%m月%d日')
        elif tag == ExcelReportWithOpenpyxl.tag_period:
          if data.start_date is None or data.end_date is None:
            return
          sum_month = (data.end_date.year - data.start_date.year) * 12 + data.end_date.month - data.start_date.month + 1
          month = sum_month % 12
          if sum_month > 12:
            year = sum_month // 12
            text = '{}年{}ヵ月'.format(str(year), str(month))
          else:
            text = '{}ヵ月'.format(str(month))
        elif tag == ExcelReportWithOpenpyxl.tag_memo:
          text = data.other

    return text

  def getOutputTextFromSelectedData(data, expect):
    if(data is not None):
      array = data.split(',')
      if(str(expect) in array):
        return '○'
    return None

if __name__=='__main__':
  ExcelReportWithOpenpyxl.write()