# Installation

```bash 
git clone https://github.com/jwapico/soulRipper.git
cd soulRipper
```

Download the latest release of [slskd](https://github.com/slskd/slskd/releases) into the root of the project directory

Modify `assets/slskd.template.yml` with the appropriate information
- You will need to generate an API key with:

```bash
slskd --generate-secret 69
```

You need to download the [SoulseekQt](https://www.slsknet.org/news/node/1) GUI in order to create a username and password I think
- You don't need to change the username and password for web just soulseek

Move your modified `slskd.template.yml` in wherever it looks for the config file when you run slskd (it will tell you)

You can check slskd + Soulseek are working by visiting the web frontend at [http://localhost:5030](http://localhost:5030) and logging in with username and password "slskd"

Now that slskd and Soulseek are configured you need to configure the actual SoulRipper - modify `config.yaml`

Also create a `.env` file with the following:

```
SPOTIFY_CLIENT_ID=<your_spotify_client_id>
SPOTIFY_CLIENT_SECRET=<your_spotify_client_secret>
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/spotify/callback/
SLSKD_API_KEY=<your_slskd_api_key>
```

> Generate Spotify API keys in the [Developer Dashboard](https://developer.spotify.com/dashboard), make sure your callback is identical.

Create a python venv and install the requirements

```bash
python -m venv venv
source venv/bin/activate
# or for windows: ./venv/Scripts/Activate.ps1
pip install .
```

`yt-dlp` may require you to install the [Deno runtime](https://deno.com/) and set your cookies. To set your cookies download the cookies.txt addon ([firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/), [chrome](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)), go to www.youtube.com/, sign in, download `cookies.txt` and place in `assets/`.
- As YouTube gets more strict you may need to jump through more hoops to get `yt-dlp` to work so these instructions are subject to change (I will not rewrite this document if things become obsolete; just do what `yt-dlp` says)

Now you should *finally* be able to run the app

```bash
# show all functionality
soulripper -h
```

```bash
# search for specific track
soulripper --search-query "Kiss of Life - Sade"
```

```bash
# download spotify playlist
soulripper --playlist-url
```

```bash
# download all spotify liked songs
soulripper --download-liked
```
