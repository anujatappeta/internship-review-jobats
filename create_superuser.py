import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

try:
    import django
    django.setup()
    from django.contrib.auth import get_user_model
except Exception as e:
    print(f"[-] Django setup failed: {e}")
    sys.exit(1)

def create_admin():
    User = get_user_model()
    username = os.environ.get('ADMIN_USERNAME')
    email = os.environ.get('ADMIN_EMAIL')
    password = os.environ.get('ADMIN_PASSWORD')

    if not username or not email or not password:
        print("[-] Set ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD to create a superuser.")
        return

    print("[*] Checking / Creating Automatic Admin Superuser...")
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"[+] Superuser '{username}' created successfully.")
    else:
        print(f"[*] Superuser '{username}' already exists.")

if __name__ == '__main__':
    create_admin()
