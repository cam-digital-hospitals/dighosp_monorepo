# Web proxy

The webproxy service is a simple Nginx service. We use `default.conf` to set up the reverse proxy service. Each service corresponds to a single `location` entry within the main `server` entry.

## Single-page redirect

We redirect the root of the website to a specific page, returning a `302 Found` status code:

```nginx
  location = / {  # Redirect the root and only the root
    return 302 /frontend/;
  }
```

## Dash frontend

Dash apps define their own URL prefix behavior for presenting hyperlinks and making API calls, so we do not strip the prefix in Nginx. We also extend the timeout duration to support long-running Dash callbacks, e.g., those that require heavy computation.

```nginx
  location /frontend/ {
    proxy_pass http://frontend:8000;  # no trailing / = do not strip prefix
    proxy_read_timeout 180s;  # support longer Dash callbacks
    proxy_send_timeout 180s;  # support longer Dash callbacks
  }
```

## FastAPI

We use FastAPI to provide backend services. The root path is provided when launching FastAPI:

```Dockerfile
# Dockerfile

CMD fastapi run dighosp_des/api.py --host 0.0.0.0 --root-path ${FASTAPI_ROOT:-''}
```

Then, in Nginx, a simple `proxy_pass` will suffice:
```nginx
  location /api/des/ {
    proxy_pass http://des-api:8000/;
  }
```
