# Check list for new titles (after updating admin.* metafiles)

1. Download new OCR files (it will go through all the titles anyway and point out missing files in older titles. There will be few, so ignore the errors)
```
python3 tools/bm_ocr_downloader.py
```

2. Process the OCR files for frequency analysis and other statistics
```
python3 tools/bm_freq_processor.py
```

3. Create the language analysis summary file
```
python3 tools/bm_lang_summary.py
```

4. (optional) Update the custom/individualized language analysis (This can be done in the Language settings screen as well)
```
python3 tools/bm_custom_lang_analysis.py analyze
```

5. Link the new titles in Bilingual manga DB with corresponding entity IDs in Mangaupdates.com
```
python3 tools/mangaupdates.py match_all
```
Check that the titles/release years/synopses match. If not, see the python script for more detailed procedure

6. (optional) Update the ratings and votes from Mangaupdates.com (for new titles this was already done automatically in the previous step). Usually things change very little so once per month is enough.
```
python3 tools/mangaupdates.py refresh
```
