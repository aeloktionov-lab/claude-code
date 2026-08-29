# Деплой на Рег.ру

Готовые конфиги лежат в `deploy/`. Сайт — обычное Node.js-приложение (Express), поэтому
нужен **облачный/VPS-сервер Рег.ру** (тариф «Облачный сервер» / Cloud), а не обычный
shared-хостинг — там нет поддержки Node.js-процессов.

Рекомендуемый тариф для старта: 1 vCPU / 1–2 ГБ RAM / 20 ГБ SSD, Ubuntu 22.04 —
самый младший облачный сервер Рег.ру этому требованию соответствует с запасом.

## 1. Заказать сервер

1. В панели Рег.ру → «Облачные серверы» → создать сервер: Ubuntu 22.04 LTS, минимальный тариф
2. Дождаться письма с IP-адресом сервера, логином `root` и паролем

## 2. Подключиться и подготовить сервер

```bash
ssh root@<IP_СЕРВЕРА>

apt update && apt upgrade -y
apt install -y nginx git ufw

# Node.js 20 LTS через NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# отдельный непривилегированный пользователь для приложения
adduser --disabled-password --gecos "" croid
```

## 3. Забрать код и установить зависимости

```bash
su - croid
mkdir -p /var/www/croid
git clone https://github.com/aeloktionov-lab/claude-code.git /var/www/croid
cd /var/www/croid/server
npm install --omit=dev
cp /var/www/croid/deploy/env.example /var/www/croid/server/.env
nano /var/www/croid/server/.env   # задать надёжный ADMIN_PASSWORD
exit   # обратно в root
```

> При обновлениях сайта: `cd /var/www/croid && git pull && cd server && npm install --omit=dev && systemctl restart croid`

## 4. Запустить как systemd-сервис

```bash
cp /var/www/croid/deploy/croid.service /etc/systemd/system/croid.service
systemctl daemon-reload
systemctl enable --now croid
systemctl status croid   # должен быть active (running)
```

## 5. Настроить Nginx (обратный прокси)

```bash
cp /var/www/croid/deploy/nginx.conf /etc/nginx/sites-available/croid.ru
ln -s /etc/nginx/sites-available/croid.ru /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
```

## 6. Привязать домен croid.ru к серверу

В панели Рег.ру → «Домены» → `croid.ru` → DNS-серверы/управление записями:
- A-запись `@` → IP сервера
- A-запись `www` → IP сервера
(если домен куплен в Рег.ру, это делается прямо там; DNS обновляется обычно от
нескольких минут до пары часов)

## 7. Включить HTTPS (Let's Encrypt, бесплатно)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d croid.ru -d www.croid.ru
```

Certbot сам допишет SSL-блок в конфиг Nginx и настроит автопродление сертификата.

## 8. Открыть файрвол

```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
```

## Проверка

- `https://croid.ru` — открывается сайт
- `https://croid.ru/admin.html` — запрашивает логин/пароль (пароль — из `server/.env`)
- `systemctl status croid` — сервис активен, автоперезапускается при падении (`Restart=on-failure`)

## Бэкап данных

Все заявки и обращения — в файле `/var/www/croid/server/data.sqlite`. Добавьте его
в регулярный бэкап (например, cron + копирование в облачное хранилище), это не
делает Nginx/systemd автоматически.
