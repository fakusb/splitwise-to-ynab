#!/usr/bin/env python3

import csv
from datetime import datetime, timedelta
from decimal import Decimal
import json
from pprint import pprint
import requests
import sys

YNAB_BASE_URL = "https://api.youneedabudget.com/v1"

if len(sys.argv) < 2:
  print("ERROR: Not all required arguments were provided")
  sys.exit(1)

csv_file = sys.argv[1]
date_start = datetime.strptime(sys.argv[2],"%Y-%m-%d").date()
date_end = datetime.today().date()

if len(sys.argv) > 3:
  date_end = datetime.strptime(sys.argv[3], "%Y-%m-%d").date()

with open('config.json') as config:
  config = json.load(config)

access_token = config['access_token']
BUDGET_ID = config['budget_id']

print(f"Importing Splitwise transactions starting from {date_start} to {date_end} inclusive from {csv_file}")

data = { 
  "transactions": []
}

with open(csv_file, newline='', encoding='utf-8') as csvfile:
  reader = csv.reader(csvfile)
  for _ in range(4): next(reader)

  for row in reader:
    if len(row) == 0:
      break

    txn_date = datetime.strptime(row[0], "%Y-%m-%d").date()

    later_than_start = txn_date >= date_start
    earlier_than_end = txn_date <= date_end

    if later_than_start and earlier_than_end:
      description = row[1]
      category_splitwise = row[2]
      lendToOther = int(Decimal(row[5]) * 1000)
      costTotal = int(Decimal(row[3]) * 1000)

      if category_splitwise == 'Payment':
        data["transactions"].append({
        "account_id": config['idGiro'],
        "date": str(txn_date),
        "amount": -lendToOther,
        "payee_name": config['nameOtherPayee'],
        "category_id": config['idCatSplitwise'],
        "memo": description + "(logged in Splitwise)",
        "cleared": "uncleared",
        "approved": False
        })
        continue
    


      if lendToOther > 0:
        budgetSpend = costTotal - lendToOther
        moneyMoved = costTotal
      else :
        budgetSpend = - lendToOther
        moneyMoved = 0

      category_ynab = config['categoryMap'].get(category_splitwise)

      subtransactions = []
      subtransactions.append({
        "amount": -lendToOther,
        "payee_name": config['nameOtherPayee'],
        "category_id": config['idCatSplitwise'],
        "memo": description + " (" + category_splitwise+", Splitwise verliehen)" ,
      })
      if budgetSpend > 0:
        subtransactions.append({
          "amount": -budgetSpend,
          "memo": description,
          "category_id": category_ynab,
          "memo": description + " (" + category_splitwise+")"
        })
      data["transactions"].append({
        "account_id": config['idGiro'],
        "date": str(txn_date),
        "amount": -moneyMoved,
        "memo": description + " (" + category_splitwise+", Splitwise, Gesamtbetrag)" ,
        "cleared": "uncleared",
        "approved": False,
        "subtransactions": subtransactions
      })

headers = {
  'Accept': 'application/json',
  'Content-Type': 'application/json',
  'Authorization': f'Bearer {access_token}'
}
response = requests.post(f'{YNAB_BASE_URL}/budgets/{BUDGET_ID}/transactions', headers=headers, json=data)
pprint(response.json())
