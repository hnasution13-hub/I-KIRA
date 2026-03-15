from apps.investor.models import InvestorAccount

InvestorAccount.objects.filter(username='administrator').delete()

acc = InvestorAccount()
acc.nama = 'Founder'
acc.username = 'administrator'
acc.aktif = True
acc.set_password('admin123')
acc.save()

print("=================================")
print("Berhasil buat akun investor!")
print("Username : administrator")
print("Password : admin123")
print("=================================")