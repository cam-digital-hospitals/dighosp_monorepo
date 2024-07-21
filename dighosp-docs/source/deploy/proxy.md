# Public reverse proxy

To host the site publicly, we can use a reverse proxy service such as [ngrok](https://ngrok.com/). First, obtain a domain from ngrok, for example `foo-bar-baz.ngrok-free.app`. For convenience, you can save this to `.bashrc`:

```bash
# $HOME/.bashrc

NGROK_URL=better-eagle-bursting.ngrok-free.app
```

Finally, to deploy the site:
```bash
ngrok http --domain=$NGROK_URL 80
```
