import requests
from collections import defaultdict

API_KEY = '70f08c4ca8d39e217f90e5aa' 

class CurrencyConverter:
    def __init__(self, base_currency):
        self.base_currency = base_currency
        self.rates = self.fetch_rates()

    def fetch_rates(self):
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{self.base_currency}"
        response = requests.get(url)
        data = response.json()
        if response.status_code != 200 or data['result'] != 'success':
            raise Exception("Currency API error.")
        return data['conversion_rates']

    def convert(self, amount, from_currency, to_currency):
        if from_currency == to_currency:
            return round(amount, 2)

        # Convert from source to base (if needed), then to target
        if from_currency != self.base_currency:
            amount = amount / self.rates[from_currency]
        return round(amount * self.rates[to_currency], 2)


class BillSplitter:
    def __init__(self, people, currency_converter):
        self.people = people
        self.expenses = []
        self.converter = currency_converter
        self.balances = defaultdict(float)

    def add_expense(self, payer, amount, currency, description=""):
        converted_amount = self.converter.convert(amount, currency, self.converter.base_currency)
        split_amount = converted_amount / len(self.people)
        self.expenses.append((payer, amount, currency, converted_amount, description))

        for person in self.people:
            if person == payer:
                self.balances[person] += converted_amount - split_amount
            else:
                self.balances[person] -= split_amount

    def settle_debts(self):
        debtors = {k: v for k, v in self.balances.items() if v < 0}
        creditors = {k: v for k, v in self.balances.items() if v > 0}

        settlements = []
        debtors = sorted(debtors.items(), key=lambda x: x[1])
        creditors = sorted(creditors.items(), key=lambda x: -x[1])

        i, j = 0, 0
        while i < len(debtors) and j < len(creditors):
            debtor, debt_amt = debtors[i]
            creditor, credit_amt = creditors[j]

            payment = min(-debt_amt, credit_amt)
            settlements.append(f"{debtor} pays {creditor} {payment:.2f} {self.converter.base_currency}")

            debt_amt += payment
            credit_amt -= payment

            debtors[i] = (debtor, debt_amt)
            creditors[j] = (creditor, credit_amt)

            if abs(debt_amt) < 0.01:
                i += 1
            if credit_amt < 0.01:
                j += 1

        return settlements

    def show_summary(self):
        print("\n--- Expense Summary ---")
        for payer, amount, currency, converted, desc in self.expenses:
            print(f"{payer} paid {amount} {currency} ({converted:.2f} {self.converter.base_currency}) for {desc or 'unspecified'}")
        print("\n--- Net Balances ---")
        for person, balance in self.balances.items():
            print(f"{person}: {balance:.2f} {self.converter.base_currency}")
        print("\n--- Settlements ---")
        for line in self.settle_debts():
            print(line)


#MAIN APP 
if __name__ == "__main__":
    print("BillSplitter with Any-to-Any Currency Conversion")
    base_currency = input("Convert all amounts to which currency? (e.g. USD, NGN, EUR): ").strip().upper()
    people = input("Enter names (comma separated): ").split(",")
    people = [p.strip() for p in people]

    cc = CurrencyConverter(base_currency)
    splitter = BillSplitter(people, cc)

    while True:
        payer = input("\nWho paid? (or 'done'): ").strip()
        if payer.lower() == "done":
            break
        if payer not in people:
            print("Invalid name. Try again.")
            continue
        try:
            amount = float(input("Amount: "))
            currency = input("Currency (e.g. USD, EUR): ").strip().upper()
            desc = input("Description: ")
            splitter.add_expense(payer, amount, currency, desc)
        except Exception as e:
            print("Error:", e)

    splitter.show_summary()

