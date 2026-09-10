#!/bin/bash
set -e

rsync -av --omit-dir-times \
  --exclude='.git' \
  --exclude='staticfiles/' \
  --exclude='media/' \
  --exclude='venv/' \
  /var/lib/jenkins/workspace/Ranqing\ AI/ \
  /home/Raphael/RanqingAI-Backend/

cd /home/Raphael/RanqingAI-Backend
. venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart celerybeat

# =======================================================================
#!/bin/bash
set -e

rsync -av --omit-dir-times --no-group --no-perms \
  --exclude='.git' \
  --exclude='staticfiles/' \
  --exclude='media/' \
  --exclude='venv/' \
  --exclude='celerybeat-schedule*' \
  /var/lib/jenkins/workspace/Ranqing\ AI/ \
  /home/Raphael/RanqingAI-Backend/

cd /home/ubuntu/RanqingAI-Backend

. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput

sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart celerybeat