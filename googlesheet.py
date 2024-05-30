import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# JSON credentials file path
SERVICE_ACCOUNT_FILE = 'light-legend-215213-d0df0e5cbed5.json'

# Google Sheet ID and name

#SHEET_NAME =  'test_table'
SHEET_ID =  "108P7NGpzitusSBV8eHi7YyjFDf9OIqiw9nCmB5i2LU0"
# Google Sheet credentials setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Connect to the Google Sheets API
client = gspread.authorize(credentials)


async def write_data_to_google_sheet(data, passed_username):
    sheet = client.open_by_key(SHEET_ID)
    #sheet = client.open(SHEET_NAME)

    # Extract month from profit date
    profit_date = data['date']
    month_name = datetime.strptime(profit_date, '%d-%m-%Y').strftime('%B-%Y') if profit_date else 'General'

    # Get or create the sheet for the specific month
    try:
        worksheet = sheet.worksheet(month_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=month_name, rows=1000, cols=10)
        worksheet.update(range_name = 'A1:E1', values = [['Дата расхода', 'сумма расхода', 'описание расхода', 'тип расхода', 'кто внес данные']])
        worksheet.update(range_name = 'G1:I1', values = [['Дата выручки', 'Сумма выручки', 'Кто внес данные']])
        worksheet.format('A1:I1', {'textFormat': {'bold': True}})

    # Prepare expenses data
    expenses_data = list(zip(
        [profit_date] * len(data['ExpensesList']),
        data['ExpensesList'],
        data['ExpensesDescList'],
        data['ExpensesTypeList'],
        [ passed_username ] * len(data['ExpensesList'])
    ))

    # Add expenses data to the worksheet
    expenses_records = worksheet.get_all_records(head=1)
    expenses_start_row = len(expenses_records) + 2
    worksheet.update(
        range_name=f"A{expenses_start_row}:E{expenses_start_row + len(expenses_data) - 1}",
        values=expenses_data
    )

    # Prepare profits data
    if data['Total_profit']:
        profit_data = [[profit_date, data['Total_profit'], passed_username ]]
        profit_records = worksheet.get_all_records(head=1, default_blank='')
        profit_start_row = len(profit_records) + 2
        worksheet.update(
            range_name=f'G{profit_start_row}:I{profit_start_row + len(profit_data) - 1}',
            values=profit_data
        )

    def get_range_size(cell_range):
        if not cell_range:
            return 0, 0

        start_col = cell_range[0].col
        start_row = cell_range[0].row
        end_col = cell_range[-1].col
        end_row = cell_range[-1].row

        rows = end_row - start_row + 1
        cols = end_col - start_col + 1
        return rows, cols
    # Sorting logic
    def sort_by_date_range(column_range):
        # Extract data range
        data_range = worksheet.range(column_range)
        columns_ammount = get_range_size(data_range)[1]

        # Convert to matrix
        rows = len(data_range) // columns_ammount
        matrix = [[data_range[i * columns_ammount + j].value for j in range(columns_ammount)] for i in range(rows)]
        # Sort matrix by date
        matrix.sort(key=lambda x: datetime.strptime(x[0], '%d-%m-%Y') if x[0] else datetime.max)
        # Update the worksheet
        for i, row in enumerate(matrix):
            for j, cell in enumerate(row):
                data_range[i * columns_ammount + j].value = cell
        worksheet.update_cells(data_range)

    sort_by_date_range(f'A2:E{expenses_start_row + len(expenses_data) - 1}')
    if data['Total_profit']:
        sort_by_date_range(f'G2:I{profit_start_row + 1}')


    # number_format = {
    #     "numberFormat": {
    #         "type": "CURRENCY",
    #         "pattern": "#,##0.00"
    #     }
    # }
    #
    # worksheet.format("B2:B1000",  number_format )
    # worksheet.format("H2:H1000", number_format)
# Example JSON input
json_input = '''{
    "date": "01-05-2024",
    "Total_profit": "10000",
    "ExpensesList": [19000, 14000, 10000, 10000, 1000],
    "ExpensesDescList": ["Рамки для картин в 3х4, Банки, крючки, канистры", "Ключи", "зп Васе", "клей, пластины", "Провод 40м"],
    "ExpensesTypeList": ["Закупки прочее", "Закупки прочее", "Зарплата бармена, охраны", "Закупки прочее", "Закупки ремонт и стройка"],
    "Not_shure_flag": "No"
}'''

# Example usage
# data = json.loads(json_input)
# write_data_to_google_sheet(data, 'Петрович'  )