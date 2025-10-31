
# Change ENV

# Docker

```
docker compose up -d
```

```
docker compose run --rm certbot certonly --webroot \
  -w /var/www/certbot \
  -d "$DOMAIN_NAME" \
  --email "$CERTBOT_EMAIL" --agree-tos --no-eff-email
```

