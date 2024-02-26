#!/bin/sh
wget http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz
gunzip JMdict_e.gz
mkdir -p ../lang
mv JMdict_e ../lang/
