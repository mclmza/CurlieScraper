# Curlie scraper

Script developed for the Disruptive Data Summer School

## How to use

Works with Python 3

### Standard mode

```sh
python3 main.py
```

#### Save to csv

```sh
python3 main.py > output.csv
```

### Boosted mode

```sh
python3 -u main.py --boosted
```

This configuration needs TOR service to work. You'll also need to edit your `torrc` file as follows:

```sh
ControlPort 9051
## If you enable the controlport, be sure to enable one of these
## authentication methods, to prevent attackers from accessing it.
HashedControlPassword 16:05834BCEDD478D1060F1D7E2CE98E9C13075E8D3061D702F63BCD674DE
``` 

Note that the HashedControlPassword above is for the password `password`

