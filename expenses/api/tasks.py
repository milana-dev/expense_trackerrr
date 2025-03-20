from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from ..models import FinancialRecord
from users.models import UserProfil

@shared_task
def update_financial_record(user_id, new_income=None, new_expense=None):
    try:
        user = UserProfil.objects.get(id=user_id)
        financial_record, created = FinancialRecord.objects.get_or_create(user=user)
        current_balance = financial_record.income_amount - financial_record.expense_amount
        
        if new_expense is not None and new_expense > current_balance:
            return {"message": "Xərc mövcud balansdan çox ola bilməz!"}
        if new_income is not None:
            financial_record.income_amount += new_income
        if new_expense is not None:
            financial_record.expense_amount += new_expense
            
        financial_record.save()
        new_balance = financial_record.income_amount - financial_record.expense_amount
        return {
            "username": user.username,
            "income_amount": financial_record.income_amount,
            "expense_amount": financial_record.expense_amount,
            "balance": new_balance,
            "message": "Maliyyə rekordu uğurla yeniləndi!"
        }

    except ObjectDoesNotExist:
        return {"message": "İstifadəçi tapılmadı!"}





















































