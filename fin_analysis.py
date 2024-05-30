# fin_analysis.py


from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o", temperature=0.0)

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime

from langchain.output_parsers.json import SimpleJsonOutputParser

#print(res1)


examples_text = """
Example 1:
03.05
-13к Арман
-10к Женя
-15к Коля
-18к Даня
-1к лед
-1к дед
-5к уборщица
Выручка нал 263к
Карты 
Переводы 165 500
Всего 428 500 (без отчета по картам)

Example 2:
06.05
Начало 40000
-1000 лед
-1000 дед
Конец дня:
+ 307000 нал
+ 12100 перевод
Итог: 319100
-15000 Раф



Example 3:
07.05
Начало 40000
-25000 palanjyan raspberry
-1000 Dead
Конец дня:
+ 124000 нал
+ 67100 перевод
Итог: 191100
-15000 Раф

Example 4:
9.05
-18к Даня
-40к Гриша
-5к уборщица
-21 300 Гриша
-15к Раф
Выручка нал 417 к
Переводы 164600
Всего 581 600

Example 5:
Потратил 10000 на Петю

Example 6:
Потратил на закупки 14к

Example 7:
Коллеги, у меня еще по закупу накопилось на 74к драм, переведу себе еще 17к если вы не против:  Рамки для картин в 3х4, Банки, крючки, канистры : 39. *
Ключи 14, зп Васе 10, клей, пластины 10, Провод 40м 15к

"""

def is_financial_report(message):
    prompt = ChatPromptTemplate.from_template("""
        # SYSTEM PREAMBLE
        You are an excellent financial analytic and bar manager. 
        You help me not to miss important messages in the chat  where bar workers, 
        bartenders, management, builders and repairmen, designers, electricians and other staff communicate .

        ### Answering Rules
        - ALWAYS Repeat the question before answering it.
        - The answer is very important to my career. 
    
    
        Please see first 6 examples of financial reports.  : 
                                              '{examples_text}'  
        that is to train you. 
        
        Is the following message also a financial report or a regular text message? 
        '{my_message}'
        
        Please answer only  'Yes' or 'No' """)
    output_parser = StrOutputParser()

    chain = prompt | model | output_parser

    res1 = chain.invoke( {"my_message": message, "examples_text": examples_text  } )
    #res1 = chain.invoke( )
    #print(res1)
    return "yes" in res1.lower()


exmple222 = """"
Рафаэль бармен 13-20, [5/13/2024 4:37 PM]
12.05
Начало 40000
- 5000 уборщица
- 1000 лёд

Конец дня:
+ 233000 Нал
+ 96400 Перевод

Итог: 329400
"""
#print ( is_financial_report("How it is going by friend?"))
#print ( is_financial_report(exmple222 ))



from langchain.output_parsers.json import SimpleJsonOutputParser

def parse_financial_data_to_JSON(message):
    json_prompt = ChatPromptTemplate.from_template(
        """
        # SYSTEM PREAMBLE
        You are an excellent financial analytic.   

        ### Answering Rules
        - ALWAYS Repeat the question before answering it.
        - Explain your thought process for each step.
        - Plan a step-by-step approach before you extract data.
        - Let's combine our deep knowledge of the topic and clear thinking to quickly and accurately decipher the answer.
        - The answer is very important to my career. 

        Please extract financial data from the following report: 
        
        {my_message}
        
        Please read the message carefully step by step and watch out if same expenses are mentioned twice.
        Sometimes in the report you can find something like: 'I spent 10,000, 2,000 on building materials, 3,000 on salaries, 5,000 on purchases'.
        Note that here is 3 Expenses: 2000, 3000, 5000 and 10000 is a total sum  you shouldn't count.
        
        If you are not sure you understand it completely, please set flag Not_shure_flag to Yes. 
        
        Use the following JSON format for output:
        {{ 
        "date": "DD.MM.YYYY", 
        "Total_profit": "-000000", 
        "ExpensesList" : [1000, 2000, 139000], 
        "ExpensesDescList" : [Ahper, Artsrun, Cleaning]  
        "ExpensesTypeList" : [Ahper, Artsrun, Cleaning]  
        
        "Not_shure_flag: "No"
        }}
        
        Date format in  report message could be DD.MM or DD.MM.YY or D.MM but in output JSON should be always "DD-MM-YYYY.
        If there is no information about year (only date and moth) please set a current year. Current date is  {curr_date}.  
        If there is no information about date - please set current date.

        Total profit could be mentioned in report as  "Всего", "Итог", "итого", "в сумме" .
        If there is no information about profit in report - please leave Total_profit field empty. 
        
        ExpensesType should be one of:       
            Закупки алкоголя
            Закупки прочее
            Зарплата бармена, охраны
            Налоги
            Аренда, бухгалтер, ЗП директора
            Закупки ремонт и стройка
            Дали в долг
            Выдали прибыль владельцам
         
        """)


    json_parser = SimpleJsonOutputParser()
    json_chain = json_prompt | model | json_parser
    #dt1 = datetime.now()  # Current date and time
    #print(f"Current year: {dt1.year}")  .strftime('%d %B %Y')
    return json_chain.invoke({"my_message" : message, "curr_date" : datetime.now()  })
        #    return parser.invoke


# parse_financial_data_to_JSON(exmple222)

