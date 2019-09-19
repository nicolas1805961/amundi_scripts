import csv
import xlsxwriter

values = ["log_sid", "Address", "User_Name", "time_stamp", "date_time", "session_id", "Access_Profile", "Client_Hostname"]

csv.register_dialect('myDialect', delimiter = ',', quoting=csv.QUOTE_MINIMAL)
col = []
file = input("Please enter the file name to format:")
file = file + ".csv"
out_file = input("Please enter the name of the output file:")
out_file = out_file + ".xlsx"
if "vm" not in file:
    values.append("Virtual_IP")
    values.append("Access_Policy_Result")
workbook = xlsxwriter.Workbook(out_file)
worksheet = workbook.add_worksheet()
bold = workbook.add_format({'bold': True})
with open(file, "r") as file_in:
    reader = csv.reader(file_in, dialect = "myDialect")
    data = list(reader)
    new_data = [x for x in data if x != []]
    index_user = new_data[0].index("User_Name")
    for i, j in enumerate(new_data):
        for u, k in enumerate(j):
            if i == 0 and new_data[i][u] not in values:
                col.append(u)
                continue
            if u == index_user and new_data[i][u] == "":
                worksheet.set_row(i, None, None, {"hidden": 1})
            worksheet.write(i, u, k)
    for col_index in col:
        worksheet.set_column(col_index, col_index, None, None, {"hidden": 1})
    worksheet.set_column(0, 30, 20)
    worksheet.set_row(0, None, bold)
workbook.close()