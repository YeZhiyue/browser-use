import pandas as pd
import mysql.connector
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 数据库配置
db_config = {
	'host': 'localhost',
	'user': 'root',
	'password': '',
	'database': 'company_data'
}

# Excel 文件路径
excel_file = '~/Downloads/wmcompany.xlsx'  # 替换为你的 Excel 文件路径
target_sheet = '国家筛选'  # 指定要处理的工作表名称

def import_excel_to_db(excel_file, target_sheet, db_config):
	"""
    将 Excel 文件中的指定工作表导入到 MySQL 数据库中。

    Args:
        excel_file (str): Excel 文件路径。
        target_sheet (str): 要导入的工作表名称。
        db_config (dict): 数据库配置信息。
    """
	try:
		# 连接到数据库
		logging.info("正在尝试连接到数据库...")
		mydb = mysql.connector.connect(**db_config)
		mycursor = mydb.cursor()
		logging.info("成功连接到数据库.")

		# 读取 Excel 文件
		logging.info(f"正在读取 Excel 文件，工作表：{target_sheet}...")
		excel_data = pd.read_excel(excel_file, sheet_name=target_sheet)
		logging.info(f"成功读取 Excel 文件，工作表：{target_sheet}，共 {len(excel_data)} 行数据.")

		# 遍历 DataFrame 的每一行
		logging.info(f"开始处理工作表 '{target_sheet}' 中的数据...")
		for index, row in excel_data.iterrows():
			logging.debug(f"正在处理第 {index + 1} 行数据...")

			# 从行中提取数据
			company_name = row['公司名称'] if pd.notna(row['公司名称']) else None
			company_country = row['公司所属国家/地区'] if pd.notna(row['公司所属国家/地区']) else None
			company_website = row['官网'] if pd.notna(row['官网']) else None
			is_cookware_specialist = row['是否专业锅具'] if pd.notna(row['是否专业锅具']) else False  # Keep the boolean handling
			exhibition_product_category = row['参展产品类别'] if pd.notna(row['参展产品类别']) else None
			exhibition_frequency = row['逛展频次'] if pd.notna(row['逛展频次']) else None
			company_address = row['地址'] if pd.notna(row['地址']) else None
			contact_person = row['联络人'] if pd.notna(row['联络人']) else None
			contact_email = row['联络邮箱'] if pd.notna(row['联络邮箱']) else None
			contact_phone1 = row['联络电话'] if pd.notna(row['联络电话']) else None
			contact_phone2 = row['联络电话.1'] if pd.notna(row['联络电话.1']) else None
			future_exhibitions = row['2025上半年作为采购商身份参加厨具相关展会的公司（全球厨具相关展会）'] if pd.notna(row['2025上半年作为采购商身份参加厨具相关展会的公司（全球厨具相关展会）']) else None

			# 准备 SQL 查询
			sql = """
            INSERT INTO company_info (company_name, company_country, company_website, is_cookware_specialist,
                                        exhibition_product_category, exhibition_frequency, company_address,
                                        contact_person, contact_email, contact_phone1, contact_phone2,
                                        future_exhibitions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

			# 准备要插入的值
			val = (
				company_name,
				company_country,
				company_website,
				is_cookware_specialist,
				exhibition_product_category,
				exhibition_frequency,
				company_address,
				contact_person,
				contact_email,
				contact_phone1,
				contact_phone2,
				future_exhibitions
			)

			# 执行查询
			try:
				mycursor.execute(sql, val)
				logging.debug(f"成功插入第 {index + 1} 行数据到数据库.")
			except Exception as e:
				logging.error(f"插入第 {index + 1} 行数据时发生错误: {e}")

		# 提交更改
		logging.info("正在提交更改到数据库...")
		mydb.commit()
		logging.info(f"工作表 '{target_sheet}' 处理完成. 插入了 {mycursor.rowcount} 条记录.")

	except mysql.connector.Error as err:
		logging.error(f"数据库连接错误: {err}")

	except FileNotFoundError:
		logging.error(f"找不到 Excel 文件: {excel_file}")

	except KeyError as err:
		logging.error(f"在 Excel 文件中找不到列 '{err}'")

	except Exception as err:
		logging.error(f"发生了一个意外错误: {err}")

	finally:
		if mydb and mydb.is_connected():
			mycursor.close()
			mydb.close()
			logging.info("MySQL 连接已关闭")


if __name__ == "__main__":
	"""
    主程序入口。
    """
	import_excel_to_db(excel_file, target_sheet, db_config)
	logging.info("程序执行完毕.")
