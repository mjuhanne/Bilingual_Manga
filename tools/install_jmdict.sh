#!/bin/sh
wget http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz
wget http://ftp.edrdg.org/pub/Nihongo/JMnedict.xml.gz
gunzip JMdict_e.gz
gunzip JMnedict.xml.gz
mkdir -p lang
mv JMdict_e lang/
mv JMnedict.xml lang/
python tools/process_jmdict.py
python tools/process_jmnedict.py
python tools/process_jmnedict_mongo.py
