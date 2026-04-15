#!/usr/bin/env bash
set -euo pipefail

APP_CONTAINER=${APP_CONTAINER:-hhcc_app}

CMD="from django.contrib.auth import get_user_model; User=get_user_model(); u=User.objects.get(username='eze'); u.set_password('Furosemida'); u.is_superuser=True; u.is_staff=True; u.is_active=True; u.save(); u=User.objects.get(username='omar'); u.set_password('Corbis5'); u.is_superuser=False; u.is_staff=False; u.is_active=True; u.save(); print('ok')"

docker exec -i "$APP_CONTAINER" python3 manage.py shell -c "$CMD"
