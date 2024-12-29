# Bilingual_Manga-home--src-
Source code of bilingual manga(home)

1. Get the database json files from https://github.com/B-M-dev/Bilingual_Manga_databases and place them in json folder

2. Fetch the sub modules

    git submodule init
    git submodule update

2. Create Python environment and install requirements

    python -m venv venv
    pip install -r requirements.txt

3. Install Fugashi, Unidict ja JMDict

    pip install fugashi[unidic]
    python -m unidic download
    tools/install_jmdict.sh

4. Install MongoDB (see instructions for your platform)
    https://www.mongodb.com/docs/manual/administration/install-community/

5. Import Manga/book metadata from json files into MongoDB
    python tools/import_json_to_mongo.py 



4. Run these commands in the main directory
- `npm install`
- `node --env-file=.env app.js`
- `npm run dev`
