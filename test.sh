./all_tests_old 
./all_tests_new
python src/diff/main.py
python src/parser/main.py
uvicorn server:app --reload
