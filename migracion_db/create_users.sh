#!/usr/bin/env bash
set -euo pipefail

APP_CONTAINER=${APP_CONTAINER:-hhcc_app}

CMD="from django.contrib.auth import get_user_model; User=get_user_model(); u,_=User.objects.get_or_create(username='eze'); u.is_superuser=True; u.is_staff=True; u.is_active=True; u.set_password('Furosemida'); u.save(); u,_=User.objects.get_or_create(username='omar'); u.is_superuser=False; u.is_staff=False; u.is_active=True; u.set_password('Corbis5'); u.save(); print(list(User.objects.values_list('username','is_superuser','is_staff','is_active')))"

docker exec -i "$APP_CONTAINER" python3 manage.py shell -c "$CMD"
