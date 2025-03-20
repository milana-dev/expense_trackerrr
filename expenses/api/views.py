from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from users.models import UserProfil
from .tasks import update_financial_record

from expenses.api.filters import RecordFilter

from expenses.models import (
    FinancialRecord,
    IncomeCategory,
    ExpenseCategory
    )

from .serializers import (
    ListIncomeCategorySerializer,
    ListExpenseCategorySerializer,
    CreateFinancialRecordSerializer, 
    UpdateFinancialRecordSerializer, 
    
)


class CreateRecordApiView(generics.CreateAPIView):
    queryset = FinancialRecord.objects.all()
    serializer_class = CreateFinancialRecordSerializer
    permission_classes = [IsAuthenticated]
    
    
    def create(self, request, *args, **kwargs):
        selected_user_id = request.data.get("user")  
        if selected_user_id:
            profile = UserProfil.objects.get(id=selected_user_id)
        else:
            profile = request.user 

        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            income_amount = serializer.validated_data.get("income_amount", 0)
            expense_amount = serializer.validated_data.get("expense_amount", 0)

            try:
                financial_record = FinancialRecord.objects.get(user=profile)
                balance = financial_record.income_amount - financial_record.expense_amount

                if balance == 0 and expense_amount > 0:
                    return Response({"message": "Xərc əməliyyatı həyata keçirilə bilməz, çünki balansınız sıfırdır!"}, status=status.HTTP_400_BAD_REQUEST)
                
                if balance < expense_amount:
                    return Response({"message": "Xərc əməliyyatı həyata keçirilə bilməz, balansınız xərcdən azdır!"}, status=status.HTTP_400_BAD_REQUEST)

                financial_record.income_amount += income_amount
                financial_record.expense_amount += expense_amount
                financial_record.save()

                return Response({"message": "Maliyyə rekordu uğurla yeniləndi!"}, status=status.HTTP_200_OK)

            except FinancialRecord.DoesNotExist:
                if expense_amount > 0:
                    return Response({"message": "Balansınız sıfır olduğu üçün xərc əməliyyatı edilə bilməz!"}, status=status.HTTP_400_BAD_REQUEST)

                serializer.save(user=profile) 
                return Response({"message": "Maliyyə rekordu uğurla yaradıldı!"}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    
class ListFinancialRecordAPIView(generics.ListAPIView):
    queryset = FinancialRecord.objects.select_related('user_profile', 'income_category', 'expense_category')
    serializer_class = CreateFinancialRecordSerializer
    filterset_class = RecordFilter
    
    



class UpdateFinancialRecordView(generics.UpdateAPIView):
    queryset = FinancialRecord.objects.all()
    serializer_class = UpdateFinancialRecordSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def put(self, request, *args, **kwargs):
        user = request.user
        new_income = request.data.get('income_amount')
        new_expense = request.data.get('expense_amount')

        task = update_financial_record.delay(user.id, new_income, new_expense)
        return Response({
            "message": "Maliyyə rekordu yenilənir, nəticəni gözləyin...",
            "task_id": task.id
        }, status=status.HTTP_202_ACCEPTED)












