# Deploy dev con Docker

Nella root del progetto:

```
docker-compose -f docker/docker-compose-dev.yml -p generatore_int up
```

- aggiungi il parametro `-d` oppure `--detach` se vuoi liberare la shell

Alla fine del processo nel browser, `localhost` il progetto è in esecuzione


## Creazione superuser

```
docker-compose -f docker/docker-compose-dev.yml -p generatore_int exec generatore_interattivo_django bash
```

In questo modo ti agganci alla shell del container Docker, poi:

```
cd /app
python manage.py createsuperuser
```

**N.B.** ambiente dev: ricorda di impostare `Client id: 10` e `Signboard id: 11` nel database admin:
```
Pagina iniziale › Builder › Impostazioni clienti › ClientSetting object ($id) 
```

Per caricare la fixture:

```
cd /app
python manage.py loaddata sample_data/dump.xml
```

Per le migrazioni:

```
cd /app
python manage.py makemigrations
python manage.py migrate
```
**N.B.** È possibile fare le migrazioni aprendo un altro terminale (tab o finestra)
e agganciarsi alla shell del container. È sconsigliato agganciarsi al container nello stesso
terminale senza il parametro `--detach`, cioè mettendo in background il progetto
in esecuzione non "sganciato" (`^CTRL+Z bg`, oppure `&` appesa in fondo).


## Versioni:

Sviluppo in locale:

```
docker-compose -f docker/docker-compose-dev.yml up -d
```

Versione di sviluppo e test `dev02`:

```
docker-compose -f docker/docker-compose-dev02.yml up -d
```

Ambiente di produzione (con `debug = False`)

```
docker-compose -f docker/docker-compose-prod.yml up -d
```

Ambiente di produzione (con `debug = True`)

```
docker-compose -f docker/docker-compose-prod-debug.yml up -d
```

Worker versione di sviluppo e test `worker-test`:

```
docker-compose -f docker/docker-compose-worker-debug.yml up -d
```

Worker produzione `pdf2jpg`:

```
docker-compose -f docker/docker-compose-worker.yml up -d
```


## Troubleshooting

- Spegnere il container e rimuovere i volumi:
```
docker-compose -f docker/docker-compose-dev.yml -p generatore_int down --volumes
```
- Rimuovere il database pertinente (per dev: tutta la cartella `docker/dev/mysql-data`);
- Accendere il container con `up` al posto di `down --volumes`.

## Generare i file per le traduzioni

```
docker-compose -f docker/docker-compose-dev.yml -p generatore_int exec generatore_interattivo_django bash
```

Per generare i files di traduzioni:

```
cd /app
python manage.py makemessages -l it -i myvenv
python manage.py makemessages -l en -i myvenv
python manage.py makemessages -l es -i myvenv
```

Una volta tradotti, per applicare le traduzioni:

```
python manage.py compilemessages -l it
python manage.py compilemessages -l en
python manage.py compilemessages -l es
```


## Utilizzo di pylint e black per controlli su indentazione e pulizia del codice

Quando fai il checkout del progetto installa la libreria `pre-commit`:

```
pip install pre-commit
```

poi lancia i comandi:

```
pre-commit install
pre-commit autoupdate
```

In questo modo git ad ogni commit analizzerà i files committati

Se vuoi formattare manualmente i files del progetto dei installare black e pylint:

```
pip install black
pip install pylint
```

e poi lanciare manualmente questi comandi:

```
black .
python lint.py -p ../generatore-interattivo/
```